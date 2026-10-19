#!/usr/bin/env python3
"""macOS IPv4 UDP STUN probe; optionally verify the Mihomo proxy chain.
macOS IPv4 UDP STUN 验证；可选检查 Mihomo 记录的代理链，不输出节点凭据。
"""
import argparse
import json
from pathlib import Path
import secrets
import socket
import struct
import time
import urllib.request


def valid_response(data, transaction):
    if len(data) < 20:
        return False
    message_type, length, cookie = struct.unpack('!HHI', data[:8])
    return (message_type == 0x0101 and cookie == 0x2112A442
            and data[8:20] == transaction and length % 4 == 0
            and len(data) >= 20 + length)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interface', default='en1')
    parser.add_argument('--address', required=True)
    parser.add_argument('--server', required=True, help='Current IPv4 DNS answer / 当前 IPv4 解析结果')
    parser.add_argument('--port', type=int, default=3478)
    parser.add_argument('--timeout', type=float, default=8)
    parser.add_argument('--controller-secret-file', type=Path)
    parser.add_argument('--controller', default='http://192.168.10.1:9090')
    args = parser.parse_args()
    socket.inet_aton(args.server)
    transaction = secrets.token_bytes(12)
    request = struct.pack('!HHI', 0x0001, 0, 0x2112A442) + transaction
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.IPPROTO_IP, 25, socket.if_nametoindex(args.interface))
        sock.bind((args.address, 0))
        sock.settimeout(args.timeout)
        start = time.monotonic()
        sock.sendto(request, (args.server, args.port))
        data, peer = sock.recvfrom(4096)
        if not valid_response(data, transaction):
            raise ValueError('Invalid STUN response / STUN 响应校验失败')
        result = {'udp_stun': 'PASS', 'source_ip': sock.getsockname()[0],
                  'elapsed_ms': round((time.monotonic() - start) * 1000, 2)}
        if args.controller_secret_file:
            secret = json.loads(args.controller_secret_file.read_text())['secret']
            api_request = urllib.request.Request(args.controller.rstrip('/') + '/connections',
                                                 headers={'Authorization': 'Bearer ' + secret})
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(api_request, timeout=5) as response:
                entries = json.load(response).get('connections', [])
            matching = [entry for entry in entries
                        if entry.get('metadata', {}).get('network', '').lower() == 'udp'
                        and entry.get('metadata', {}).get('sourceIP') == args.address
                        and str(entry.get('metadata', {}).get('sourcePort')) == str(sock.getsockname()[1])]
            result['proxy_chain_observed'] = any(entry.get('chains')
                                                and 'DIRECT' not in entry['chains'] for entry in matching)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
