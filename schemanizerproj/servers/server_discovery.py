import logging
import Queue
import pprint
import socket
import threading
import time
import MySQLdb
from django.conf import settings
import ipcalc
from utils import exceptions, helpers

log = logging.getLogger(__name__)


class DiscoverServerThread(threading.Thread):
    def __init__(self, host_queue, port_set, server_queue, *args, **kwargs):
        super(DiscoverServerThread, self).__init__(*args, **kwargs)

        self.host_queue = host_queue
        self.port_set = port_set
        self.server_queue = server_queue
        self.daemon = True

    def run(self):
        try:

            msg = '%s started.' % self.name
            print msg
            log.debug(msg)

            while not self.host_queue.empty():
                try:
                    host = self.host_queue.get(False)
                    try:
                        time.sleep(0)
                        hostname = str(host)

                        msg = '[%s] Processing hostname %s' % (
                            self.name, hostname)
                        print msg
                        log.debug(msg)

                        mysql_server_ports = []
                        for port in self.port_set:
                            try:

                                msg = '[%s] Checking %s:%s...' % (
                                    self.name, hostname, port)
                                print msg
                                log.debug(msg)

                                socket_obj = socket.create_connection(
                                    (hostname, port))
                                socket_obj.close()

                                msg = '[%s] Port %s is open.' % (
                                    self.name, port)
                                print msg
                                log.debug(msg)

                                connection_options = {
                                    'host': hostname,
                                    'port': port,
                                    'user': settings.MYSQL_USER,
                                    'passwd': settings.MYSQL_PASSWORD,
                                }

                                msg = (
                                    '[%s] Attempting MySQL server connection '
                                    'at port %s...' % (self.name, port))
                                print msg
                                log.debug(msg)

                                start_time = time.time()
                                conn = MySQLdb.connect(**connection_options)
                                try:
                                    with conn as cursor:
                                        pass
                                finally:
                                    conn.close()

                                msg = (
                                    '[%s] Connected to MySQL server at %s:%s, '
                                    'elapsed time = %s.' % (
                                        self.name, hostname, port,
                                        time.time() - start_time))
                                print msg
                                log.debug(msg)

                                mysql_server_ports.append(port)
                            except Exception, e:
                                # msg = '[%s] ERROR %s: %s' % (self.name, type(e), e)
                                # log.exception(msg)
                                pass
                            time.sleep(0)

                        if len(mysql_server_ports) == 1:
                            self.server_queue.put(dict(
                                name=hostname,
                                host=hostname,
                                hostname=hostname,
                                port=mysql_server_ports[0],

                            ))
                        else:
                            for index, port in enumerate(mysql_server_ports):
                                self.server_queue.put(dict(
                                    name='%s (%s)' % (hostname, index),
                                    host=host,
                                    hostname=hostname,
                                    port=port,
                                ))
                    finally:
                        self.host_queue.task_done()
                except Queue.Empty:
                    pass
                time.sleep(0)

        except Exception, e:
            msg = '[%s] ERROR %s: %s' % (self.name, type(e), e)
            log.exception(msg)

        finally:
            msg = '%s ended.' % self.name
            print msg
            log.debug(msg)


def discover_mysql_servers(hosts, ports='3306'):
    """Discover mysql servers.

    hosts format:
        192.168.2.113/24

    ports format:
        3300-3310, 3306
    """
    start_time = time.time()

    msg = 'Serer discovery started, start time = %s' % start_time
    print msg
    log.debug(msg)

    port_set = helpers.parse_int_set(ports)
    host_queue = Queue.Queue()
    # max = 3
    # total = 0
    for host in ipcalc.Network(hosts):
        host_queue.put(host)
        # total += 1
        # if total > max:
        #     break
    # host_queue.put('192.168.2.112')
    # host_queue.put('192.168.2.113')

    max_threads = 256
    thread_list = []
    server_queue = Queue.Queue()

    msg = 'Starting threads'
    print msg
    log.debug(msg)

    for i in range(max_threads):
        thread_obj = DiscoverServerThread(
            host_queue, port_set, server_queue, name='thread-%s' % str(i))
        thread_list.append(thread_obj)
        thread_obj.start()

    # block until all hosts are processed
    msg = 'Waiting for all hosts to be processed.'
    print msg
    log.debug(msg)

    host_queue.join()

    msg = 'Threads ended'
    print msg
    log.debug(msg)

    mysql_servers = []
    while not server_queue.empty():
        mysql_server = server_queue.get()
        try:
            msg = 'server = %s' % pprint.pformat(mysql_server)
            print msg
            log.debug(msg)

            mysql_servers.append(mysql_server)
        finally:
            server_queue.task_done()

    log.debug(
        'Server discovery completed, elapsed time = %s.',
        time.time() - start_time)
    print 'elapsed time = %s' % (time.time() - start_time)

    return mysql_servers


# def discover_mysql_servers_no_nmap(hosts, ports='3306'):
#     """Discover mysql servers.
#
#     hosts format:
#         192.168.2.113/24
#
#     ports format:
#         3300-3310, 3306
#     """
#
#     start_time = time.time()
#     log.debug('Server discovery started.')
#     port_set = helpers.parse_int_set(ports)
#
#     mysql_servers = []
#
#     for host in ipcalc.Network(hosts):
#         hostname = str(host)
#         log.debug('Processing hostname %s', hostname)
#         mysql_server_ports = []
#         for port in port_set:
#             try:
#                 log.debug('Checking port %s', port)
#                 socket_obj = socket.create_connection((hostname, port))
#                 socket_obj.close()
#                 log.debug('Port %s is open.', port)
#                 connection_options = {
#                     'host': hostname,
#                     'port': port,
#                     'user': settings.MYSQL_USER,
#                     'passwd': settings.MYSQL_PASSWORD,
#                 }
#                 log.debug('Attempting MySQL server connection at port %s...', port)
#                 conn = MySQLdb.connect(**connection_options)
#                 conn.close()
#                 log.debug('Connected to MySQL server at port %s.', port)
#                 mysql_server_ports.append(port)
#             except Exception, e:
#                 msg = 'ERROR %s: %s' % (type(e), e)
#                 log.exception(msg)
#                 pass
#
#         if len(mysql_server_ports) == 1:
#             mysql_servers.append(dict(
#                 name=hostname,
#                 host=hostname,
#                 hostname=hostname,
#                 port=mysql_server_ports[0],
#
#             ))
#         else:
#             for index, port in enumerate(mysql_server_ports):
#                 mysql_servers.append(dict(
#                     name='%s (%s)' % (hostname, index),
#                     host=host,
#                     hostname=hostname,
#                     port=port,
#                 ))
#
#     log.debug(
#         'Server discovery completed, elapsed time = %s.',
#         time.time() - start_time)
#     return mysql_servers


# def discover_mysql_servers(hosts, ports):
#     nm = nmap.PortScanner()
#     results = nm.scan(hosts, ports)
#     if (
#             'nmap' in results and
#             'scaninfo' in results['nmap'] and
#             'error' in results['nmap']['scaninfo']):
#         raise exceptions.Error('%s' % (results['nmap']['scaninfo']['error'],))
#     mysql_servers = []
#     for host in nm.all_hosts():
#         hostname = host
#         port_scanner_host = nm[host]
#         if port_scanner_host['hostname']:
#             hostname = port_scanner_host['hostname']
#         mysql_server_ports = []
#         for tcp_port in port_scanner_host.all_tcp():
#             if (
#                     port_scanner_host['tcp'][tcp_port]['name'] == 'mysql' and
#                     port_scanner_host['tcp'][tcp_port]['state'] == 'open'):
#                 mysql_server_ports.append(tcp_port)
#         if len(mysql_server_ports) == 1:
#             mysql_servers.append(dict(
#                 name=hostname,
#                 host=host,
#                 hostname=hostname,
#                 port=mysql_server_ports[0],
#
#             ))
#         else:
#             for index, port in enumerate(mysql_server_ports):
#                 mysql_servers.append(dict(
#                     name='%s (%s)' % (hostname, index),
#                     host=host,
#                     hostname=hostname,
#                     port=port,
#                 ))
#     return mysql_servers