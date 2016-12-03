import unittest

import dsc_it100


class TestProtocol(unittest.TestCase):
    def test_checksum(self):
        message = dsc_it100.Message(dsc_it100.COMMAND_POLL)
        self.assertEqual(message.checksum(), '90')

        message = dsc_it100.Message(dsc_it100.COMMAND_STATUS_REQUEST)
        self.assertEqual(message.checksum(), '91')

        message = dsc_it100.Message(dsc_it100.COMMAND_CODE_SEND, '123456')
        self.assertEqual(message.checksum(), 'C7')

    def test_serialization(self):
        message = dsc_it100.Message(dsc_it100.COMMAND_CODE_SEND, '123456')
        self.assertEqual(message.serialize(), '200123456C7\r\n')

    def test_deserialization(self):
        message = dsc_it100.Message.deserialize('200123456C7\r\n')
        self.assertEqual(message.command, dsc_it100.COMMAND_CODE_SEND)
        self.assertEqual(message.data, '123456')

        # Invalid messages.
        with self.assertRaises(ValueError):
            dsc_it100.Message.deserialize('200123456')
        with self.assertRaises(ValueError):
            dsc_it100.Message.deserialize('20012345600\r\n')
        with self.assertRaises(ValueError):
            dsc_it100.Message.deserialize('200123456C7')
