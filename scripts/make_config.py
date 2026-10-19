#!/usr/bin/env python3
"""Merge two local Clash YAML subscriptions. URLs stay in private files.
合并两份本地 Clash YAML 订阅；订阅链接仅保存在私人文件中。
Requires / 依赖: PyYAML 6.x
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import yaml


def private_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, 'w') as out:
        out.write(content)


def build(subscriptions, urls, secret):
    names = ['Subscription-1', 'Subscription-2']
    for sub in subscriptions:
        if not isinstance(sub, dict) or not isinstance(sub.get('proxies'), list) or not sub['proxies']:
            raise ValueError('Need nonempty Clash YAML proxies / 需要含节点的 Clash YAML')
    if len(urls) != 2 or any(not u.startswith('https://') for u in urls):
        raise ValueError('Need two HTTPS subscription URLs / 需要两个 HTTPS 订阅链接')
    config = dict(subscriptions[1])
    node_names = {node['name'] for node in config.pop('proxies')}
    old_groups = config.pop('proxy-groups', [])
    reserved = {'代理', '自动选择', '订阅一节点', '订阅二节点'}
    if any(g['name'] in reserved - {'代理'} for g in old_groups):
        raise ValueError('Rename colliding proxy groups first / 请先重命名冲突的策略组')
    config.pop('experimental', None)
    config.update({
        'mixed-port': 7893, 'port': 7890, 'socks-port': 7891,
        'allow-lan': True, 'bind-address': '*', 'mode': 'rule', 'log-level': 'info',
        'ipv6': False, 'external-controller': '0.0.0.0:9090',
        'external-ui': '/usr/share/openclash/ui/metacubexd', 'secret': secret,
        'unified-delay': True, 'tcp-concurrent': True,
        'profile': {'store-selected': True, 'store-fake-ip': False},
    })
    config['proxy-providers'] = {
        name: {'type': 'http', 'url': url, 'path': f'./proxy_provider/subscription-{i}.yaml',
               'interval': 86400, 'override': {'additional-prefix': f'[{name}] '},
               'health-check': {'enable': True, 'url': 'https://www.gstatic.com/generate_204',
                                'interval': 600, 'timeout': 8000, 'lazy': True}}
        for i, (name, url) in enumerate(zip(names, urls), 1)
    }
    groups = [
        {'name': '代理', 'type': 'select', 'proxies': ['自动选择', '订阅一节点', '订阅二节点', 'DIRECT'], 'use': names},
        {'name': '自动选择', 'type': 'url-test', 'use': names, 'url': 'https://www.gstatic.com/generate_204',
         'interval': 600, 'tolerance': 100, 'lazy': True},
        {'name': '订阅一节点', 'type': 'select', 'use': [names[0]]},
        {'name': '订阅二节点', 'type': 'select', 'use': [names[1]]},
    ]
    for original in old_groups:
        if original['name'] == '代理':
            continue
        group = dict(original)
        had_nodes = any(n in node_names for n in group.get('proxies', []))
        group['proxies'] = [n for n in group.get('proxies', []) if n not in node_names]
        if had_nodes:
            group['use'] = list(dict.fromkeys(group.get('use', []) + names))
        groups.append(group)
    config['proxy-groups'] = groups
    if not config.get('rules'):
        config['rules'] = ['GEOIP,CN,DIRECT', 'MATCH,代理']
    filters = []
    for sub in subscriptions:
        filters.extend(sub.get('dns', {}).get('fake-ip-filter', []))
    config['dns'] = {
        'enable': True, 'listen': '0.0.0.0:7874', 'ipv6': False,
        'enhanced-mode': 'fake-ip', 'fake-ip-range': '198.18.0.1/16',
        'fake-ip-filter': list(dict.fromkeys(filters)), 'use-hosts': True,
        'default-nameserver': ['223.5.5.5', '119.29.29.29'],
        'proxy-server-nameserver': ['223.5.5.5', '119.29.29.29'],
        'nameserver': ['https://dns.alidns.com/dns-query', 'https://doh.pub/dns-query'],
    }
    config['tun'] = {'enable': True, 'stack': 'gvisor', 'device': 'utun',
                     'auto-route': False, 'auto-detect-interface': True, 'dns-hijack': ['any:53']}
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--subscription-one', type=Path, required=True)
    parser.add_argument('--subscription-two', type=Path, required=True)
    parser.add_argument('--urls-file', type=Path, required=True, help='JSON array with two HTTPS URLs')
    parser.add_argument('--output-directory', type=Path, default=Path('private/generated'))
    args = parser.parse_args()
    subs = [yaml.safe_load(p.read_text()) for p in (args.subscription_one, args.subscription_two)]
    urls = json.loads(args.urls_file.read_text())
    output = args.output_directory
    secret_file = output / 'controller-private.json'
    secret = json.loads(secret_file.read_text())['secret'] if secret_file.exists() else secrets.token_urlsafe(24)
    config = build(subs, urls, secret)
    private_write(secret_file, json.dumps({'secret': secret}))
    for i, sub in enumerate(subs, 1):
        private_write(output / f'provider-{i}.yaml', yaml.safe_dump({'proxies': sub['proxies']}, allow_unicode=True, sort_keys=False))
    private_write(output / 'Cudy-OpenClash.yaml', yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
    print('Generated private configuration / 已生成私人配置:', output)
    print('Providers / 订阅: 2; rules / 规则:', len(config['rules']))


if __name__ == '__main__':
    main()
