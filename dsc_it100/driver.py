import asyncio
import logging

import serial_asyncio

from . import protocol, exceptions

try:
    from asyncio import ensure_future
except ImportError:
    # Python 3.4.3 and earlier has this as async
    # pylint: disable=unused-import
    from asyncio import async
    ensure_future = async

# Exports.
__all__ = [
    'Driver'
]

logger = logging.getLogger(__name__)


class Driver(object):
    """
    DSC IT-100 driver.
    """

    def __init__(self, serial_port, loop=None):
        """
        Constructs the DSC IT-100 driver.

        :param serial_port: Serial port where the IT-100 is connected to
        :param loop: Optional event loop to use
        """

        if loop is None:
            loop = asyncio.get_event_loop()

        self._loop = loop
        self._port = serial_port
        self._reader = None
        self._writer = None

    def connect(self):
        """
        Establishes a connection with the DSC IT-100 module.
        """

        if self._reader or self._writer:
            raise exceptions.DriverError('Driver is already connected')

        self._reader, self._writer = self._loop.run_until_complete(
            serial_asyncio.open_serial_connection(loop=self._loop, url=self._port, baudrate=9600)
        )

        # Spawn coroutine for handling protocol messages.
        ensure_future(self._handle_messages(), loop=self._loop)

    @asyncio.coroutine
    def _handle_messages(self):
        """
        Incoming message handler.
        """

        while not self._reader.at_eof():
            line = yield from self._reader.readline()
            try:
                message = protocol.Message.deserialize(line.decode())
            except ValueError:
                logger.warning("Received malformed message from DSC IT-100.")
                continue

            print('got message', message)

    def close(self):
        """
        Closes the connection with the DSC IT-100 module.
        """

        if not self._writer:
            raise exceptions.DriverError('Driver not connected')

        self._writer.transport.close()
