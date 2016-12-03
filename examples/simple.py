import asyncio

import dsc_it100

loop = asyncio.get_event_loop()
driver = dsc_it100.Driver('/dev/ttyUSB0', loop)
driver.connect()
loop.run_forever()
loop.close()
