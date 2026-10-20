"""Stage a locally built Windows Icarus and its complete runtime dependencies."""
import argparse
import hashlib
import json
import shutil
import sys
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SYSTEM_DLLS=set('kernel32.dll advapi32.dll user32.dll gdi32.dll shell32.dll ole32.dll oleaut32.dll msvcrt.dll ucrtbase.dll ntdll.dll ws2_32.dll shlwapi.dll comdlg32.dll comctl32.dll winmm.dll version.dll bcrypt.dll crypt32.dll secur32.dll rpcrt4.dll imm32.dll setupapi.dll'.split())


def stage(prefix, dependency_bin, license_dir):
    import pefile
    lock=json.loads((ROOT/'vendor/lock.json').read_text())['icarus']
    source=ROOT/'vendor'/lock['source_file']
    if hashlib.sha256(source.read_bytes()).hexdigest()!=lock['source_sha256']:
        raise ValueError('Icarus source checksum mismatch')
    destination=ROOT/'vendor/icarus'
    if destination.exists():
        raise FileExistsError('Use a clean source checkout; vendor/icarus already exists')
    for name in ('bin/iverilog.exe','bin/vvp.exe','lib/ivl/ivl.exe','lib/ivl/ivlpp.exe'):
        if not (prefix/name).is_file():raise FileNotFoundError(name)
    shutil.copytree(str(prefix/'bin'),str(destination/'bin'))
    shutil.copytree(str(prefix/'lib/ivl'),str(destination/'lib/ivl'))
    licenses=destination/'licenses';licenses.mkdir()
    if not license_dir.is_dir():raise FileNotFoundError('Runtime license directory is required')
    shutil.copytree(str(license_dir),str(licenses/'mingw-runtime'))
    with tarfile.open(source) as archive:
        item=next(m for m in archive.getmembers() if m.name.endswith('/COPYING'))
        (licenses/'Icarus-COPYING.txt').write_bytes(archive.extractfile(item).read())
    queue=list(destination.rglob('*'));seen=set();imports={}
    while queue:
        path=queue.pop()
        if not path.is_file() or path in seen:continue
        seen.add(path)
        try:pe=pefile.PE(str(path),fast_load=True)
        except pefile.PEFormatError:continue
        if pe.FILE_HEADER.Machine!=0x8664:raise ValueError('Non-x64 PE: '+path.name)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
        names=[entry.dll.decode('ascii').lower() for entry in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[])]
        pe.close();imports[path.relative_to(destination).as_posix()]=names
        for name in names:
            if name in SYSTEM_DLLS or name.startswith(('api-ms-win-','ext-ms-win-')):continue
            if (destination/'bin'/name).is_file():continue
            candidates=[path.parent/name,dependency_bin/name]
            dll=next((p for p in candidates if p.is_file()),None)
            if dll is None:raise FileNotFoundError('Unresolved PE import '+name+' in '+path.name)
            target=destination/'bin'/name
            shutil.copy2(str(dll),str(target));queue.append(target)
    inventory={p.relative_to(destination).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
               for p in destination.rglob('*') if p.is_file()}
    manifest={'version':lock['version'],'source_sha256':lock['source_sha256'],
              'files':inventory,'imports':imports,'architecture':'AMD64'}
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Staged Windows Icarus:',len(inventory),'files')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prefix',type=Path,required=True)
    p.add_argument('--dependency-bin',type=Path,required=True)
    p.add_argument('--license-dir',type=Path,required=True)
    a=p.parse_args();stage(a.prefix,a.dependency_bin,a.license_dir)
