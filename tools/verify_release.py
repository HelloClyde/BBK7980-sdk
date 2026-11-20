"""Verify downloaded release assets and every file inside the SDK archive."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import sys
import zipfile

def verify(folder):
    folder = Path(folder)
    sums = (folder/'SHA256SUMS.txt').read_text(encoding='utf8').splitlines()
    assets = {}
    for line in sums:
        expected, name = line.split('  ', 1)
        if Path(name).name != name: raise ValueError('Invalid asset name')
        data = (folder/name).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected: raise ValueError('Asset SHA256 mismatch: '+name)
        assets[name] = data
    archives = [name for name in assets if name.endswith('-win64.zip')]
    if len(archives) != 1 or set(assets) != {archives[0], 'build-report.json'}:
        raise ValueError('Unexpected release asset list')
    with zipfile.ZipFile(folder/archives[0]) as z:
        if z.testzip(): raise ValueError('ZIP CRC failure')
        members = z.namelist()
        if len(members) != len(set(members)): raise ValueError('Duplicate ZIP members')
        prefix = members[0].split('/')[0]+'/'
        manifest_name = prefix+'SHA256SUMS.txt'
        covered = set()
        for line in z.read(manifest_name).decode('utf8').splitlines():
            expected, name = line.split('  ', 1)
            if '..' in PurePosixPath(name).parts or PurePosixPath(name).is_absolute(): raise ValueError('Invalid archive path')
            if hashlib.sha256(z.read(prefix+name)).hexdigest() != expected: raise ValueError('Inner SHA256 mismatch: '+name)
            covered.add(prefix+name)
        if covered | {manifest_name} != set(members): raise ValueError('Manifest does not cover archive')
        forbidden = {'syscode.bin', 'font.bin', 'installed-nand.bin', 'pclink.exe'}
        if any(PurePosixPath(name).name.lower() in forbidden or name.endswith('.bin.z') for name in members):
            raise ValueError('Forbidden firmware/NAND input in archive')
        baseline = json.loads(z.read(prefix+'validation/relocation.json'))
        for entry in baseline['applications']:
            if hashlib.sha256(z.read(prefix+'bin/'+entry['file'])).hexdigest() != entry['sha256']:
                raise ValueError('Published application differs from validated binary')
        if z.read(prefix+'validation/ci-report.json') != assets['build-report.json']: raise ValueError('Build report mismatch')
    print('Release assets, ZIP CRC, full internal manifest and five application hashes verified')

if __name__ == '__main__': verify(sys.argv[1] if len(sys.argv)>1 else 'dist')
