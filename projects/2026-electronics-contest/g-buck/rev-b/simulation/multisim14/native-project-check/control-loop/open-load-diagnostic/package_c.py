"""Package a matching C native project and separately scoped5ms smoke evidence."""
from pathlib import Path
import json,hashlib,zipfile
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]

def main():
    build=json.loads((HERE/'results/C_build_checks.json').read_text());smoke=json.loads((HERE/'results/C_5ms_smoke.json').read_text())
    native=PROJECT/build['output'];digest=hashlib.sha256(native.read_bytes()).hexdigest()
    assert digest==build['output_sha256']==smoke['project_sha256']
    assert smoke['smoke_completed'] and not smoke['native100ms_stability_verified']
    package=PROJECT/'downloads/Multisim14_空载C版_Ki20对照_2026-10-24.zip'
    names=['C_README.md','GBUCK_CTRL_EQ_KIV20.lib','results/C_build_checks.json','results/C_5ms_smoke.json','results/C_5ms_smoke.log']
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(native,native.name)
        for name in names:z.write(HERE/name,name)
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    checks={'date':'2026-10-24','package':str(package.relative_to(PROJECT)),'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'native_matches_build_and_smoke_record':True,'zip_integrity_verified':True,'native100ms_stability_verified':False}
    (HERE/'results/C_delivery_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n');print(json.dumps(checks,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
