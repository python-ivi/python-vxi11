#!/usr/bin/env python

import nose
from nose.tools import eq_
from vxi11.vxi11 import parse_visa_resource_string

def test_parse_visa_resource_string():
    f = parse_visa_resource_string

    res = f('TCPIP::10.0.0.1::INSTR')
    eq_(res['type'], 'TCPIP')
    eq_(res['prefix'], 'TCPIP')
    eq_(res['arg1'], '10.0.0.1')
    eq_(res['suffix'], 'INSTR')

    res = f('TCPIP0::10.0.0.1::INSTR')
    eq_(res['type'], 'TCPIP')
    eq_(res['prefix'], 'TCPIP0')
    eq_(res['arg1'], '10.0.0.1')
    eq_(res['suffix'], 'INSTR')

    res = f('TCPIP::10.0.0.1::gpib,5::INSTR')
    eq_(res['type'], 'TCPIP')
    eq_(res['prefix'], 'TCPIP')
    eq_(res['arg1'], '10.0.0.1')
    eq_(res['suffix'], 'INSTR')

    res = f('TCPIP0::10.0.0.1::gpib,5::INSTR')
    eq_(res['type'], 'TCPIP')
    eq_(res['prefix'], 'TCPIP0')
    eq_(res['arg1'], '10.0.0.1')
    eq_(res['arg2'], 'gpib,5')
    eq_(res['suffix'], 'INSTR')

    res = f('TCPIP0::10.0.0.1::usb0::INSTR')
    eq_(res['type'], 'TCPIP')
    eq_(res['prefix'], 'TCPIP0')
    eq_(res['arg1'], '10.0.0.1')
    eq_(res['arg2'], 'usb0')
    eq_(res['suffix'], 'INSTR')

    res = f('TCPIP0::10.0.0.1::usb0[1234::5678::MYSERIAL::0]::INSTR')
    eq_(res['type'], 'TCPIP')
    eq_(res['prefix'], 'TCPIP0')
    eq_(res['arg1'], '10.0.0.1')
    eq_(res['arg2'], 'usb0[1234::5678::MYSERIAL::0]')
    eq_(res['suffix'], 'INSTR')

