#!/usr/bin/env python3
"""Download pinned public files and verify SHA256. No router changes.
下载固定版本公开文件并校验 SHA256，不修改路由器。
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path('packages'))
    parser.add_argument('--include-source', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'assets-manifest.json').read_text())
    args.directory.mkdir(parents=True, exist_ok=True)
    for asset in manifest['assets']:
        if asset.get('source_only') and not args.include_source:
            continue
        dest = args.directory / asset['filename']
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == asset['sha256']:
            print('Verified / 校验通过:', dest.name)
            continue
        partial = dest.with_name(dest.name + '.part')
        try:
            request = urllib.request.Request(asset['url'], headers={'User-Agent': 'TR3600-guide/1.0'})
            digest = hashlib.sha256()
            with urllib.request.urlopen(request, timeout=120) as response, partial.open('wb') as out:
                while chunk := response.read(1024 * 1024):
                    out.write(chunk)
                    digest.update(chunk)
            if digest.hexdigest() != asset['sha256']:
                raise ValueError('SHA256 mismatch / 校验失败: ' + dest.name)
            partial.replace(dest)
            print('Downloaded and verified / 下载并校验通过:', dest.name)
        finally:
            partial.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
