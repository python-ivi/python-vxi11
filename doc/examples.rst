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

Asyncio connections
===================
The **AsyncInstrument** class can be used for usage with asyncio::
    
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
