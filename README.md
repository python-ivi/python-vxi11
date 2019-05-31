# Python VXI-11 Readme

For more information and updates:
http://alexforencich.com/wiki/en/python-vxi11/start

GitHub repository:
https://github.com/python-ivi/python-vxi11

Google group:
https://groups.google.com/d/forum/python-ivi

## Introduction

Python VXI-11 provides a pure Python VXI-11 driver for controlling instruments
over Ethernet.

## Requirements

* Python 2 or Python 3

## Installation

Extract and run

    # python setup.py install

## Usage examples

Connecting to Agilent MSO7104A via LXI:

    import vxi11
    instr =  vxi11.Instrument("192.168.1.104")
    print(instr.ask("*IDN?"))
    # returns 'AGILENT TECHNOLOGIES,MSO7104A,MY********,06.16.0001'

Connecting to Agilent E3649A on GPIB address 5 via HP 2050A GPIB bridge:

    import vxi11
    instr = vxi11.Instrument("192.168.1.105", "gpib,5")
    print(instr.ask("*IDN?"))
    # returns 'Agilent Technologies,E3649A,0,1.4-5.0-1.0'

Connecting to Agilent MSO-X 3014A via USBTMC via Agilent E5810 GPIB bridge:

    import vxi11
    instr = vxi11.Instrument("192.168.1.201", "usb0[2391::6056::MY********::0]")
    print(instr.ask("*IDN?"))
    # returns 'AGILENT TECHNOLOGIES,MSO-X 3014A,MY********,02.35.2013061800'

It is also possible to connect with VISA resource strings like so:

    import vxi11
    instr =  vxi11.Instrument("TCPIP::192.168.1.104::INSTR")
    print(instr.ask("*IDN?"))
    # returns 'AGILENT TECHNOLOGIES,MSO7104A,MY********,06.16.0001'

and:

    import vxi11
    instr = vxi11.Instrument("TCPIP::192.168.1.105::gpib,5::INSTR")
    print(instr.ask("*IDN?"))
    # returns 'Agilent Technologies,E3649A,0,1.4-5.0-1.0'

and:

    import vxi11
    instr = vxi11.Instrument("TCPIP::192.168.1.201::usb0[2391::6056::MY********::0]::INSTR")
    print(instr.ask("*IDN?"))
    # returns 'AGILENT TECHNOLOGIES,MSO-X 3014A,MY********,02.35.2013061800'


## Python 3 asyncio usage example

    from asyncio import get_event_loop
    from vxi11 import vxi11
    
    
    instr = vxi11.AsyncInstrument("sqs-ilh-las-osz_dpo71254c")
    
    
    async def acquire():
        await instr.open()
        print(await instr.ask("*IDN?"))
        # In our case, prints 'TEKTRONIX,DPO71254C,C500158,CF:91.1CT FV:10.5.1 Build 24'
    
        cmd = "DAT:SOU " + ",".join(f"CH{x}" for x in range(1, 5))
        await instr.write(cmd)
    
        await instr.write("WAVFRMS?")
    
        readout = await instr.read_raw(-1)
        print(readout)
    
        await instr.close()
    
    
    loop = get_event_loop()
    loop.run_until_complete(acquire())
