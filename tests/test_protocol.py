import unittest

import dsc_it100


class TestProtocol(unittest.TestCase):
    def test_checksum(self):
        message = dsc_it100.Message(dsc_it100.COMMAND_POLL)
        self.assertEquals(message.checksum(), '\x90')

        message = dsc_it100.Message(dsc_it100.COMMAND_STATUS_REQUEST)
        self.assertEquals(message.checksum(), '\x91')

        message = dsc_it100.Message(dsc_it100.COMMAND_CODE_SEND, '123456')
        self.assertEquals(message.checksum(), '\xc7')

    def test_serialization(self):
        message = dsc_it100.Message(dsc_it100.COMMAND_CODE_SEND, '123456')
        self.assertEquals(message.serialize(), '200123456\xc7\r\n')

    def test_deserialization(self):
        message = dsc_it100.Message.deserialize('200123456\xc7\r\n')
        self.assertEquals(message.command, dsc_it100.COMMAND_CODE_SEND)
        self.assertEquals(message.data, '123456')

        # Invalid messages.
        with self.assertRaises(ValueError):
            dsc_it100.Message.deserialize('200123456')
        with self.assertRaises(ValueError):
            dsc_it100.Message.deserialize('200123456\x00\r\n')
        with self.assertRaises(ValueError):
            dsc_it100.Message.deserialize('200123456\xc7')
