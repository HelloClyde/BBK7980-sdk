"""Build a minimal cc65 toolchain from a hash-checked, immutable source archive."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = 'eebf54af545f4ae52f8489a2f6d4d5f93e7942d2'
SOURCE_SHA256 = '6a7880ce125fde77cfa523aedf629c174040bc0827c40cbd20994f6f5d17c32b'
SOURCE_URL = f'https://codeload.github.com/cc65/cc65/zip/{COMMIT}'
TOOLS = ['cl65', 'cc65', 'ca65', 'ld65', 'ar65', 'da65', 'od65']


def install(archive=None):
    work = ROOT / 'build/toolchain-source'
    work.mkdir(parents=True, exist_ok=True)
    archive = Path(archive).resolve() if archive else work / 'cc65-source.zip'
    if not archive.exists():
        print(f'Downloading {SOURCE_URL}', flush=True)
        with urllib.request.urlopen(SOURCE_URL, timeout=120) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
            raise ValueError('cc65 source download SHA256 mismatch')
        archive.write_bytes(data)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError('cc65 source archive SHA256 mismatch')
    compiler = shutil.which('gcc')
    make = shutil.which('mingw32-make') or shutil.which('make')
    if not compiler or not make:
        raise RuntimeError('GCC and GNU make must be on PATH; see docs/BUILD.md')
    with zipfile.ZipFile(archive) as z:
        prefix = f'cc65-{COMMIT}/'
        for name in z.namelist():
            if not name.startswith(prefix) or '..' in Path(name).parts:
                raise ValueError('Unexpected archive member')
        z.extractall(work)
    source = work / f'cc65-{COMMIT}'
    suffix = '.exe' if os.name == 'nt' else ''
    options = ['BUILD_ID=Git eebf54a']
    if os.name == 'nt':
        options += ['EXE_SUFFIX=.exe', 'SHELL=cmd.exe']
    subprocess.run([make, '-C', str(source / 'src'), '-j2', *options, *TOOLS], check=True)
    (source / 'lib').mkdir(exist_ok=True)
    subprocess.run([make, '-C', str(source / 'libsrc'), '-j2', *options, 'none'], check=True)
    target = ROOT / 'toolchain/cc65'
    (target / 'bin').mkdir(parents=True, exist_ok=True)
    for name in TOOLS:
        shutil.copy2(source / 'bin' / (name + suffix), target / 'bin' / (name + suffix))
    for name in ['include', 'asminc']:
        shutil.copytree(source / name, target / name, dirs_exist_ok=True)
    for name in ['cfg/none.cfg', 'lib/none.lib']:
        dest = target / name
        dest.parent.mkdir(exist_ok=True)
        shutil.copy2(source / name, dest)
    shutil.copy2(source / 'LICENSE', target / 'LICENSE.txt')
    (target / 'provenance.json').write_text(json.dumps(dict(
        commit=COMMIT, source_url=SOURCE_URL, source_sha256=SOURCE_SHA256,
        license='LICENSE.txt', build_id='Git eebf54a'), indent=2) + '\n', encoding='utf8')
    subprocess.run([str(target / 'bin' / ('cl65' + suffix)), '--version'], check=True)
    print(target)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, help='Use a local copy of the pinned source ZIP')
    args = parser.parse_args()
    install(args.archive)
