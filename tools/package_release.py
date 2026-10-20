"""Build a clean source ZIP with a per-file SHA-256 inventory, without binaries."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP_FILES = {'README.md', 'CHANGELOG.md', 'VERSION', 'LICENSE', 'THIRD_PARTY_NOTICES.md',
             'INFORME_ENTREGA.md', 'pyproject.toml', '.gitignore', 'install_windows.bat',
             'run_windows.bat', 'build_windows.bat', 'install_linux.sh', 'run.sh'}
TOP_DIRS = {'app', 'docs', 'tests', 'tools', 'requirements', 'examples', 'installer', '.github', 'history'}
IGNORED = {'__pycache__', '.pytest_cache', '.git', 'test-data'}


def selected(path):
    rel = path.relative_to(ROOT)
    if path.is_symlink() or not path.is_file() or any(p in IGNORED for p in rel.parts):
        return False
    if path.suffix in {'.pyc', '.pyo', '.vvp', '.tmp'}:
        return False
    if len(rel.parts) == 1:
        return rel.name in TOP_FILES
    if rel.parts[0] in TOP_DIRS:
        return True
    if rel.parts[0] == 'vendor':
        return len(rel.parts) == 2 or rel.parts[1] in {'sources', 'licenses'}
    if rel.parts[0] == 'build':
        if len(rel.parts) == 2:
            return rel.name in {'PhoenixForge.spec', 'PhoenixForge_legacy.spec', 'windows_version.txt',
                               'v11-tests.xml', 'v11-tests.log', 'v11-tests-before-doc-fix.log',
                               'windows-build-report.json', 'windows-build-attempt.log',
                               'qt-sources.log', 'v11-acceptance.log', 'windows-tests.xml',
                               'msys2-packages.txt', 'python-packages.txt'}
        return rel.parts[1] in {'verification', 'hooks'} and len(rel.parts) == 3
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(ROOT.parent / 'PhoenixForge_v1.1.0_Source.zip'))
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    target = Path(args.output).resolve()
    if target.exists() and not args.overwrite:
        parser.error('Destination exists; choose another name or use --overwrite.')
    for name in TOP_FILES:
        if not (ROOT / name).is_file():
            raise FileNotFoundError('Required release file: ' + name)
    paths = sorted(p for p in ROOT.rglob('*') if p.resolve() != target and selected(p))
    inventory = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    target.parent.mkdir(parents=True, exist_ok=True)
    # Fixed ZIP timestamps make equal source trees reproducible.
    with zipfile.ZipFile(str(target), 'w' if args.overwrite else 'x', zipfile.ZIP_DEFLATED) as archive:
        def write(name, data, executable=False):
            info = zipfile.ZipInfo('PhoenixForge/' + name, (2026, 10, 9, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100755 if executable else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
        for path in paths:
            write(path.relative_to(ROOT).as_posix(), path.read_bytes(), path.suffix == '.sh')
        write('RELEASE_SHA256.json', json.dumps(inventory, indent=2, sort_keys=True).encode('utf-8'))
    with zipfile.ZipFile(str(target)) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('ZIP integrity failure')
    checksum = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(target.suffix + '.sha256').write_text(checksum + '  ' + target.name + '\n', encoding='ascii')
    print(json.dumps({'file': str(target), 'files': len(inventory) + 1,
                      'bytes': target.stat().st_size, 'sha256': checksum}, indent=2))


if __name__ == '__main__':
    main()
