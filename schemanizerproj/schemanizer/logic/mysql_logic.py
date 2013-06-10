"""MySQL server-related logic."""

import logging
import time

import MySQLdb

log = logging.getLogger(__name__)


class MySQLServerConnectionTester(object):
    """Contains logic for connecting to a MySQL server to test if it is ready."""

    def __init__(
            self, connection_options=None, connect_pre_delay=None,
            connect_timeout=None, message_callback=None):
        """Initializes object."""

        super(MySQLServerConnectionTester, self).__init__()

        self._connect_pre_delay = connect_pre_delay
        self._connect_timeout = connect_timeout
        self._message_callback = message_callback

        if connection_options is None:
            self._connection_options = {}
        else:
            self._connection_options = connection_options

        self._init_run_vars()

    def _init_run_vars(self):
        """Initializes variables needed when logic is run."""
        self._messages = []

    @property
    def message(self):
        """Returns messages."""
        return self._messages

    def _store_message(self, message, message_type='info'):
        """Stores message."""
        self._messages.append(dict(
            message=message,
            message_type=message_type))
        if self._message_callback:
            self._message_callback(message, message_type)

    def run(self):
        """Creates connection to a MySQL server."""

        self._init_run_vars()

        if self._connect_pre_delay:
            # For hosts that were dynamically started such as EC2 instances,
            # this is to give time for MySQL server to start,
            # before attempting to connect to it.
            self._store_message(
                'Waiting for %s second(s) to give time for MySQL server to start. (connect_pre_delay)' % (
                    self._connect_pre_delay,))
            time.sleep(self._connect_pre_delay)

        # Attempt to connect to MySQL server until connected successfully
        # or timed out.
        conn = None
        tries = 0
        start_time = time.time()
        while True:
            try:
                tries += 1
                msg = 'Connecting to MySQL server, tries=%s.' % (tries,)
                log.info(msg)
                self._store_message(msg)
                conn = MySQLdb.connect(**self._connection_options)
                msg = 'Connected to MySQL server.'
                log.info(msg)
                self._store_message(msg)
                break
            except Exception, e:
                log.exception('EXCEPTION')
                self._store_message(
                    'ERROR %s: %s' % (type(e), e), 'error')

            if (self._connect_timeout and
                    time.time() - start_time > self._connect_timeout):
                msg = 'Gave up trying to connect to MySQL server.'
                log.info(msg)
                self._store_message(msg)
                break
            time.sleep(0.1)
        return conn
