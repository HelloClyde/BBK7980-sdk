"""Build all examples, run host tests and verify the published binary baseline."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest
from build import build
from verify_examples import EXAMPLES, verify
ROOT = Path(__file__).resolve().parents[1]

def check():
    version = json.loads((ROOT/'SDK.json').read_text(encoding='utf8'))['version']
    tag = os.environ.get('GITHUB_REF', '')
    if tag.startswith('refs/tags/') and tag != 'refs/tags/v'+version:
        raise ValueError('Tag must match SDK.json version')
    for example in EXAMPLES: build(ROOT/'examples'/example)
    applications = verify()
    tests = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if not result.wasSuccessful(): raise RuntimeError('Host tests failed')
    (ROOT/'build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='template-', dir=ROOT/'build') as folder:
        project = Path(folder)/'new-app'
        subprocess.run([sys.executable, str(ROOT/'tools/new_project.py'), str(project), '--name', '我的应用'], check=True)
        build(project)
        from PIL import Image
        from emulator import parse
        Image.frombytes('L', (32,24), bytes([255,170,85,0]*192)).save(project/'icon.png')
        spec=json.loads((project/'project.json').read_text(encoding='utf8'))
        spec.update(icon='icon.png',category=4)
        (project/'project.json').write_text(json.dumps(spec,ensure_ascii=False),encoding='utf8')
        build(project)
        _,payload,flags=parse(project/'build/我的应用.exe')
        if flags!=0x104 or payload[0x4010:0x4110]!=b'\x1b'*192+b'\0'*64:
            raise ValueError('PNG icon/category did not reach the application container')
    report = dict(sdk=version, result='passed', commit=os.environ.get('GITHUB_SHA'),
                  compiler_source_commit='eebf54af545f4ae52f8489a2f6d4d5f93e7942d2',
                  checks=['five clean source builds', 'BJBBK.110 headers and bank checksums',
                          'five exact emulator-baseline binary SHA256 matches',
                          f'{result.testsRun} host graphics/rules/icon tests', 'external project template build',
                          'PNG icon and non-default category in built container'],
                  emulator='Prior local original-firmware execution; not rerun by public CI',
                  physical_device='not tested', applications=applications)
    (ROOT/'build/ci-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    return report

if __name__ == '__main__': check()
