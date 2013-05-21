"""Amazon EC2-related logic."""
import logging
import time

import boto

log = logging.getLogger(__name__)


class EC2InstanceStarter(object):
    """Contains logic for starting an EC2 instance."""

    def __init__(
            self, region, aws_access_key_id, aws_secret_access_key,
            ami_id, key_name, instance_type, security_groups,
            running_state_check_pre_delay=None,
            running_state_check_timeout=None,
            message_callback=None):
        """Initializes instance."""

        super(EC2InstanceStarter, self).__init__()

        self._region = region
        self._aws_access_key_id = aws_access_key_id
        self._aws_secret_access_key = aws_secret_access_key
        self._ami_id = ami_id
        self._key_name = key_name
        self._instance_type = instance_type
        self._security_groups = security_groups
        self._running_state_check_pre_delay = running_state_check_pre_delay
        self._running_state_check_timeout = running_state_check_timeout
        self._message_callback = message_callback

    def _init_run_vars(self):
        """Initializes variables used for running logic."""
        self._messages = []
        self._reservation = None
        self._instance = None

    @property
    def messages(self):
        """Returns messages."""
        return self._messages

    @property
    def reservation(self):
        """Returns an EC2 Reservation response object."""
        return self._reservation

    @property
    def instance(self):
        """Returns an EC2 instance object."""
        return self._instance

    def _store_message(self, message, message_type='info'):
        """Stores message."""
        self._messages.append(dict(
            message=message,
            message_type=message_type))
        if self._message_callback:
            self._message_callback(self, message, message_type)

    def _delay_running_state_check(self):
        """Delays running state check."""

        if self._running_state_check_pre_delay is not None:
            # Sleep, to give time for EC2 instance to reach running state,
            # before attempting to access it.
            msg = 'Waiting for %s second(s) to give time for EC2 instance to reach running state.' % (
                self._running_state_check_pre_delay)
            log.info(msg)
            self._store_message(msg)
            time.sleep(self._running_state_check_pre_delay)

    def _wait_for_instance_running_state(self):
        """Polls EC2 instance state until it becomes running or timed out."""

        assert self._instance

        tries = 0
        start_time = time.time()
        while True:
            try:
                tries += 1
                msg = 'Waiting for instance to run, tries=%s.' % (tries,)
                log.info(msg)
                self._store_message(msg)
                self._instance.update()
                if self._instance.state == 'running':
                    break
            except StandardError, e:
                log.exception('EXCEPTION')
                self._store_message('EXCEPTION %s: %s' % (type(e), e), 'error')

            if (self._running_state_check_timeout and
                    time.time() - start_time > self._running_state_check_timeout):
                msg = 'Gave up trying to wait for EC2 instance to run.'
                log.error(msg)
                self._store_message(msg, 'error')
                break
            time.sleep(0.1)

    def run(self):
        """Main EC2 instance starter logic."""

        self._init_run_vars()

        conn = boto.ec2.connect_to_region(
            self._region,
            aws_access_key_id=self._aws_access_key_id,
            aws_secret_access_key=self._aws_secret_access_key)

        self._reservation = conn.run_instances(
            self._ami_id,
            key_name=self._key_name,
            instance_type=self._instance_type,
            security_groups=self._security_groups)
        log.debug('reservation: %s' % (self._reservation,))

        if self._reservation and self._reservation.instances:
            self._instance = self._reservation.instances[0]

            self._delay_running_state_check()
            self._wait_for_instance_running_state()

    def terminate_instances(self):
        """Terminates started EC2 instances."""

        if self._reservation and self._reservation.instances:
            for instance in self._reservation.instances:
                instance.terminate()
                msg = 'EC2 instance terminated.'
                log.info(msg)
                self._store_message(msg)
