# Django settings for schemanizerproj project.

import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.' + 'mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'schemanizer_dev',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
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
TIME_ZONE = 'Asia/Manila'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'site_media', 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/site_media/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'site_media', 'static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/site_media/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'yx^0so)b7568fp1_)tod5yv57kkrb9i_nl_#_oxxx%udgbaxkk'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'django.middleware.transaction.TransactionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'schemanizerproj.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'schemanizerproj.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',

    'south',
    'crispy_forms',
    'tastypie',
    'debug_toolbar',
    'djcelery',

    #=============
    # project apps
    #=============
    'schemanizer',

)

#TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'simple': {
            'format': u'[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
        },
        'console': {
            'format': u'[%(asctime)s] %(message)s',
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'simple',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'mode': 'a+',
            'encoding': 'utf-8',
            'delay': True,
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'schemanizerproj': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'schemanizer': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        }
    },
}

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
#
# MySQL connection options for reviewing changesets
#
# If AWS_MYSQL_HOST is None, the EC2 instance host name is used.
# AWS_MYSQL_PORT, AWS_MYSQL_USER and AWS_MYSQL_PASSWORD are also used
# in changeset apply operations.
AWS_MYSQL_HOST = None
AWS_MYSQL_PORT = None
AWS_MYSQL_USER = 'sandbox'
AWS_MYSQL_PASSWORD = 'sandbox'

# Number of seconds to wait for EC2 instance to start before accessing it.
AWS_EC2_INSTANCE_START_WAIT = 60
# When checking the state of an instance, this is the
# number of seconds that should elapse before giving up.
AWS_EC2_INSTANCE_STATE_CHECK_TIMEOUT = 300

# Number of seconds to wait before trying to connect to MySQL server on EC2 instance.
# This is to give time for it to start completely.
AWS_MYSQL_START_WAIT = 60
# When attempting to connect to MySQL server on EC2 instance,
# this is the number of seconds that should elapse before giving up.
AWS_MYSQL_CONNECT_TIMEOUT = 300

# If True will not launch an EC2 instance
DEV_NO_EC2_APPLY_CHANGESET = False


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
CHANGESET_REPO_USER = None
CHANGESET_REPO_PASSWORD = None
# directory to look for changesets, for example: /changesets
CHANGESET_PATH = None


#==============================================================================
# Site information
#==============================================================================
#
# The values found here are automatically used to update site information
# whenever a management command syncdb is executed.
SITE_NAME = 'Schemanizer'
SITE_DOMAIN = '127.0.0.1:8000'

#=============================================================================
# Settings for MySQL server discovery
#=============================================================================
NMAP_HOSTS = '192.168.43.0/24'
NMAP_PORTS = '3306'



#=============================================================================
# DB settings used by test cases for test data
#=============================================================================
TEST_DB_NAME = 'schemanizer_django_test_db'
TEST_DB_HOST = None
TEST_DB_PORT = None
TEST_DB_USER = None
TEST_DB_PASSWORD = None


#=============================================================================
# django-celery settings
#=============================================================================

# Broker URL in the form:
#   transport://userid:password@hostname:port/virtual_host
# Only the scheme part (transport://) is required, the rest is optional, and
# defaults to the specific transports default values
BROKER_URL = 'amqp://sandbox:sandbox@localhost:5672/'


#=============================================================================
# Changeset related settings
#=============================================================================
#
# default user to use for changeset actions as changeset review (reviewed_by)
DEFAULT_CHANGESET_ACTION_USERNAME = u'admin'

# If True, no schemanizer emails will be sent.
DISABLE_SEND_MAIL = False

try:
    from local_settings import *
except ImportError:
    pass


import djcelery
djcelery.setup_loader()