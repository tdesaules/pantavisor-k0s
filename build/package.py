#!/usr/bin/env python3
"""Export a public component from this repository's Yocto deploy directory."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def package(deploy, output, profile='base'):
    project = json.loads((ROOT / 'build/component.json').read_text())
    variant = project['profiles'][profile]
    version = (ROOT / 'VERSION').read_text().strip()
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('VERSION must be a canonical release number')
    image = project['image'] + '-' + project['machine']
    # Inspect the actual public image tar, not a private rendered filesystem.
    with tarfile.open(deploy / (image + '.tar.gz')) as archive:
        for member in archive:
            name = member.name.removeprefix('./').lstrip('/')
            if member.size and (name.endswith('authorized_keys') or 'host_key' in name
                                or name.startswith('var/lib/k0s/pki/')):
                raise ValueError('Credentials found in public rootfs: ' + name)
    output.mkdir(parents=True, mode=0o755, exist_ok=False)
    for suffix, destination in (('squashfs', 'rootfs.squashfs'), ('tar.gz', 'rootfs.tar.gz'),
                                ('manifest', 'packages.manifest'), ('spdx.tar.zst', 'sbom.spdx.tar.zst')):
        shutil.copyfile(deploy / (image + '.' + suffix), output / destination)
    for source, destination in (('runtime/contract.json', 'runtime.json'), ('runtime/lxc.conf.in', 'lxc.conf.in')):
        shutil.copyfile(ROOT / source, output / destination)
    runtime = json.loads((output / 'runtime.json').read_text())
    metadata = {'schema': 2, 'kind': 'rootfs', 'name': variant['name'], 'version': version,
        'architecture': runtime['architecture'], 'runtimeABI': runtime['id'], 'features': variant['features'],
        'upstream': project['upstream'], 'rootfsSha256': digest(output / 'rootfs.squashfs'),
        'source': {'repository': project['repository'],
                   'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                   'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT))},
        'files': {p.name: {'sha256': digest(p), 'size': p.stat().st_size} for p in sorted(output.iterdir())}}
    (output / 'component.json').write_text(json.dumps(metadata, sort_keys=True, separators=(',', ':')) + '\n')
    print('sha256:' + digest(output / 'component.json'))
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', default='base')
    parser.add_argument('--deploy-dir', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    package(args.deploy_dir or ROOT / 'artifacts/build' / args.profile / 'tmp/deploy/images/userspace-arm64',
            args.output or ROOT / 'dist' / args.profile, args.profile)
