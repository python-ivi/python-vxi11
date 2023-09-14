#!/usr/bin/env python

from vxi11.vxi11 import parse_visa_resource_string


def test_parse_visa_resource_string():
    f = parse_visa_resource_string

    res = f('TCPIP::10.0.0.1::INSTR')
    assert res['type'] == 'TCPIP'
    assert res['prefix'] == 'TCPIP'
    assert res['arg1'] == '10.0.0.1'
    assert res['suffix'] == 'INSTR'

    res = f('TCPIP0::10.0.0.1::INSTR')
    assert res['type'] == 'TCPIP'
    assert res['prefix'] == 'TCPIP0'
    assert res['arg1'] == '10.0.0.1'
    assert res['suffix'] == 'INSTR'

    res = f('TCPIP::10.0.0.1::gpib,5::INSTR')
    assert res['type'] == 'TCPIP'
    assert res['prefix'] == 'TCPIP'
    assert res['arg1'] == '10.0.0.1'
    assert res['suffix'] == 'INSTR'

    res = f('TCPIP0::10.0.0.1::gpib,5::INSTR')
    assert res['type'] == 'TCPIP'
    assert res['prefix'] == 'TCPIP0'
    assert res['arg1'] == '10.0.0.1'
    assert res['arg2'] == 'gpib,5'
    assert res['suffix'] == 'INSTR'

    res = f('TCPIP0::10.0.0.1::usb0::INSTR')
    assert res['type'] == 'TCPIP'
    assert res['prefix'] == 'TCPIP0'
    assert res['arg1'] == '10.0.0.1'
    assert res['arg2'] == 'usb0'
    assert res['suffix'] == 'INSTR'

    res = f('TCPIP0::10.0.0.1::usb0[1234::5678::MYSERIAL::0]::INSTR')
    assert res['type'] == 'TCPIP'
    assert res['prefix'] == 'TCPIP0'
    assert res['arg1'] == '10.0.0.1'
    assert res['arg2'] == 'usb0[1234::5678::MYSERIAL::0]'
    assert res['suffix'] == 'INSTR'
