"""Check containers against the exact emulator-validated 1.1.0 binaries."""
from pathlib import Path
import hashlib
import json
from emulator import parse
ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ['hello', 'diagnostics', 'minesweeper', 'storage', 'music']

def verify():
    baseline = json.loads((ROOT/'validation/relocation.json').read_text(encoding='utf8'))
    expected = {v['file']: v['sha256'] for v in baseline['applications']}
    payloads = {}
    for name in ['report.json', 'io-report.json']:
        report = json.loads((ROOT/'validation'/name).read_text(encoding='utf8'))
        if report['result'] != 'passed': raise ValueError('Emulator baseline is not passed')
        payloads.update({v['name']: v['sha256'] for v in report['installed']})
    result = []
    for example in EXAMPLES:
        project = ROOT/'examples'/example
        spec = json.loads((project/'project.json').read_text(encoding='utf8'))
        filename = spec['name']+'.exe'
        path = project/'build'/filename
        actual_name, payload, flags = parse(path)
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        payload_sha = hashlib.sha256(payload).hexdigest()
        if actual_name != filename or flags != (256 | spec.get('category', 9)):
            raise ValueError('Caption/category mismatch: '+example)
        if len(raw) != 32896 or sha != expected[filename] or payload_sha != payloads[filename]:
            raise ValueError(example+': differs from exact emulator-validated 1.1.0 baseline')
        result.append(dict(example=example, file=filename, sha256=sha, payload_sha256=payload_sha))
    print('Five containers/checksums and emulator-validated binary hashes match')
    return result

if __name__ == '__main__': verify()
