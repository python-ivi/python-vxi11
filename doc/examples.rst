=====================
Python VXI11 Examples
=====================

Opening a connection
====================

Connect to an Agilent MSO7104A oscilloscope on IP address 192.168.1.104::

    >>> import vxi11
    >>> instr =  vxi11.Instrument("192.168.1.104")
    >>> print(instr.ask("*IDN?"))
    'AGILENT TECHNOLOGIES,MSO7104A,MY********,06.16.0001'

Connect to an Agilent E3649A via an HP 2050A GPIB bridge::

    >>> import vxi11
    >>> instr = vxi11.Instrument("192.168.1.105", "gpib,5")
    >>> print(instr.ask("*IDN?"))
    'Agilent Technologies,E3649A,0,1.4-5.0-1.0'

Configuring connections
=======================

Open a connection and set the timeout::

    >>> import vxi11
    >>> instr = vxi11.Instrument("192.168.1.104")
    >>> instr.timeout = 60*1000
    >>> print(instr.ask("*TST?"))
    '0'
