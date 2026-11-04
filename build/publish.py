"""Publish a clean, build-bound component as a versioned ORAS artifact."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def publish(directory, registry):
    directory = directory.resolve()
    metadata = json.loads((directory / 'component.json').read_text())
    if metadata['source']['dirty']: raise ValueError('Release requires a clean source build')
    if not re.fullmatch(r'ghcr\.io/[a-z0-9._/-]+', registry): raise ValueError('Expected a GHCR repository without tag')
    version = metadata['version']
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version): raise ValueError('Invalid release version')
    expected = set(metadata['files']) | {'component.json'}
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file() or p.is_symlink()}
    if actual != expected or any(p.is_symlink() for p in directory.rglob('*')): raise ValueError('Invalid export inventory')
    for name, item in metadata['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts: raise ValueError('Unsafe path')
        with (directory / name).open('rb') as stream: checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
        if checksum != item['sha256'] or (directory / name).stat().st_size != item['size']: raise ValueError('Export changed: ' + name)
    if 'build-provenance.json' not in expected: raise ValueError('Build provenance required')
    built = json.loads((directory / 'build-provenance.json').read_text())
    if built['source']['dirty'] or any(metadata['source'].get(key) != value for key, value in built['source'].items()):
        raise ValueError('Build provenance identity mismatch')
    reference = registry + ':' + version
    subprocess.run(['oras', 'push', '--artifact-type', 'application/vnd.pantavisor.component.v2', reference, *sorted(expected)], cwd=directory, check=True)
    digest = subprocess.check_output(['oras', 'resolve', reference], text=True).strip()
    print(registry + '@' + digest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('registry')
    args = parser.parse_args()
    publish(args.directory, args.registry)
