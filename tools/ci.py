"""Build all examples, run host tests and verify the published binary baseline."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
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
    subprocess.run([sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=ROOT, check=True)
    (ROOT/'build').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='template-', dir=ROOT/'build') as folder:
        project = Path(folder)/'new-app'
        subprocess.run([sys.executable, str(ROOT/'tools/new_project.py'), str(project), '--name', '我的应用'], check=True)
        build(project)
    report = dict(sdk=version, result='passed', commit=os.environ.get('GITHUB_SHA'),
                  compiler_source_commit='eebf54af545f4ae52f8489a2f6d4d5f93e7942d2',
                  checks=['five clean source builds', 'BJBBK.110 headers and bank checksums',
                          'five exact emulator-baseline binary SHA256 matches',
                          '13 host graphics/rules tests', 'external project template build'],
                  emulator='Prior local original-firmware execution; not rerun by public CI',
                  physical_device='not tested', applications=applications)
    (ROOT/'build/ci-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    return report

if __name__ == '__main__': check()
