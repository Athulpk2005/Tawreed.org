"""Local administration. Passwords are prompted, never supplied as command-line arguments."""
import argparse, getpass, os, sqlite3
from pathlib import Path
from app import create_app, PH, now

def main():
    parser=argparse.ArgumentParser(description='Tawreed ATS management')
    parser.add_argument('command',choices=['create-admin','reset-password','serve','backup'])
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--destination',help='New private backup directory outside the website')
    args=parser.parse_args();os.umask(0o077);app=create_app()
    if args.command=='serve':
        if app.config['PRODUCTION']:raise SystemExit('Use gunicorn behind an HTTPS reverse proxy in production. See README_ATS.md.')
        print(f'Local website: http://127.0.0.1:{args.port}/index.html\nRecruitment workspace: http://127.0.0.1:{args.port}/recruiter-login.html')
        app.run(host='127.0.0.1',port=args.port,debug=False);return
    with app.app_context():
        db=app.db()
        if args.command in ('create-admin','reset-password'):
            mail=input('Account email: ').strip().lower()
            import re
            if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',mail):raise SystemExit('A valid email is required.')
            user=db.execute('SELECT * FROM users WHERE email=?',(mail,)).fetchone()
            if args.command=='create-admin' and user:raise SystemExit('Account already exists. Use reset-password.')
            if args.command=='reset-password' and not user:raise SystemExit('Account not found.')
            name=input('Administrator full name: ').strip() if args.command=='create-admin' else None
            if args.command=='create-admin' and not 1<=len(name)<=150:raise SystemExit('Enter a name of 1–150 characters.')
            pw=getpass.getpass('Password (12–128 characters): ')
            if not 12<=len(pw)<=128 or pw!=getpass.getpass('Confirm password: '):raise SystemExit('Passwords must match and contain 12–128 characters.')
            if user:
                db.execute('UPDATE users SET password_hash=?,must_change=1 WHERE id=?',(PH.hash(pw),user['id']));db.execute('DELETE FROM sessions WHERE user_id=?',(user['id'],))
            else:db.execute('INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)',(name,mail,PH.hash(pw),'admin',now()))
            db.execute('INSERT INTO audit(action,target,created_at) VALUES(?,?,?)',(args.command,mail,now()));db.commit();print('Account updated. No password is stored in plain text.')
        elif args.command=='backup':
            if not args.destination:raise SystemExit('--destination is required.')
            import shutil
            dest=Path(args.destination).resolve();site=Path(__file__).resolve().parent.parent
            if dest==site or site in dest.parents or dest.exists():raise SystemExit('Choose a new private directory outside the website.')
            dest.mkdir(parents=True,mode=0o700)
            # Stop the app during backup so the CV snapshot and SQLite backup match.
            target=sqlite3.connect(dest/'ats.sqlite3');db.backup(target);target.close()
            shutil.copytree(Path(app.config['DATA_DIR'])/'resumes',dest/'resumes');print('Backup saved. Protect and encrypt the backup at rest.')
if __name__=='__main__':main()
