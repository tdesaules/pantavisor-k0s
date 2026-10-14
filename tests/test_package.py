import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('component_package', ROOT / 'build/package.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ComponentTests(unittest.TestCase):
    def fixture(self, directory, secret=False):
        project = json.loads((ROOT / 'build/component.json').read_text())
        prefix = project['image'] + '-' + project['machine']
        for suffix in ('squashfs', 'manifest', 'spdx.tar.zst'):
            (directory / (prefix + '.' + suffix)).write_bytes(b'test payload')
        with tarfile.open(directory / (prefix + '.tar.gz'), 'w:gz') as archive:
            member = tarfile.TarInfo('home/root/.ssh/authorized_keys' if secret else 'usr/bin/example')
            member.size = 4
            archive.addfile(member, io.BytesIO(b'test'))

    def test_independent_component_has_provenance_contract_and_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory)
            result = module.package(directory, directory / 'output')
            self.assertEqual(result['schema'], 2)
            self.assertEqual(result['version'], (ROOT / 'VERSION').read_text().strip())
            self.assertEqual(result['architecture'], 'arm64')
            self.assertIn('runtime.json', result['files'])
            self.assertIn('lxc.conf.in', result['files'])
            self.assertEqual(result['rootfsSha256'], result['files']['rootfs.squashfs']['sha256'])
            self.assertNotIn('bsp', result)

    def test_credentials_are_rejected_before_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.fixture(directory, secret=True)
            with self.assertRaisesRegex(ValueError, 'Credentials'):
                module.package(directory, directory / 'output')
            self.assertFalse((directory / 'output').exists())

    def test_service_shell_syntax(self):
        for path in [*(ROOT / 'build').rglob('*'), *(ROOT / 'services').rglob('*')]:
            if path.is_file() and path.read_bytes().startswith(b'#!/bin/sh'):
                subprocess.run(['sh', '-n', str(path)], check=True)

    def test_runtime_contract_is_board_independent(self):
        contract = json.loads((ROOT / 'runtime/contract.json').read_text())
        self.assertTrue(contract['id'].startswith('pantavisor-'))
        self.assertNotIn('ventuno', json.dumps(contract))
        self.assertNotIn('mmcblk', json.dumps(contract))
        self.assertNotIn('nvme', json.dumps(contract))
