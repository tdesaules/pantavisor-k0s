"""Bind successful builds to source content and exact deploy payloads."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def snapshot(root):
    names = subprocess.check_output(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=root).decode().split('\0')
    files = {name: digest(root / name) if (root / name).is_file() else None for name in sorted(set(names)) if name}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def read(deploy, root):
    record = json.loads((deploy / 'build-provenance.json').read_text())
    if record['schema'] != 1 or record['source']['treeSha256'] != snapshot(root):
        raise ValueError('Sources changed since build; rebuild before packaging')
    for name, checksum in record['files'].items():
        if Path(name).name != name or digest(deploy / name) != checksum:
            raise ValueError('Build payload changed: ' + name)
    return record


def run(root, deploy, names, command):
    deploy.mkdir(parents=True, exist_ok=True)
    record_path = deploy / 'build-provenance.json'
    record_path.unlink(missing_ok=True)
    source = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
              'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=root)),
              'treeSha256': snapshot(root),
              'epoch': int(subprocess.check_output(['git', 'show', '-s', '--format=%ct', 'HEAD'], cwd=root))}
    started = time.time()
    subprocess.run(command, cwd=root, check=True)
    if snapshot(root) != source['treeSha256']:
        raise ValueError('Sources changed during build')
    record = {'schema': 1, 'source': source, 'durationSeconds': round(time.time() - started, 3),
              'files': {name: digest(deploy / name) for name in names}}
    record_path.write_text(json.dumps(record, sort_keys=True) + '\n')


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    deploy, prefix, *command = sys.argv[1:]
    names = [prefix + '.' + suffix for suffix in ('squashfs', 'tar.gz', 'manifest', 'spdx.tar.zst')]
    run(root, Path(deploy), names, command)
