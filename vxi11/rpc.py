"""
Sun RPC version 2 -- RFC1057

This file is drawn from Python's RPC demo, updated for python 3.  There
doesn't seem to be an original author or license associated the original
file.

XXX There should be separate exceptions for the various reasons why
XXX an RPC can fail, rather than using RuntimeError for everything

XXX Need to use class based exceptions rather than string exceptions

XXX The UDP version of the protocol resends requests when it does
XXX not receive a timely reply -- use only for idempotent calls!

XXX There is no provision for call timeout on TCP connections

Original source: http://svn.python.org/projects/python/trunk/Demo/rpc/rpc.py

"""

import xdrlib
import socket
import os
import struct

RPCVERSION = 2

CALL = 0
REPLY = 1

AUTH_NULL = 0
AUTH_UNIX = 1
AUTH_SHORT = 2
AUTH_DES = 3

MSG_ACCEPTED = 0
MSG_DENIED = 1

SUCCESS = 0            # RPC executed successfully
PROG_UNAVAIL  = 1      # remote hasn't exported program
PROG_MISMATCH = 2      # remote can't support version #
PROC_UNAVAIL  = 3      # program can't support procedure
GARBAGE_ARGS  = 4      # procedure can't decode params

RPC_MISMATCH = 0       # RPC version number != 2
AUTH_ERROR = 1         # remote can't authenticate caller

AUTH_BADCRED      = 1  # bad credentials (seal broken)
AUTH_REJECTEDCRED = 2  # client must begin new session
AUTH_BADVERF      = 3  # bad verifier (seal broken)
AUTH_REJECTEDVERF = 4  # verifier expired or replayed
AUTH_TOOWEAK      = 5  # rejected for security reasons

# Exceptions
class RPCError(Exception): pass
class RPCBadFormat(RPCError): pass
class RPCBadVersion(RPCError): pass
class RPCGarbageArgs(RPCError): pass
class RPCUnpackError(RPCError): pass

def make_auth_null():
    return b''

class Packer(xdrlib.Packer):

    def pack_auth(self, auth):
        flavor, stuff = auth
        self.pack_enum(flavor)
        self.pack_opaque(stuff)

    def pack_auth_unix(self, stamp, machinename, uid, gid, gids):
        self.pack_uint(stamp)
        self.pack_string(machinename)
        self.pack_uint(uid)
        self.pack_uint(gid)
        self.pack_uint(len(gids))
        for i in gids:
            self.pack_uint(i)

    def pack_callheader(self, xid, prog, vers, proc, cred, verf):
        self.pack_uint(xid)
        self.pack_enum(CALL)
        self.pack_uint(RPCVERSION)
        self.pack_uint(prog)
        self.pack_uint(vers)
        self.pack_uint(proc)
        self.pack_auth(cred)
        self.pack_auth(verf)
        # Caller must add procedure-specific part of call

    def pack_replyheader(self, xid, verf):
        self.pack_uint(xid)
        self.pack_enum(REPLY)
        self.pack_uint(MSG_ACCEPTED)
        self.pack_auth(verf)
        self.pack_enum(SUCCESS)
        # Caller must add procedure-specific part of reply

class Unpacker(xdrlib.Unpacker):

    def unpack_auth(self):
        flavor = self.unpack_enum()
        stuff = self.unpack_opaque()
        return (flavor, stuff)

    def unpack_callheader(self):
        xid = self.unpack_uint()
        temp = self.unpack_enum()
        if temp != CALL:
            raise RPCBadFormat('no CALL but %r' % (temp,))
        temp = self.unpack_uint()
        if temp != RPCVERSION:
            raise RPCBadVersion('bad RPC version %r' % (temp,))
        prog = self.unpack_uint()
        vers = self.unpack_uint()
        proc = self.unpack_uint()
        cred = self.unpack_auth()
        verf = self.unpack_auth()
        return xid, prog, vers, proc, cred, verf
        # Caller must add procedure-specific part of call

    def unpack_replyheader(self):
        xid = self.unpack_uint()
        mtype = self.unpack_enum()
        if mtype != REPLY:
            raise RPCUnpackError('no REPLY but %r' % (mtype,))
        stat = self.unpack_enum()
        if stat == MSG_DENIED:
            stat = self.unpack_enum()
            if stat == RPC_MISMATCH:
                low = self.unpack_uint()
                high = self.unpack_uint()
                raise RPCUnpackError('MSG_DENIED: RPC_MISMATCH: %r' % ((low, high),))
            if stat == AUTH_ERROR:
                stat = self.unpack_uint()
                raise RPCUnpackError('MSG_DENIED: AUTH_ERROR: %r' % (stat,))
            raise RPCUnpackError('MSG_DENIED: %r' % (stat,))
        if stat != MSG_ACCEPTED:
            raise RPCUnpackError('Neither MSG_DENIED nor MSG_ACCEPTED: %r' % (stat,))
        verf = self.unpack_auth()
        stat = self.unpack_enum()
        if stat == PROG_UNAVAIL:
            raise RPCUnpackError('call failed: PROG_UNAVAIL')
        if stat == PROG_MISMATCH:
            low = self.unpack_uint()
            high = self.unpack_uint()
            raise RPCUnpackError('call failed: PROG_MISMATCH: %r' % ((low, high),))
        if stat == PROC_UNAVAIL:
            raise RPCUnpackError('call failed: PROC_UNAVAIL')
        if stat == GARBAGE_ARGS:
            raise RPCGarbageArgs
        if stat != SUCCESS:
            raise RPCUnpackError('call failed: %r' % (stat,))
        return xid, verf
        # Caller must get procedure-specific part of reply

# Common base class for clients

class Client:

    def __init__(self, host, prog, vers, port):
        self.host = host
        self.prog = prog
        self.vers = vers
        self.port = port
        self.lastxid = 0 # XXX should be more random?
        self.cred = None
        self.verf = None

    def make_call(self, proc, args, pack_func, unpack_func):
        # Don't normally override this (but see Broadcast)
        if pack_func is None and args is not None:
            raise TypeError('non-null args with null pack_func')
        self.start_call(proc)
        if pack_func:
            pack_func(args)
        self.do_call()
        if unpack_func:
            result = unpack_func()
        else:
            result = None
        self.unpacker.done()
        return result

    def start_call(self, proc):
        # Don't override this
        self.lastxid = xid = self.lastxid + 1
        cred = self.mkcred()
        verf = self.mkverf()
        p = self.packer
        p.reset()
        p.pack_callheader(xid, self.prog, self.vers, proc, cred, verf)

    def do_call(self):
        # This MUST be overridden
        raise RPCError('do_call not defined')

    def mkcred(self):
        # Override this to use more powerful credentials
        if self.cred is None:
            self.cred = (AUTH_NULL, make_auth_null())
        return self.cred

    def mkverf(self):
        # Override this to use a more powerful verifier
        if self.verf is None:
            self.verf = (AUTH_NULL, make_auth_null())
        return self.verf

    def call_0(self):
        # Procedure 0 is always like this
        return self.make_call(0, None, None, None)


# Record-Marking standard support

def sendfrag(sock, last, frag):
    x = len(frag)
    if last: x = x | 0x80000000
    header = struct.pack(">I", x)
    sock.sendall(header + frag)

def sendrecord(sock, record):
    if len(record) > 0:
        sendfrag(sock, 1, record)

def recvfrag(sock):
    header = sock.recv(4)
    if len(header) < 4:
        raise EOFError
    x = struct.unpack(">I", header[0:4])[0]
    last = ((x & 0x80000000) != 0)
    n = int(x & 0x7fffffff)
    frag = b''
    while n > 0:
        buf = sock.recv(n)
        if not buf: raise EOFError
        n = n - len(buf)
        frag = frag + buf
    return last, frag

def recvrecord(sock):
    record = b''
    last = 0
    while not last:
        last, frag = recvfrag(sock)
        record = record + frag
    return record


# Client using TCP to a specific port

class RawTCPClient(Client):
    def __init__(self, host, prog, vers, port):
        Client.__init__(self, host, prog, vers, port)
        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def close(self):
        self.sock.close()

    def do_call(self):
        call = self.packer.get_buf()
        sendrecord(self.sock, call)
        while True:
            reply = recvrecord(self.sock)
            u = self.unpacker
            u.reset(reply)
            xid, verf = u.unpack_replyheader()
            if xid == self.lastxid:
                # xid matches, we're done
                return
            elif xid < self.lastxid:
                # Stale data in buffer due to interruption
                # Discard and fetch another record
                continue
            else:
                # xid larger than expected - packet from the future?
                raise RPCError('wrong xid in reply %r instead of %r' % (xid, self.lastxid))


# Client using UDP to a specific port

class RawUDPClient(Client):
    def __init__(self, host, prog, vers, port):
        Client.__init__(self, host, prog, vers, port)
        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect((self.host, self.port))

    def close(self):
        self.sock.close()

    def do_call(self):
        call = self.packer.get_buf()
        self.sock.send(call)
        try:
            from select import select
        except ImportError:
            print('WARNING: select not found, RPC may hang')
            select = None
        BUFSIZE = 8192 # Max UDP buffer size
        timeout = 1
        count = 5
        while 1:
            r, w, x = [self.sock], [], []
            if select:
                r, w, x = select(r, w, x, timeout)
            if self.sock not in r:
                count = count - 1
                if count < 0: raise RPCError('timeout')
                if timeout < 25: timeout = timeout *2
##                              print 'RESEND', timeout, count
                self.sock.send(call)
                continue
            reply = self.sock.recv(BUFSIZE)
            u = self.unpacker
            u.reset(reply)
            xid, verf = u.unpack_replyheader()
            if xid != self.lastxid:
##                              print 'BAD xid'
                continue
            break


# Client using UDP broadcast to a specific port

class RawBroadcastUDPClient(RawUDPClient):

    def __init__(self, bcastaddr, prog, vers, port):
        RawUDPClient.__init__(self, bcastaddr, prog, vers, port)
        self.reply_handler = None
        self.timeout = 30

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def set_reply_handler(self, reply_handler):
        self.reply_handler = reply_handler

    def set_timeout(self, timeout):
        self.timeout = timeout # Use None for infinite timeout

    def make_call(self, proc, args, pack_func, unpack_func):
        if pack_func is None and args is not None:
            raise TypeError('non-null args with null pack_func')
        self.start_call(proc)
        if pack_func:
            pack_func(args)
        call = self.packer.get_buf()
        self.sock.sendto(call, (self.host, self.port))
        try:
            from select import select
        except ImportError:
            print('WARNING: select not found, broadcast will hang')
            select = None
        BUFSIZE = 8192 # Max UDP buffer size (for reply)
        replies = []
        if unpack_func is None:
            def dummy(): pass
            unpack_func = dummy
        while 1:
            r, w, x = [self.sock], [], []
            if select:
                if self.timeout is None:
                    r, w, x = select(r, w, x)
                else:
                    r, w, x = select(r, w, x, self.timeout)
            if self.sock not in r:
                break
            reply, fromaddr = self.sock.recvfrom(BUFSIZE)
            u = self.unpacker
            u.reset(reply)
            xid, verf = u.unpack_replyheader()
            if xid != self.lastxid:
##                              print 'BAD xid'
                continue
            reply = unpack_func()
            self.unpacker.done()
            replies.append((reply, fromaddr))
            if self.reply_handler:
                self.reply_handler(reply, fromaddr)
        return replies


# Port mapper interface

# Program number, version and (fixed!) port number
PMAP_PROG = 100000
PMAP_VERS = 2
PMAP_PORT = 111

# Procedure numbers
PMAPPROC_NULL = 0                       # (void) -> void
PMAPPROC_SET = 1                        # (mapping) -> bool
PMAPPROC_UNSET = 2                      # (mapping) -> bool
PMAPPROC_GETPORT = 3                    # (mapping) -> unsigned int
PMAPPROC_DUMP = 4                       # (void) -> pmaplist
PMAPPROC_CALLIT = 5                     # (call_args) -> call_result

# A mapping is (prog, vers, prot, port) and prot is one of:

IPPROTO_TCP = 6
IPPROTO_UDP = 17

# A pmaplist is a variable-length list of mappings, as follows:
# either (1, mapping, pmaplist) or (0).

# A call_args is (prog, vers, proc, args) where args is opaque;
# a call_result is (port, res) where res is opaque.


class PortMapperPacker(Packer):

    def pack_mapping(self, mapping):
        prog, vers, prot, port = mapping
        self.pack_uint(prog)
        self.pack_uint(vers)
        self.pack_uint(prot)
        self.pack_uint(port)

    def pack_pmaplist(self, list):
        self.pack_list(list, self.pack_mapping)

    def pack_call_args(self, ca):
        prog, vers, proc, args = ca
        self.pack_uint(prog)
        self.pack_uint(vers)
        self.pack_uint(proc)
        self.pack_opaque(args)


class PortMapperUnpacker(Unpacker):

    def unpack_mapping(self):
        prog = self.unpack_uint()
        vers = self.unpack_uint()
        prot = self.unpack_uint()
        port = self.unpack_uint()
        return prog, vers, prot, port

    def unpack_pmaplist(self):
        return self.unpack_list(self.unpack_mapping)

    def unpack_call_result(self):
        port = self.unpack_uint()
        res = self.unpack_opaque()
        return port, res


class PartialPortMapperClient:

    def __init__(self):
        self.packer = PortMapperPacker()
        self.unpacker = PortMapperUnpacker('')

    def set(self, mapping):
        return self.make_call(PMAPPROC_SET, mapping, \
                self.packer.pack_mapping, \
                self.unpacker.unpack_uint)

    def unset(self, mapping):
        return self.make_call(PMAPPROC_UNSET, mapping, \
                self.packer.pack_mapping, \
                self.unpacker.unpack_uint)

    def get_port(self, mapping):
        return self.make_call(PMAPPROC_GETPORT, mapping, \
                self.packer.pack_mapping, \
                self.unpacker.unpack_uint)

    def dump(self):
        return self.make_call(PMAPPROC_DUMP, None, \
                None, \
                self.unpacker.unpack_pmaplist)

    def callit(self, ca):
        return self.make_call(PMAPPROC_CALLIT, ca, \
                self.packer.pack_call_args, \
                self.unpacker.unpack_call_result)


class TCPPortMapperClient(PartialPortMapperClient, RawTCPClient):

    def __init__(self, host):
        RawTCPClient.__init__(self, host, PMAP_PROG, PMAP_VERS, PMAP_PORT)
        PartialPortMapperClient.__init__(self)


class UDPPortMapperClient(PartialPortMapperClient, RawUDPClient):

    def __init__(self, host):
        RawUDPClient.__init__(self, host, PMAP_PROG, PMAP_VERS, PMAP_PORT)
        PartialPortMapperClient.__init__(self)


class BroadcastUDPPortMapperClient(PartialPortMapperClient, RawBroadcastUDPClient):

    def __init__(self, bcastaddr):
        RawBroadcastUDPClient.__init__(self, bcastaddr, PMAP_PROG, PMAP_VERS, PMAP_PORT)
        PartialPortMapperClient.__init__(self)


# Generic clients that find their server through the Port mapper

class TCPClient(RawTCPClient):

    def __init__(self, host, prog, vers, port=0):
        if port == 0:
            pmap = TCPPortMapperClient(host)
            port = pmap.get_port((prog, vers, IPPROTO_TCP, 0))
            pmap.close()
        if port == 0:
            raise RPCError('program not registered')
        RawTCPClient.__init__(self, host, prog, vers, port)


class UDPClient(RawUDPClient):

    def __init__(self, host, prog, vers, port=0):
        if port == 0:
            pmap = UDPPortMapperClient(host)
            port = pmap.get_port((prog, vers, IPPROTO_UDP, 0))
            pmap.close()
        if port == 0:
            raise RPCError('program not registered')
        RawUDPClient.__init__(self, host, prog, vers, port)


class BroadcastUDPClient(Client):

    def __init__(self, bcastaddr, prog, vers):
        self.pmap = BroadcastUDPPortMapperClient(bcastaddr)
        self.pmap.set_reply_handler(self.my_reply_handler)
        self.prog = prog
        self.vers = vers
        self.user_reply_handler = None
        self.addpackers()

    def close(self):
        self.pmap.close()

    def set_reply_handler(self, reply_handler):
        self.user_reply_handler = reply_handler

    def set_timeout(self, timeout):
        self.pmap.set_timeout(timeout)

    def my_reply_handler(self, reply, fromaddr):
        port, res = reply
        self.unpacker.reset(res)
        result = self.unpack_func()
        self.unpacker.done()
        self.replies.append((result, fromaddr))
        if self.user_reply_handler is not None:
            self.user_reply_handler(result, fromaddr)

    def make_call(self, proc, args, pack_func, unpack_func):
        self.packer.reset()
        if pack_func:
            pack_func(args)
        if unpack_func is None:
            def dummy(): pass
            self.unpack_func = dummy
        else:
            self.unpack_func = unpack_func
        self.replies = []
        packed_args = self.packer.get_buf()
        dummy_replies = self.pmap.Callit( \
                (self.prog, self.vers, proc, packed_args))
        return self.replies


# Server classes

# These are not symmetric to the Client classes
# XXX No attempt is made to provide authorization hooks yet

class Server:

    def __init__(self, host, prog, vers, port):
        self.host = host # Should normally be '' for default interface
        self.prog = prog
        self.vers = vers
        self.port = port # Should normally be 0 for random port
        self.registered = False
        self.addpackers()

    def __del__(self):
        # make sure to unregister on delete
        if self.registered:
            self.unregister()

    def register(self):
        mapping = self.prog, self.vers, self.prot, self.port
        p = TCPPortMapperClient(self.host)
        if not p.set(mapping):
            raise RPCError('register failed')
        self.registered = True

    def unregister(self):
        mapping = self.prog, self.vers, self.prot, self.port
        p = TCPPortMapperClient(self.host)
        if not p.unset(mapping):
            raise RPCError('unregister failed')
        self.registered = False

    def handle(self, call):
        # Don't use unpack_header but parse the header piecewise
        # XXX I have no idea if I am using the right error responses!
        self.unpacker.reset(call)
        self.packer.reset()
        xid = self.unpacker.unpack_uint()
        self.packer.pack_uint(xid)
        temp = self.unpacker.unpack_enum()
        if temp != CALL:
            return None # Not worthy of a reply
        self.packer.pack_uint(REPLY)
        temp = self.unpacker.unpack_uint()
        if temp != RPCVERSION:
            self.packer.pack_uint(MSG_DENIED)
            self.packer.pack_uint(RPC_MISMATCH)
            self.packer.pack_uint(RPCVERSION)
            self.packer.pack_uint(RPCVERSION)
            return self.packer.get_buf()
        self.packer.pack_uint(MSG_ACCEPTED)
        self.packer.pack_auth((AUTH_NULL, make_auth_null()))
        prog = self.unpacker.unpack_uint()
        if prog != self.prog:
            self.packer.pack_uint(PROG_UNAVAIL)
            return self.packer.get_buf()
        vers = self.unpacker.unpack_uint()
        if vers != self.vers:
            self.packer.pack_uint(PROG_MISMATCH)
            self.packer.pack_uint(self.vers)
            self.packer.pack_uint(self.vers)
            return self.packer.get_buf()
        proc = self.unpacker.unpack_uint()
        methname = 'handle_' + repr(proc)
        try:
            meth = getattr(self, methname)
        except AttributeError:
            self.packer.pack_uint(PROC_UNAVAIL)
            return self.packer.get_buf()
        cred = self.unpacker.unpack_auth()
        verf = self.unpacker.unpack_auth()
        try:
            meth() # Unpack args, call turn_around(), pack reply
        except (EOFError, RPCGarbageArgs):
            # Too few or too many arguments
            self.packer.reset()
            self.packer.pack_uint(xid)
            self.packer.pack_uint(REPLY)
            self.packer.pack_uint(MSG_ACCEPTED)
            self.packer.pack_auth((AUTH_NULL, make_auth_null()))
            self.packer.pack_uint(GARBAGE_ARGS)
        return self.packer.get_buf()

    def turn_around(self):
        try:
            self.unpacker.done()
        except RuntimeError:
            raise RPCGarbageArgs
        self.packer.pack_uint(SUCCESS)

    def handle_0(self): # Handle NULL message
        self.turn_around()

    def addpackers(self):
        # Override this to use derived classes from Packer/Unpacker
        self.packer = Packer()
        self.unpacker = Unpacker('')


class TCPServer(Server):

    def __init__(self, host, prog, vers, port):
        Server.__init__(self, host, prog, vers, port)
        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.prot = IPPROTO_TCP
        self.sock.bind((self.host, self.port))
        self.host, self.port = self.sock.getsockname()

    def loop(self):
        self.sock.listen(0)
        while 1:
            self.session(self.sock.accept())

    def session(self, connection):
        sock, (host, port) = connection
        while 1:
            try:
                call = recvrecord(sock)
            except EOFError:
                break
            except socket.error:
                print('socket error:', sys.exc_info()[0])
                break
            reply = self.handle(call)
            if reply is not None:
                sendrecord(sock, reply)

    def forkingloop(self):
        # Like loop but uses forksession()
        self.sock.listen(0)
        while 1:
            self.forksession(self.sock.accept())

    def forksession(self, connection):
        # Like session but forks off a subprocess
        import os
        # Wait for deceased children
        try:
            while 1:
                pid, sts = os.waitpid(0, os.WNOHANG)
        except os.error:
            pass
        pid = None
        try:
            pid = os.fork()
            if pid: # Parent
                connection[0].close()
                return
            # Child
            self.session(connection)
        finally:
            # Make sure we don't fall through in the parent
            if pid == 0:
                os._exit(0)


class UDPServer(Server):

    def __init__(self, host, prog, vers, port):
        Server.__init__(self, host, prog, vers, port)
        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.prot = IPPROTO_UDP
        self.sock.bind((self.host, self.port))
        self.host, self.port = self.sock.getsockname()

    def loop(self):
        while 1:
            self.session()

    def session(self):
        call, host_port = self.sock.recvfrom(8192)
        reply = self.handle(call)
        if reply is not None:
            self.sock.sendto(reply, host_port)


# Simple test program -- dump portmapper status

def test(host = ''):
    pmap = UDPPortMapperClient(host)
    list = pmap.dump()
    list.sort()
    for prog, vers, prot, port in list:
        st = "%d %d " % (prog, vers)
        if prot == IPPROTO_TCP: st += "tcp "
        elif prot == IPPROTO_UDP: st += "udp "
        else: st += "%d " % prot
        st += "%d" % port
        print(st)


