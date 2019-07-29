import asyncio
import logging
from asyncio import ensure_future

import serial_asyncio

from . import protocol, exceptions, state


# Exports.
__all__ = [
    'Driver'
]

logger = logging.getLogger(__name__)


class Driver(object):
    """
    DSC IT-100 driver.
    """

    # Update types.
    UPDATE_ZONE = 'zone'
    UPDATE_PARTITION = 'partition'
    UPDATE_GENERAL = 'general'

    # State update handlers.
    state_update_handlers = {
        # Zone updates.
        protocol.NOTIFY_ZONE_ALARM: {'type': UPDATE_ZONE, 'status': {'alarm': True}},
        protocol.NOTIFY_ZONE_ALARM_RESTORE: {'type': UPDATE_ZONE, 'status': {'alarm': False}},
        protocol.NOTIFY_ZONE_TAMPER: {'type': UPDATE_ZONE, 'status': {'tamper': True}},
        protocol.NOTIFY_ZONE_TAMPER_RESTORE: {'type': UPDATE_ZONE, 'status': {'tamper': False}},
        protocol.NOTIFY_ZONE_FAULT: {'type': UPDATE_ZONE, 'status': {'fault': True}},
        protocol.NOTIFY_ZONE_FAULT_RESTORE: {'type': UPDATE_ZONE, 'status': {'fault': False}},
        protocol.NOTIFY_ZONE_OPEN: {'type': UPDATE_ZONE, 'status': {'open': True}},
        protocol.NOTIFY_ZONE_RESTORED: {'type': UPDATE_ZONE, 'status': {'open': False}},

        # Partition updates.
        protocol.NOTIFY_PARTITION_READY: {'type': UPDATE_PARTITION, 'status': {'ready': True}},
        protocol.NOTIFY_PARTITION_NOT_READY: {'type': UPDATE_PARTITION, 'status': {'ready': False}},
        protocol.NOTIFY_PARTITION_ARMED: {'type': UPDATE_PARTITION},
        protocol.NOTIFY_PARTITION_READY_TO_FORCE_ARM: {'type': UPDATE_PARTITION, 'status': {'ready': True}},
        protocol.NOTIFY_PARTITION_IN_ALARM: {'type': UPDATE_PARTITION, 'status': {'alarm': True}},
        protocol.NOTIFY_PARTITION_DISARMED: {'type': UPDATE_PARTITION, 'status': {
            'alarm': False,
            'armed_stay': False,
            'armed_away': False,
            'exit_delay': False,
            'entry_delay': False,
        }},
        protocol.NOTIFY_PARTITION_EXIT_DELAY: {'type': UPDATE_PARTITION, 'status': {'exit_delay': True}},
        protocol.NOTIFY_PARTITION_ENTRY_DELAY: {'type': UPDATE_PARTITION, 'status': {'entry_delay': True}},
        protocol.NOTIFY_PARTITION_BUSY: {'type': UPDATE_PARTITION},
        protocol.NOTIFY_PARTITION_USER_CLOSING: {'type': UPDATE_PARTITION},
        protocol.NOTIFY_PARTITION_SPECIAL_CLOSING: {'type': UPDATE_PARTITION},
        protocol.NOTIFY_PARTITION_PARTIAL_CLOSING: {'type': UPDATE_PARTITION},
        protocol.NOTIFY_PARTITION_USER_OPENING: {'type': UPDATE_PARTITION, 'status': {
            'alarm': False,
            'armed_stay': False,
            'armed_away': False,
            'exit_delay': False,
            'entry_delay': False,
        }},
        protocol.NOTIFY_PARTITION_SPECIAL_OPENING: {'type': UPDATE_PARTITION, 'status': {
            'alarm': False,
            'armed_stay': False,
            'armed_away': False,
            'exit_delay': False,
            'entry_delay': False,
        }},
        protocol.NOTIFY_PARTITION_TROUBLE: {'type': UPDATE_PARTITION, 'status': {'trouble': True}},
        protocol.NOTIFY_PARTITION_TROUBLE_RESTORED: {'type': UPDATE_PARTITION, 'status': {'trouble': False}},

        # General updates.
        protocol.NOTIFY_PANEL_BATTERY_TROUBLE: {'type': UPDATE_GENERAL, 'battery_trouble': True},
        protocol.NOTIFY_PANEL_BATTERY_RESTORED: {'type': UPDATE_GENERAL, 'battery_trouble': False},
        protocol.NOTIFY_PANEL_AC_TROUBLE: {'type': UPDATE_GENERAL, 'ac_trouble': True},
        protocol.NOTIFY_PANEL_AC_RESTORED: {'type': UPDATE_GENERAL, 'ac_trouble': False},
    }

    def __init__(self, serial_port, loop=None, baudrate=9600):
        """
        Constructs the DSC IT-100 driver.

        :param serial_port: Serial port where the IT-100 is connected to
        :param baudrate: Optional baud rate for serial port
        :param loop: Optional event loop to use
        """

        if loop is None:
            loop = asyncio.get_event_loop()

        self._loop = loop
        self._port = serial_port
        self._baudrate = baudrate
        self._reader = None
        self._writer = None
        self._code = None
        self._state = state.AlarmState()

        # Handlers.
        self._handler_zone_update = None
        self._handler_partition_update = None
        self._handler_general_update = None

    @property
    def handler_zone_update(self):
        return self._handler_zone_update

    @handler_zone_update.setter
    def handler_zone_update(self, value):
        self._handler_zone_update = value

    @property
    def handler_partition_update(self):
        return self._handler_partition_update

    @handler_partition_update.setter
    def handler_partition_update(self, value):
        self._handler_partition_update = value

    @property
    def handler_general_update(self):
        return self._handler_general_update

    @handler_general_update.setter
    def handler_general_update(self, value):
        self._handler_general_update = value

    def set_alarm_code(self, code):
        """
        Configure alarm code to be sent to the IT-100 module upon request.
        """

        self._code = code

    def connect(self):
        """
        Establishes a connection with the DSC IT-100 module.
        """

        if self._reader or self._writer:
            raise exceptions.DriverError('Driver is already connected')

        ensure_future(self._connect(), loop=self._loop)

    @asyncio.coroutine
    def _connect(self):
        self._reader, self._writer = yield from serial_asyncio.open_serial_connection(
            loop=self._loop, url=self._port, baudrate=self._baudrate)

        # Spawn coroutine for handling protocol messages.
        ensure_future(self._handle_messages(), loop=self._loop)
        self.send_status_request()

    def send_message(self, command, data=''):
        """
        Sends a protocol message to the IT-100 unit.
        """

        self._writer.write(protocol.Message(command, data).serialize().encode('ascii'))

    def send_status_request(self):
        """
        Send a status request message to the IT-100 unit.
        """

        self.send_message(protocol.COMMAND_STATUS_REQUEST)

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

            if message.command == protocol.NOTIFY_CODE_REQUIRED:
                if not self._code:
                    logger.warning("Received code request, but no code has been set.")
                    continue

                self.send_message(protocol.COMMAND_CODE_SEND, self._code[:6])
            else:
                # Check if a handler is registered for the given message.
                handler = self.state_update_handlers.get(message.command, None)
                if handler is None:
                    logger.debug("No handler for notification '{}'.".format(message.command))
                    continue

                handler = handler.copy()
                handler_type = handler['type']
                del handler['type']

                if handler_type == Driver.UPDATE_ZONE:
                    # Zone update.
                    try:
                        zone = int(message.data[1:])
                    except ValueError:
                        logger.warning("Received malformed zone identifier from DSC IT-100.")
                        continue

                    zone = self._state.update_zone(zone, handler)
                    if self._handler_zone_update is not None:
                        self._handler_zone_update(self, zone)
                elif handler_type == Driver.UPDATE_PARTITION:
                    # Partition update.
                    try:
                        partition = int(message.data[0])
                    except ValueError:
                        logger.warning("Received malformed partition identifier from DSC IT-100.")
                        continue

                    partition = self._state.update_partition(partition, handler)
                    if self._handler_partition_update is not None:
                        self._handler_partition_update(self, partition)
                elif handler_type == Driver.UPDATE_GENERAL:
                    # General status update.
                    general = self._state.update_general(handler)
                    if self._handler_general_update is not None:
                        self._handler_general_update(self, general)

    def close(self):
        """
        Closes the connection with the DSC IT-100 module.
        """

        if not self._writer:
            raise exceptions.DriverError('Driver not connected')

        self._writer.transport.close()

    def get_alarm_state(self):
        """
        Return current alarm state.
        """

        return self._state
