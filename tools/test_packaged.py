"""Run the real frozen GUI twice with development tools removed from PATH."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import time
import traceback
import faulthandler
try:
    from tools.verify_artifact import inspect_pe
except ModuleNotFoundError:
    from verify_artifact import inspect_pe


def normal_launch(executable, environment, notify=lambda stage: None):
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
    notify('ordinary_gui_spawn_begin')
    child = subprocess.Popen([str(executable)], env=environment, cwd=str(executable.parent), shell=False)
    notify('ordinary_gui_spawned_pid_' + str(child.pid))
    try:
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline and child.poll() is None:
            user.EnumWindows(callback, 0)
            if found:
                break
            time.sleep(.1)
        if not found:
            raise RuntimeError('Ordinary startup produced no visible native window after 90 seconds; child return code ' + str(child.poll()))
        notify('ordinary_gui_window_detected')
        user.PostMessageW(found[0], 0x0010, 0, 0)  # WM_CLOSE, normal application cleanup
        if child.wait(timeout=30) != 0:
            raise RuntimeError('Ordinary startup/close returned an error')
    finally:
        if child.poll() is None:
            child.kill(); child.wait(timeout=10)
    return True


def verify(executable, output):
    """Fail closed, retaining diagnostics if the frozen executable crashes.

    Two isolated frozen launches plus a real normal window are required.
    """
    artifact = inspect_pe(executable, minimum_size=20*1024*1024)
    if sys.platform != 'win32':
        raise RuntimeError('Native Windows required for packaged acceptance')
    import ctypes
    if hasattr(ctypes.WinDLL('ntdll'), 'wine_get_version'):
        raise RuntimeError('Wine is not native Windows acceptance')
    output.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    progress = output / 'acceptance-progress.log'
    def notify(stage):
        line = '[+%.1fs] %s\n' % (time.monotonic() - started, stage)
        print('[packaged acceptance] ' + line.strip(), flush=True)
        with progress.open('a', encoding='utf-8') as stream:
            stream.write(line)
    notify('begin_real_frozen_acceptance')
    diagnostic_stream = (output / 'acceptance-python-stack.log').open('a', encoding='utf-8')
    faulthandler.dump_traceback_later(120, repeat=True, file=diagnostic_stream)
    stage = 'environment'
    report = {'artifact': artifact, 'passed': False, 'stage': stage}
    copied = None
    try:
        environment = os.environ.copy()
        system = Path(environment.get('SystemRoot', r'C:\Windows'))
        environment['PATH'] = str(system/'System32') + os.pathsep + str(system)
        for name in ('PYTHONPATH','PYTHONHOME','QT_PLUGIN_PATH',
                     'QML2_IMPORT_PATH','QT_QPA_PLATFORM','PHOENIXFORGE_DATA'):
            environment.pop(name,None)
        source = Path(executable).resolve()
        folder = output / 'Prueba Fénix'
        folder.mkdir(exist_ok=True)
        copied = folder / source.name
        shutil.copy2(str(source), str(copied))
        temporary = folder / 'Temporal'
        temporary.mkdir(exist_ok=True)
        environment['TEMP'] = environment['TMP'] = str(temporary.resolve())
        environment['PHOENIXFORGE_DATA'] = str((folder / 'user-data').resolve())
        stage = 'ordinary_gui_startup'
        notify(stage)
        before = time.monotonic()
        ordinary = normal_launch(copied.resolve(), environment, notify=notify)
        gui_seconds = round(time.monotonic()-before, 2)
        report['ordinary_gui_seconds'] = gui_seconds
        report['ordinary_startup'] = ordinary
        notify('ordinary_gui_success_%.1fs' % gui_seconds)
        reports=[]
        for n in (1,2):
            stage = 'frozen_hdl_acceptance_' + str(n)
            notify(stage)
            child_dir = output/('launch-%d' % n)
            before = time.monotonic()
            # PyInstaller onefile spawns a second process. stdout=PIPE may stay
            # open in that child after its parent is killed on timeout, hanging
            # communicate() indefinitely on Windows. A real file is bounded.
            console_path = output / ('launch-%d-console.log' % n)
            with console_path.open('wb') as console:
                result = subprocess.run(
                    [str(copied.resolve()), '--self-test', str(child_dir.resolve()),
                     '--require-bundled'],
                    env=environment, cwd=str(output), timeout=180, shell=False,
                    stdout=console, stderr=subprocess.STDOUT)
            notify(stage + '_exit_' + str(result.returncode))
            acceptance = child_dir/'acceptance.json'
            if result.returncode:
                detail = ''
                if acceptance.is_file():
                    data = json.loads(acceptance.read_text(encoding='utf-8'))
                    detail = ' stage=%s error=%s\n%s' % (
                        data.get('failed_stage'),data.get('error'),
                        str(data.get('traceback', ''))[-1800:])
                raise RuntimeError('Packaged self-test #%d failed (exit %d):%s' % (
                    n, result.returncode, detail))
            if not acceptance.is_file():
                raise RuntimeError('Frozen executable returned success without acceptance.json')
            child_report = json.loads(acceptance.read_text(encoding='utf-8'))
            if not all(child_report.get(k) for k in (
                    'success','frozen','bundled_icarus','native_windows')):
                raise RuntimeError('Packaged native acceptance requirements not met: ' + str(child_report))
            child_report['launch_duration_seconds'] = round(time.monotonic()-before, 2)
            reports.append(child_report)
            notify(stage + '_success')
        stage = 'success'
        final = {
            'artifact': artifact,
            'launches': reports,
            'ordinary_startup': ordinary,
            'ordinary_gui_seconds': gui_seconds,
            'development_PATH_removed': True,
            'clean_vm_without_development_tools': False,
        }
        (output/'packaged-acceptance.json').write_text(json.dumps(final,indent=2),encoding='utf-8')
        report.update({'passed':True,'stage':'success'})
        notify('all_acceptance_passed')
        return final
    except Exception as error:
        notify('FAILED_' + stage + '_' + str(error)[:120])
        report['stage'] = stage
        report['error'] = str(error)
        report['traceback'] = traceback.format_exc()
        raise
    finally:
        faulthandler.cancel_dump_traceback_later()
        diagnostic_stream.close()
        if copied is not None and copied.exists():
            copied.unlink()
        (output/'packaged-status.json').write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('executable',type=Path)
    p.add_argument('--output',type=Path,default=Path('build/packaged-acceptance'))
    a=p.parse_args();verify(a.executable,a.output.resolve())
