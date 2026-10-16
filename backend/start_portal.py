"""Cross-platform local launcher. Run with Python 3.10+. Runtime files stay outside the website."""
import hashlib, os, socket, subprocess, sys, threading, venv, webbrowser
from pathlib import Path

def main():
    if sys.version_info<(3,10):raise SystemExit('Install Python 3.10 or newer from python.org, then run this launcher again.')
    os.umask(0o077);backend=Path(__file__).resolve().parent;site=backend.parent
    runtime=site.parent/'.tawreed-ats-runtime';python=runtime/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if not python.is_file():print('Preparing the private Python environment…');venv.create(runtime,with_pip=True)
    requirements=backend/'requirements.txt';sha=hashlib.sha256(requirements.read_bytes()).hexdigest();stamp=runtime/'requirements.sha256'
    if not stamp.exists() or stamp.read_text()!=sha:
        subprocess.run([str(python),'-m','pip','install','--disable-pip-version-check','-r',str(requirements)],check=True);stamp.write_text(sha)
    port=int(os.environ.get('ATS_PORT','8765'))
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',port))==0:raise SystemExit(f'Port {port} is already in use. Stop the existing local server or set ATS_PORT to another port. No existing process was stopped.')
    env=dict(os.environ)
    # This launcher is intentionally local-only. Production uses wsgi.py behind HTTPS.
    env['ATS_ENV']='development'
    check='from app import create_app; a=create_app(); c=a.app_context(); c.push(); print(a.db().execute("SELECT count(*) FROM users WHERE role=\'admin\' AND active=1").fetchone()[0])'
    count=subprocess.check_output([str(python),'-c',check],cwd=backend,env=env,text=True).strip()
    if count=='0':
        print('\nCreate your first administrator. Password input is hidden. No default account is shipped.\n')
        subprocess.run([str(python),str(backend/'manage.py'),'create-admin'],env=env,check=True)
    print('\nStarting Tawreed locally. Keep this window open; press Ctrl+C to stop.\n')
    timer=threading.Timer(2,lambda:webbrowser.open(f'http://127.0.0.1:{port}/jobs.html'));timer.daemon=True;timer.start()
    try:subprocess.run([str(python),str(backend/'manage.py'),'serve','--port',str(port)],env=env,check=True)
    except KeyboardInterrupt:print('\nLocal recruitment service stopped.')
if __name__=='__main__':
    try:main()
    except subprocess.CalledProcessError:raise SystemExit('Setup did not complete. Check the message above, then run the launcher again.')
