#
# Local Settings
#
# Use this file to override the default values provided in settings.py.
#


ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.' + 'mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'schemanizer_dev',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'sandbox',
        'PASSWORD': 'sandbox',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'


# Mail is sent using the SMTP host and port specified in the EMAIL_HOST and
# EMAIL_PORT settings.  The EMAIL_HOST_USER and EMAIL_HOST_PASSWORD settings,
# if set, are used to authenticate to the SMTP server, and the EMAIL_USE_TLS
# setting controls whether a secure connection is used.
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'test@example.com'
EMAIL_HOST_PASSWORD = 'pass'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'Schemanizer <schemanizer@localhost.local>'
# If True, no schemanizer emails will be sent.
DISABLE_SEND_MAIL = False


#==============================================================================
# AWS data for launching an EC2 instance (for use in reviewing changesets)
#==============================================================================
#
# AWS Credentials
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
#
# The name of the region to connect to.
AWS_REGION = 'ap-southeast-1'
#
# The ID of the image to run.
AWS_AMI_ID = 'ami-4edb971c'
#
# The name of the key pair with which to launch instances.
AWS_KEY_NAME = 'tools-sqlcanon1-sg-key'
#
# The names (list of strings) of the security groups with which to associate instance.
AWS_SECURITY_GROUPS = ['quicklaunch-1']
#
# The type of instance to run.
# Choices:
#   t1.micro
#   m1.small
#   m1.medium
#   m1.large
#   m1.xlarge
#   c1.medium
#   c1.xlarge
#   m2.xlarge
#   m2.2xlarge
#   m2.4xlarge
#   cc1.4xlarge
#   cg1.4xlarge
#   cc2.8xlarge
AWS_INSTANCE_TYPE = 'm1.small'

# AWS_SSH_KEY_FILE and AWS_SSH_USER are used to connect to an EC2 instance
# via SSH to check the status of MySQL server and to create
# a MySQL user with the required privileges.
AWS_SSH_KEY_FILE = None     # Full path to the key file to be used when
                            # connecting to an  EC2 instance via SSH,
                            # this is the private key file downloaded from
                            # the AWS console.
                            #
AWS_SSH_USER = 'root'       # username to be used when connecting to
                            # an EC2 instance via ssh.
                            # This user should be able to connect
                            # to the MySQL server locally without a password.

#
# MySQL connection options for reviewing changesets
#
# If MYSQL_HOST is None, the EC2 instance host name is used.
# MYSQL_PORT, MYSQL_USER and MYSQL_PASSWORD are also used
# in changeset apply operations.
MYSQL_HOST = None
MYSQL_PORT = None
MYSQL_USER = 'sandbox'      # This user needs a RELOAD and PROCESS privileges
                            # during the changeset review/apply process.
                            # To grant privileges, run the following in
                            # MySQL console using a user that can grant
                            # privileges to other users:
                            #
                            # GRANT RELOAD,PROCESS ON . TO 'sandbox'@'%';
                            #
MYSQL_PASSWORD = 'sandbox'

# Number of seconds to wait for EC2 instance to start before accessing it.
AWS_EC2_INSTANCE_START_WAIT = 60

# Number of seconds to wait before trying to connect to MySQL server.
# This is to give time for it to start completely.
AWS_MYSQL_START_WAIT = 60


#==============================================================================
# Changeset Github repository information
#==============================================================================
#
# Github repo commits URL in the following format:
#   https://api.github.com/repos/<owner>/<repo>/commits
#
# Example:
#   https://api.github.com/repos/palominodb/schemanizer/commits
CHANGESET_REPO_URL = None
#
# To create a token, POST to https://api.github.com/authorizations with note
# and scopes values in the data hash,
# for example:
# $ curl -u username -d '{"scopes":["repo"],"note":"Schemanizer repo access token."}' https:/api.github.com/authorizations
AUTHORIZATION_TOKEN = None
# directory to look for changesets (no leading/trailing slash), for example: changesets
CHANGESET_PATH = None
# Github requests that return multiple items will be paginated to
# this number of items (upto maximum of 100)
GITHUB_ITEMS_PER_PAGE = 30
# number of hours ago from 'now'
CHANGESET_CHECK_HOUR_OFFSET = 1


#==============================================================================
# Site information
#==============================================================================
#
# The values found here are automatically used to update site information
# whenever a management command syncdb is executed.
SITE_NAME = 'Schemanizer'
SITE_DOMAIN = '127.0.0.1:8000'


#==============================================================================
# Settings for MySQL server discovery
#==============================================================================
DISCOVER_HOSTS = '192.168.43.0/24'
DISCOVER_PORTS = '3306'


#=============================================================================
# DB settings used by test cases for test data
#=============================================================================
TEST_DB_NAME = 'schemanizer_django_test_db'
TEST_DB_HOST = None
TEST_DB_PORT = None
TEST_DB_USER = 'sandbox'
TEST_DB_PASSWORD = 'sandbox'


#=============================================================================
# django-celery settings
#=============================================================================

# Broker URL in the form:
#   transport://userid:password@hostname:port/virtual_host
# Only the scheme part (transport://) is required, the rest is optional, and
# defaults to the specific transports default values
#
# The following is the broker URL for RabbitMQ
BROKER_URL = 'amqp://sandbox:sandbox@localhost:5672/myhostname'

