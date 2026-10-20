"""Run the real frozen GUI twice with development tools removed from PATH."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import time
try:
    from tools.verify_artifact import inspect_pe
except ModuleNotFoundError:
    from verify_artifact import inspect_pe


def normal_launch(executable, environment):
    """Observe the ordinary no-argument window through the Windows desktop API."""
    import ctypes
    from ctypes import wintypes as T
    user = ctypes.windll.user32
    kernel = ctypes.windll.kernel32
    callback_type = ctypes.WINFUNCTYPE(T.BOOL, T.HWND, T.LPARAM)
    user.EnumWindows.argtypes = [callback_type, T.LPARAM]
    user.GetWindowThreadProcessId.argtypes = [T.HWND, ctypes.POINTER(T.DWORD)]
    user.IsWindowVisible.argtypes = [T.HWND]
    user.PostMessageW.argtypes = [T.HWND, T.UINT, T.WPARAM, T.LPARAM]
    kernel.OpenProcess.argtypes = [T.DWORD, T.BOOL, T.DWORD]
    kernel.OpenProcess.restype = T.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [T.HANDLE, T.DWORD, T.LPWSTR, ctypes.POINTER(T.DWORD)]
    kernel.CloseHandle.argtypes = [T.HANDLE]
    found = []
    def inspect(hwnd, unused):
        if not user.IsWindowVisible(hwnd):
            return True
        pid = T.DWORD()
        user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = kernel.OpenProcess(0x1000, False, pid.value)
        if handle:
            try:
                size = T.DWORD(32768)
                name = ctypes.create_unicode_buffer(size.value)
                if kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)):
                    if Path(name.value).resolve() == executable.resolve():
                        found.append(hwnd)
            finally:
                kernel.CloseHandle(handle)
        return True
    callback = callback_type(inspect)
    child = subprocess.Popen([str(executable)], env=environment, cwd=str(executable.parent), shell=False)
    try:
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline and child.poll() is None:
            user.EnumWindows(callback, 0)
            if found:
                break
            time.sleep(.1)
        if not found:
            raise RuntimeError('Ordinary startup produced no visible native window')
        user.PostMessageW(found[0], 0x0010, 0, 0)  # WM_CLOSE, normal application cleanup
        if child.wait(timeout=30) != 0:
            raise RuntimeError('Ordinary startup/close returned an error')
    finally:
        if child.poll() is None:
            child.kill(); child.wait(timeout=10)
    return True


def verify(executable, output):
    artifact=inspect_pe(executable,minimum_size=20*1024*1024)
    if sys.platform!='win32':raise RuntimeError('Native Windows required for packaged acceptance')
    import ctypes
    if hasattr(ctypes.WinDLL('ntdll'),'wine_get_version'):
        raise RuntimeError('Wine is not native Windows acceptance')
    output.mkdir(parents=True,exist_ok=True)
    environment=os.environ.copy()
    system=Path(environment.get('SystemRoot',r'C:\Windows'))
    environment['PATH']=str(system/'System32')+os.pathsep+str(system)
    for name in ('PYTHONPATH','PYTHONHOME','QT_PLUGIN_PATH','QML2_IMPORT_PATH','QT_QPA_PLATFORM','PHOENIXFORGE_DATA'):
        environment.pop(name,None)
    # Validate the launch path and onefile extraction path with spaces and Unicode.
    folder = output / 'Prueba Fénix'
    folder.mkdir(exist_ok=True)
    copied = folder / executable.name
    shutil.copy2(str(executable), str(copied))
    temporary = folder / 'Temporal'
    temporary.mkdir(exist_ok=True)
    environment['TEMP'] = environment['TMP'] = str(temporary.resolve())
    environment['PHOENIXFORGE_DATA'] = str((folder / 'user-data').resolve())
    ordinary = normal_launch(copied.resolve(), environment)
    reports=[]
    for n in (1,2):
        folder=output/('launch-%d'%n)
        result=subprocess.run([str(copied.resolve()),'--self-test',str(folder.resolve()),'--require-bundled'],
                              env=environment,cwd=str(output),timeout=180,shell=False)
        if result.returncode:raise RuntimeError('Packaged self-test failed: '+str(result.returncode))
        report=json.loads((folder/'acceptance.json').read_text(encoding='utf-8'))
        if not all(report.get(k) for k in ('success','frozen','bundled_icarus','native_windows')):
            raise RuntimeError('Packaged native acceptance requirements not met')
        reports.append(report)
    copied.unlink()
    final={'artifact':artifact,'launches':reports,'ordinary_startup':ordinary,'development_PATH_removed':True,
           'clean_vm_without_development_tools':False}
    (output/'packaged-acceptance.json').write_text(json.dumps(final,indent=2),encoding='utf-8')
    return final


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('executable',type=Path)
    p.add_argument('--output',type=Path,default=Path('build/packaged-acceptance'))
    a=p.parse_args();verify(a.executable,a.output.resolve())
