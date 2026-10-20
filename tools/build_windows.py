"""Build and test actual Windows artifacts. Never substitutes another platform."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.verify_artifact import inspect_pe, verify_vendor
from tools.collect_licenses import collect
from tools.test_packaged import verify
from tools.prepare_qt_sources import prepare


def invoke(args, env=None):
    subprocess.run([str(x) for x in args], cwd=str(ROOT), env=env, check=True, shell=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--makensis', help='NSIS 3.11 makensis.exe path; auto-detected if omitted')
    parser.add_argument('--portable-only', action='store_true')
    parser.add_argument('--experimental-preview', action='store_true',
                        help='Build an explicitly unverified preview; do not run release acceptance')
    args = parser.parse_args()
    report = {'version': '1.4.0', 'utc': datetime.now(timezone.utc).isoformat(),
              'host': platform.platform(), 'python': platform.python_version(),
              'success': False, 'artifacts': [], 'clean_vm_verified': False,
              'installer_installation_verified': False, 'release_acceptance_complete': False,
              'validation_status': 'experimental_unverified' if args.experimental_preview else 'pending'}
    try:
        if sys.platform != 'win32':
            raise RuntimeError('BLOCKED: build requires native Windows x64; this host is ' + sys.platform)
        import ctypes
        if hasattr(ctypes.WinDLL('ntdll'), 'wine_get_version'):
            raise RuntimeError('BLOCKED: Wine cannot satisfy native Windows acceptance')
        if struct.calcsize('P') != 8 or sys.version_info[:3] != (3, 11, 9):
            raise RuntimeError('Use the fixed Python 3.11.9 x64 build interpreter')
        verify_vendor(ROOT / 'vendor/icarus')
        prepare(offline=True)
        collect(ROOT)
        environment = os.environ.copy()
        environment['PHOENIXFORGE_QT'] = 'pyside6'
        environment['QT_QPA_PLATFORM'] = 'windows'
        if not args.experimental_preview:
            invoke([sys.executable, '-m', 'pytest', '-q', '-m', 'not packaged',
                    '--junitxml=build/windows-tests.xml'], environment)
            result = ET.parse(str(ROOT / 'build/windows-tests.xml'))
            suites = list(result.iter('testsuite'))
            report['tests'] = {k: sum(int(s.get(k, 0)) for s in suites)
                               for k in ('tests', 'failures', 'errors', 'skipped')}
            if any(t.get('classname', '').endswith(('test_simulation', 'test_gui')) and t.find('skipped') is not None
                   for t in result.iter('testcase')):
                raise RuntimeError('An HDL test was skipped; bundled simulator is mandatory')
        portable = ROOT / 'dist/PhoenixForge_v1.4.0_Portable.exe'
        # Reuse a PE left by strict acceptance only for an explicitly UNVERIFIED preview.
        if not args.experimental_preview or not portable.is_file():
            invoke([sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm',
                    '--distpath', 'dist', '--workpath', 'build/work-modern', 'build/PhoenixForge.spec'], environment)
        artifact = inspect_pe(portable, minimum_size=20*1024*1024)
        if args.experimental_preview:
            preview = ROOT / 'dist/PhoenixForge_v1.4.0_Portable_EXPERIMENTAL.exe'
            shutil.copy2(portable, preview)
            portable.unlink(missing_ok=True)  # Never publish an unverified file under a stable name.
            report['artifacts'].append(inspect_pe(preview, minimum_size=20*1024*1024))
            report['warning'] = ('PREVIEW SIN VERIFICAR: pruebas de integración y aceptación '
                                 'de Windows omitidas deliberadamente; simulación HDL puede fallar')
            report['validation_status'] = 'experimental_unverified'
            report['success'] = True
            return 0
        report['artifacts'].append(artifact)
        acceptance = verify(portable, ROOT / 'build/packaged-acceptance')
        report['native_acceptance'] = acceptance
        report['validation_status'] = 'ci_accepted_windows_server_2022'
        if not args.portable_only:
            nsis = args.makensis or shutil.which('makensis')
            if not nsis:
                guess = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'NSIS/makensis.exe'
                nsis = str(guess) if guess.is_file() else None
            if not nsis:
                raise FileNotFoundError('Install NSIS 3.11 on the build machine, or specify --makensis')
            invoke([nsis, '/INPUTCHARSET', 'UTF8', '/DPF_ROOT=' + str(ROOT), ROOT / 'installer/PhoenixForge.nsi'])
            report['artifacts'].append(inspect_pe(ROOT / 'dist/PhoenixForge_v1.4.0_Setup.exe',
                                                 minimum_size=20*1024*1024, machine=None))
        report['success'] = True
    except Exception as error:
        report['error'] = str(error)
        print(str(error), file=sys.stderr)
    finally:
        (ROOT / 'build').mkdir(exist_ok=True)
        (ROOT / 'build/windows-build-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        if report['success']:
            (ROOT / 'dist/SHA256SUMS.txt').write_text(''.join(
                a['sha256'] + '  ' + a['name'] + '\n' for a in report['artifacts']), encoding='ascii')
    return 0 if report['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
