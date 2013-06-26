import nmap
from utils import exceptions


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