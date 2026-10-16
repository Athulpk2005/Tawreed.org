"""Build a distributable ZIP without database, CV, credential or runtime files."""
from pathlib import Path
import hashlib,json,zipfile
from datetime import datetime,timezone
SITE=Path(__file__).resolve().parent.parent
EXCLUDED_DIRS={'__pycache__','.git','.venv','venv','node_modules','var','resumes','uploads','qa','.tawreed-ats-runtime','tawreed-ats-data'}
EXCLUDED_SUFFIXES=('.pyc','.pyo','.sqlite','.sqlite3','.db','.sqlite-wal','.sqlite-shm','.sqlite3-wal','.sqlite3-shm','.log','.pem','.key','.pfx','.p12','.zip')
def allowed(p):
    parts=p.relative_to(SITE).parts
    return not any(x in EXCLUDED_DIRS or x.startswith('.') for x in parts) and not p.name.lower().endswith(EXCLUDED_SUFFIXES) and p.name not in ('SHA256.json','credentials.json','secrets.json') and not p.name.lower().startswith(('.env','secrets.'))
def package(destination=None):
    files=sorted(p for p in SITE.rglob('*') if p.is_file() and allowed(p))
    manifest={p.relative_to(SITE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (SITE/'SHA256.json').write_text(json.dumps({'built_utc':datetime.now(timezone.utc).isoformat(),'files':manifest},indent=2)+'\n')
    dest=Path(destination) if destination else SITE.parent/'Tory_Workforce_Solutions_Website.zip'
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files+[SITE/'SHA256.json']:z.write(p,SITE.name+'/'+p.relative_to(SITE).as_posix())
    with zipfile.ZipFile(dest) as z:
        assert z.testzip() is None
        for name,sha in manifest.items():assert hashlib.sha256(z.read(SITE.name+'/'+name)).hexdigest()==sha,name
    print(json.dumps({'archive':str(dest),'files':len(files)+1,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'manifest_verified':True},indent=2))
    return dest
if __name__=='__main__':package()
