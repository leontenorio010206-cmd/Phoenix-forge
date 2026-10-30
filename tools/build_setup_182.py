"""Build 1.8.2 Preview Setup only after accepted native Windows executable."""
from pathlib import Path
import json, subprocess, sys
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.build_setup_windows import find_nsis
from tools.release_gate import verify_release
from tools.verify_artifact import inspect_pe
VERSION = "1.8.2"
SHA = "aadcf3ff1b7cc8720509fde6c57ca84249f3beb45ddd14fd492c608241a12bb8"

def verify_manifest(root):
    data = json.loads((Path(root)/"installer/osscad-181.json").read_text(encoding="utf-8"))
    url = urlparse(data.get("url",""))
    if (data.get("schema_version") != 1 or data.get("component") != "osscad" or
        data.get("version") != "2026-10-27" or data.get("sha256") != SHA or
        data.get("bytes") != 603362463 or url.scheme != "https" or
        url.netloc != "github.com" or not url.path.startswith(
            "/YosysHQ/oss-cad-suite-build/releases/download/2026-10-27/") or
        data.get("expected") != "oss-cad-suite/bin/yosys.exe"):
        raise ValueError("OSS CAD manifest mismatch")
    return data

def build_setup(root=ROOT, nsis=None, runner=subprocess.run):
    root = Path(root).resolve()
    spec = verify_manifest(root)
    validated = verify_release(root/"build/windows-build-report.json",root/"dist",VERSION)
    tool = nsis or find_nsis()
    if not tool: raise FileNotFoundError("NSIS makensis.exe missing")
    runner([str(tool),"/INPUTCHARSET","UTF8","/DPF_ROOT="+str(root),
            str(root/"installer/PhoenixForge_182.nsi")],cwd=str(root),check=True)
    out = root/"dist/PhoenixForge_v1.8.2_Setup.exe"
    info = inspect_pe(out,minimum_size=20*1024*1024,machine=None)
    checkfile = out.parent/"SHA256SUMS.txt"
    prev = checkfile.read_text(encoding="ascii") if checkfile.is_file() else ""
    if out.name in prev: raise ValueError("Duplicate setup checksum")
    with checkfile.open("a",encoding="ascii") as stream:
        if prev and not prev.endswith("\n"): stream.write("\n")
        stream.write(info["sha256"]+"  "+info["name"]+"\n")
    report = {"version":VERSION,"preview":True,"accepted_portable":validated,
        "setup":info,"osscad_sha256":spec["sha256"],
        "osscad_installer_tested_on_user_pc":False,
        "cyclone_iv_bitgen_ready":False}
    (root/"build/setup-182-report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report

if __name__ == "__main__":
    print(json.dumps(build_setup(),indent=2))
