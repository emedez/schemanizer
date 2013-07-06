import logging
import socket
import time
import MySQLdb
from django.conf import settings
import nmap
import ipcalc
from utils import exceptions, helpers

log = logging.getLogger(__name__)


def discover_mysql_servers_no_nmap(hosts, ports='3306'):
    """Discover mysql servers.

    hosts format:
        192.168.2.113/24

    ports format:
        3300-3310, 3306
    """

    start_time = time.time()
    log.debug('Server discovery started.')
    port_set = helpers.parse_int_set(ports)

    mysql_servers = []

    for host in ipcalc.Network(hosts):
        hostname = str(host)
        # log.debug('Processing hostname %s', hostname)
        mysql_server_ports = []
        for port in port_set:
            try:
                # log.debug('Checking port %s', port)
                socket_obj = socket.create_connection((hostname, port))
                socket_obj.close()
                # log.debug('Port %s is open.', port)
                connection_options = {
                    'host': hostname,
                    'port': port,
                    'user': settings.MYSQL_USER,
                    'passwd': settings.MYSQL_PASSWORD,
                }
                # log.debug('Attempting MySQL server connection at port %s...', port)
                conn = MySQLdb.connect(**connection_options)
                conn.close()
                # log.debug('Connected to MySQL server at port %s.', port)
                mysql_server_ports.append(port)
            except Exception, e:
                # msg = 'ERROR %s: %s' % (type(e), e)
                # log.exception(msg)
                pass

        if len(mysql_server_ports) == 1:
            mysql_servers.append(dict(
                name=hostname,
                host=hostname,
                hostname=hostname,
                port=mysql_server_ports[0],

            ))
        else:
            for index, port in enumerate(mysql_server_ports):
                mysql_servers.append(dict(
                    name='%s (%s)' % (hostname, index),
                    host=host,
                    hostname=hostname,
                    port=port,
                ))

    log.debug(
        'Server discovery completed, elapsed time = %s.',
        time.time() - start_time)
    return mysql_servers


def discover_mysql_servers(hosts, ports):
    nm = nmap.PortScanner()
    results = nm.scan(hosts, ports)
    if (
            'nmap' in results and
            'scaninfo' in results['nmap'] and
            'error' in results['nmap']['scaninfo']):
        raise exceptions.Error('%s' % (results['nmap']['scaninfo']['error'],))
    mysql_servers = []
    for host in nm.all_hosts():
        hostname = host
        port_scanner_host = nm[host]
        if port_scanner_host['hostname']:
            hostname = port_scanner_host['hostname']
        mysql_server_ports = []
        for tcp_port in port_scanner_host.all_tcp():
            if (
                    port_scanner_host['tcp'][tcp_port]['name'] == 'mysql' and
                    port_scanner_host['tcp'][tcp_port]['state'] == 'open'):
                mysql_server_ports.append(tcp_port)
        if len(mysql_server_ports) == 1:
            mysql_servers.append(dict(
                name=hostname,
                host=host,
                hostname=hostname,
                port=mysql_server_ports[0],

            ))
        else:
            for index, port in enumerate(mysql_server_ports):
                mysql_servers.append(dict(
                    name='%s (%s)' % (hostname, index),
                    host=host,
                    hostname=hostname,
                    port=port,
                ))
    return mysql_servers