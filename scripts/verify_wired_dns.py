#!/usr/bin/env python3
"""macOS-only DNS test explicitly bound to Ethernet. / macOS 有线 DNS 验证。"""
import argparse
import secrets
import socket
import struct

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--interface', default='en0')
parser.add_argument('--address', required=True)
parser.add_argument('--router', default='192.168.10.1')
args = parser.parse_args()
for domain in ('www.baidu.com', 'pagead2.googlesyndication.com'):
    ident = secrets.randbelow(65536)
    question = b''.join(bytes([len(p)]) + p.encode() for p in domain.split('.')) + b'\0' + struct.pack('!HH', 1, 1)
    query = struct.pack('!HHHHHH', ident, 0x0100, 1, 0, 0, 0) + question
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.IPPROTO_IP, 25, socket.if_nametoindex(args.interface))  # Darwin IP_BOUND_IF
        sock.bind((args.address, 0))
        sock.settimeout(5)
        sock.sendto(query, (args.router, 53))
        data, peer = sock.recvfrom(4096)
        rid, flags, qd, answers, ns, ar = struct.unpack('!HHHHHH', data[:12])
        assert rid == ident and flags & 0x8000
        print(f'{domain}: source={sock.getsockname()[0]} DNS={peer[0]} rcode={flags & 15} answers={answers}')
