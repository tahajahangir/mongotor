# coding: utf-8
from __future__ import with_statement
from tornado.ioloop import IOLoop
from tornado import testing
from mongotor.connection import Connection
from mongotor.errors import InterfaceError, DatabaseError, IntegrityError
from bson import ObjectId
from mongotor import message
from mongotor import helpers

import fudge


class ConnectionTestCase(testing.AsyncTestCase):

    def get_new_ioloop(self):
        return IOLoop.instance()

    def setUp(self):
        super(ConnectionTestCase, self).setUp()
        self.conn = Connection(host="localhost", port=27027)

    def tearDown(self):
        super(ConnectionTestCase, self).tearDown()
        self.conn.close()

    def test_not_connect_to_mongo_raises_error(self):
        """[ConnectionTestCase] - Raises error when can't connect to mongo"""

        self.assertRaisesRegexp(InterfaceError, "Connection refused", Connection,
                                host="localhost", port=27000)

    def test_connect_to_mongo(self):
        """[ConnectionTestCase] - Can stabilish connection to mongo"""

        self.assertTrue(self.conn._connected)

    def test_send_test_message_to_mongo(self):
        """[ConnectionTestCase] - Send message to test driver connection"""

        object_id = ObjectId()
        message_test = message.query(0, 'mongotor_test.$cmd', 0, 1,
            {'driverOIDTest': object_id})

        self.conn.send_message_with_response(message_test, callback=self.stop)
        response, _ = self.wait()

        response = helpers._unpack_response(response)
        result = response['data'][0]

        self.assertEquals(result['oid'], object_id)
        self.assertEquals(result['ok'], 1.0)
        self.assertEquals(result['str'], str(object_id))

    def test_close_connection_to_mongo(self):
        """[ConnectionTestCase] - Can close connection to mongo"""

        self.conn.close()

        self.assertFalse(self.conn._connected)
        self.assertTrue(self.conn._stream.closed())

    def test_return_integrity_error_when_mongo_return_err(self):
        """[ConnectionTestCase] - Returns IntegrityError when mongo return a message with err"""

        object_id = ObjectId()
        message_insert = message.insert('mongotor_test.articles', [{'_id': object_id}],
            False, True, {})

        self.conn.send_message(message_insert, True, callback=self.stop)
        self.wait()

        self.conn.send_message(message_insert, True, callback=self.stop)
        self.assertRaises(IntegrityError, self.wait)

    @fudge.patch('mongotor.connection.helpers')
    def test_raises_error_when_cant_unpack_response(self, fake_helpers):
        """[ConnectionTestCase] - Returns DatabaseError when can't unpack response from mongo"""

        fake_helpers.provides('_unpack_response') \
            .raises(DatabaseError('database error'))

        object_id = ObjectId()
        message_test = message.query(0, 'mongotor_test.$cmd', 0, 1,
            {'driverOIDTest': object_id})

        self.conn.send_message(message_test, with_last_error=True, callback=self.stop)

        self.assertRaisesRegexp(DatabaseError, 'database error', self.wait)

    def test_reconnect_when_connection_was_lost(self):
        """[ConnectionTestCase] - Reconnect to mongo when connection was lost"""

        self.conn.close()
        self.conn._callback = self.stop
        self.wait()

        self.test_send_test_message_to_mongo()

    def test_raises_interface_error_when_cant_reconnect(self):
        """[ConnectionTestCase] - Raises InterfaceError when connection was lost and autoreconnect is False"""

        self.conn = Connection(host="localhost", port=27027, autoreconnect=False)

        self.conn.close()

        self.assertRaisesRegexp(InterfaceError, "connection is closed", self.conn.send_message,
                                'shouldBeMessage', callback=None)

    def test_raises_error_when_stream_reaise_ioerror(self):
        """[ConnectionTestCase] - Raises IOError when stream throw error"""
        fake_stream = fudge.Fake()
        fake_stream.expects('write').raises(IOError())
        fake_stream.has_attr(close=fudge.Fake().is_callable())

        with fudge.patched_context(self.conn, '_stream', fake_stream):
            self.assertRaises(IOError, self.conn.send_message, (0, ''), callback=None)
