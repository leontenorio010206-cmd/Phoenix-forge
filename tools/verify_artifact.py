"""Reject missing, truncated, wrong-platform, or unexpectedly modified artifacts."""
import hashlib
import struct
from pathlib import Path


def inspect_pe(path, minimum_size=1024*1024, machine=0x8664, gui=True):
    path=Path(path)
    if not path.is_file():raise FileNotFoundError(path)
    data=path.read_bytes()
    if len(data)<minimum_size or data[:2]!=b'MZ':raise ValueError('Missing/truncated Windows PE')
    offset=struct.unpack_from('<I',data,0x3c)[0]
    if offset+96>len(data) or data[offset:offset+4]!=b'PE\0\0':raise ValueError('Invalid PE signature')
    actual_machine=struct.unpack_from('<H',data,offset+4)[0]
    if machine is not None and actual_machine!=machine:raise ValueError('Wrong executable architecture')
    subsystem=struct.unpack_from('<H',data,offset+24+68)[0]
    if gui and subsystem!=2:raise ValueError('A GUI executable is required')
    return {'name':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'machine':hex(actual_machine),'subsystem':subsystem}


def verify_vendor(root):
    import json
    root=Path(root);manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    if manifest['architecture']!='AMD64':raise ValueError('Icarus must be x64')
    for name,expected in manifest['files'].items():
        p=(root/name).resolve();p.relative_to(root.resolve())
        if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError('Vendor integrity: '+name)
    for name in ('bin/iverilog.exe','bin/vvp.exe','lib/ivl/ivl.exe','lib/ivl/ivlpp.exe'):
        inspect_pe(root/name,minimum_size=4096,gui=False)
    return manifest
