#!/usr/bin/env python2

import dns.resolver
import socket
import argparse
import sys

nagios_codes = [ 'OK', 'WARNING', 'CRITICAL', 'UNKNOWN' ]

def exit_now(status=3, message='Something went wrong'):
    print "%s - %s" % (nagios_codes[status], message)
    sys.exit(status)

def socket_is_open(ip, port, timeout, retries):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    
    res = False
    for i in range(retries):
        try:
            s.connect((str(ip), int(port)))
            s.shutdown(socket.SHUT_RDWR)
            res = True
            break;
        finally:
            s.close()
    return res 

def resolve_a_record(query):
    resolv = dns.resolver.Resolver()
    return str(resolv.query(query, "A")[0])

def resolve_srv_record(query):
    try:
        results = []
        resolv = dns.resolver.Resolver()
        srvs = resolv.query(query, "SRV")
        for srv in srvs:
            results.append((srv.target.to_text(omit_final_dot=True), resolve_a_record(srv.target), int(srv.port)))
        return results
    except:
        exit_now(2, 'DNS lookup failed')
        
parser = argparse.ArgumentParser()
parser.add_argument('-Q', '--query', metavar='<query>', help='DNS SRV record to query for', dest='query', default=None)
parser.add_argument('-t', '--timeout', metavar='<timeout>', help='Timeout to try to connect to socket', dest='timeout', default=10)
parser.add_argument('-r', '--retries', metavar='<retries>', help='Number of times to retry connecting to socket', dest='retries', default=3)

args = parser.parse_args()

hosts_up = ''

targets = resolve_srv_record(args.query)
for target in targets:
    result = socket_is_open(target[1], target[2], args.timeout, args.retries)
    if not result:
        exit_now(2, "%s is not reachable" % target[0])
    else:
        hosts_up += target[0] +', '
exit_now(0, "%s are reachable" % hosts_up[:-2])
