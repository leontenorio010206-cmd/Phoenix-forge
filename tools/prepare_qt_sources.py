"""Build-time download of pinned corresponding sources and unmodified notices."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def prepare(offline=False):
    lock = json.loads((ROOT / 'vendor/qt-sources.json').read_text(encoding='utf-8'))
    for name, entry in lock.items():
        target = ROOT / 'vendor/sources' / name
        if not target.exists():
            if offline:
                raise FileNotFoundError('Missing build input: ' + name)
            partial = target.with_suffix(target.suffix + '.partial')
            with urlopen(entry['url'], timeout=60) as source, partial.open('wb') as stream:
                shutil.copyfileobj(source, stream)
            if hashlib.sha256(partial.read_bytes()).hexdigest() != entry['sha256']:
                partial.unlink()
                raise ValueError('Downloaded source integrity failure: ' + name)
            partial.replace(target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Source integrity failure: ' + name)
        count = 0
        with tarfile.open(target) as archive:
            for member in archive:
                rel = PurePosixPath(member.name)
                if not member.isfile() or rel.is_absolute() or '..' in rel.parts:
                    continue
                if not any(w in member.name.lower() for w in ('license', 'copying', 'copyright', 'notice')):
                    continue
                if member.size > 2*1024*1024:
                    continue
                dest = ROOT / 'vendor/licenses/Qt-upstream' / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(archive.extractfile(member).read())
                count += 1
        if not count:
            raise RuntimeError('No upstream notices found in ' + name)
        print(name + ': verified; %d notices' % count)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--offline', action='store_true')
    prepare(p.parse_args().offline)
