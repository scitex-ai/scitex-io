#!/usr/bin/env python3
"""Real Git/Hatch artifact boundary controls. No publication or token exchange."""
from pathlib import Path
import base64
import csv
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('io_release_identity', ROOT/'.github/ci/release-identity.py')
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)


def command(*argv, cwd=None):
    return subprocess.run(argv, cwd=cwd, check=True, capture_output=True, timeout=90).stdout


class RealIOArtifacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owned = tempfile.TemporaryDirectory(prefix='io-artifacts-')
        cls.root = Path(cls.owned.name)
        cls.repo = cls.root/'source'
        cls.repo.mkdir()
        raw = command('git', '-C', str(ROOT), 'archive', 'HEAD')
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            archive.extractall(cls.repo, filter='data')
        cls.version = tomllib.loads((cls.repo/'pyproject.toml').read_text())['project']['version']
        cls.tag = 'v' + cls.version
        major, minor, patch = cls.version.split('.')
        cls.wrong_tag = f'v{major}.{minor}.{int(patch) + 1}'
        # The fixture owns Git object history, not user-specific init hooks.
        command('git', 'init', '--template=', '--initial-branch=main', '--object-format=sha1', '-q', cwd=cls.repo)
        command('git', 'config', 'user.name', 'Release qualification', cwd=cls.repo)
        command('git', 'config', 'user.email', 'qualification@example.invalid', cwd=cls.repo)
        command('git', 'config', 'commit.gpgsign', 'false', cwd=cls.repo)
        command('git', 'add', '-f', '.', cwd=cls.repo)
        command('git', 'commit', '-qm', 'Owned actual IO source fixture', cwd=cls.repo)
        cls.commit = command('git', 'rev-parse', 'HEAD', cwd=cls.repo).decode().strip()
        cls.dist = cls.root/'dist'
        command(sys.executable, '-m', 'build', '--no-isolation', '--outdir', str(cls.dist), str(cls.repo))
        cls.wheel = next(cls.dist.glob('*.whl'))
        cls.sdist = next(cls.dist.glob('*.tar.gz'))
        cls.wheel_raw = cls.wheel.read_bytes()
        cls.sdist_raw = cls.sdist.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.owned.cleanup()

    def owned_dist(self, name):
        result=self.root/name
        result.mkdir()
        shutil.copyfile(self.wheel,result/self.wheel.name)
        shutil.copyfile(self.sdist,result/self.sdist.name)
        return result

    def test_actual_complete_wheel_sdist_matches_real_source(self):
        result=identity.artifact_proof(self.dist,self.tag,self.commit,'123','1',source_root=self.repo)
        self.assertGreater(result['source_membership']['wheel_public_members'],190)

    def test_source_bytes_modified_with_valid_RECORD_are_refused(self):
        with zipfile.ZipFile(io.BytesIO(self.wheel_raw)) as archive:
            files={n:archive.read(n) for n in archive.namelist()}
        files['scitex_io/__init__.py'] += b'\n# owned tamper control\n'
        record=next(n for n in files if n.endswith('.dist-info/RECORD'))
        output=io.StringIO();writer=csv.writer(output,lineterminator='\n')
        for name,body in files.items():
            if name==record: writer.writerow([name,'',''])
            else: writer.writerow([name,'sha256='+base64.urlsafe_b64encode(hashlib.sha256(body).digest()).decode().rstrip('='),str(len(body))])
        files[record]=output.getvalue().encode()
        changed=io.BytesIO()
        with zipfile.ZipFile(changed,'w') as archive:
            for name,body in files.items(): archive.writestr(name,body)
        with self.assertRaisesRegex(ValueError,'source bytes differ'):
            identity.source_payload_identity(changed.getvalue(),self.sdist_raw,self.commit,self.repo)

    def test_extra_sdist_payload_not_in_Git_is_refused(self):
        output=io.BytesIO()
        with tarfile.open(fileobj=io.BytesIO(self.sdist_raw),mode='r:gz') as source, tarfile.open(fileobj=output,mode='w:gz') as target:
            for member in source.getmembers(): target.addfile(member,source.extractfile(member) if member.isfile() else None)
            root=source.getmembers()[0].name.split('/')[0]
            member=tarfile.TarInfo(root+'/unexpected-owned.txt');body=b'owned boundary control';member.size=len(body)
            target.addfile(member,io.BytesIO(body))
        with self.assertRaisesRegex(ValueError,'undeclared public payload'):
            identity.source_payload_identity(self.wheel_raw,output.getvalue(),self.commit,self.repo)

    def test_symlink_artifact_is_refused(self):
        target=self.owned_dist('linked')
        path=target/self.wheel.name;path.unlink();path.symlink_to(self.wheel)
        with self.assertRaisesRegex(ValueError,'regular file'):
            identity.artifact_proof(target,self.tag,self.commit,'123','1',source_root=self.repo)

    def test_wrong_tag_version_is_refused(self):
        with self.assertRaises(ValueError):
            identity.artifact_proof(self.dist,self.wrong_tag,self.commit,'123','1',source_root=self.repo)

    def test_tag_newline_is_refused(self):
        with self.assertRaisesRegex(ValueError,'identity is malformed'):
            identity.artifact_proof(self.dist,self.tag + '\n',self.commit,'123','1',source_root=self.repo)

    def test_extra_distribution_file_is_refused(self):
        target=self.owned_dist('extra')
        (target/'unexpected.txt').write_text('owned control')
        with self.assertRaisesRegex(ValueError,'exactly one wheel'):
            identity.artifact_proof(target,self.tag,self.commit,'123','1',source_root=self.repo)

    def test_source_commit_drift_is_refused(self):
        with (self.repo/'README.md').open('a') as stream:stream.write('\nOwned source drift control.\n')
        command('git','add','README.md',cwd=self.repo)
        command('git','commit','-qm','Owned metadata drift',cwd=self.repo)
        changed=command('git','rev-parse','HEAD',cwd=self.repo).decode().strip()
        with self.assertRaisesRegex(ValueError,'source bytes differ'):
            identity.source_payload_identity(self.wheel_raw,self.sdist_raw,changed,self.repo)

    def source_query(self, *, protected=True, move_after=False, bad_blob=False):
        metadata=command('git','show',self.commit+':pyproject.toml',cwd=self.repo)
        main=command('git','rev-parse','main',cwd=self.repo).decode().strip()
        snapshot={'name':'main','protected':protected,'commit':{'sha':main}}
        count=0
        def query(path,status=200):
            nonlocal count
            prefix='repos/scitex-ai/scitex-io'
            if path==prefix+'/branches/main':
                count+=1
                if move_after and count>1:
                    return {**snapshot,'protected':False}
                return snapshot
            if path==prefix+'/git/ref/tags/'+self.tag:
                return {'ref':'refs/tags/'+self.tag,'object':{'type':'commit','sha':self.commit}}
            if path==prefix+'/compare/'+self.commit+'...'+main:
                return {'base_commit':{'sha':self.commit},'status':'identical' if main==self.commit else 'ahead'}
            if path==prefix+'/contents/pyproject.toml?ref='+self.commit:
                digest=hashlib.sha1(b'blob '+str(len(metadata)).encode()+b'\0'+metadata).hexdigest()
                return {'encoding':'base64','content':base64.b64encode(metadata).decode(),
                        'sha':'0'*40 if bad_blob else digest}
            raise AssertionError('unexpected policy-data request: '+path)
        return query

    def test_real_metadata_resolves_existing_tag_and_qualified_main(self):
        self.assertEqual(identity.resolve(self.tag,self.source_query()),
            {'tag':self.tag,'commit':self.commit,'version':self.version})

    def test_unprotected_main_refuses_before_native_selection(self):
        with self.assertRaisesRegex(ValueError,'main is not protected'):
            identity.resolve(self.tag,self.source_query(protected=False))

    def test_main_protection_change_during_resolution_is_refused(self):
        with self.assertRaisesRegex(ValueError,'main changed'):
            identity.resolve(self.tag,self.source_query(move_after=True))

    def test_forged_metadata_Git_blob_is_refused(self):
        with self.assertRaisesRegex(ValueError,'Git identity differs'):
            identity.resolve(self.tag,self.source_query(bad_blob=True))


if __name__=='__main__':
    unittest.main()
