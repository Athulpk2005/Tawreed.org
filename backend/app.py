"""Tawreed ATS: same-origin Flask API, private SQLite and CV storage.
Run manage.py for first-admin setup. The existing marketing site is served unchanged.
"""
from __future__ import annotations
import base64, hashlib, hmac, io, json, os, re, secrets, sqlite3, subprocess, time, zipfile
from datetime import date, datetime, timezone
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from flask import Flask, g, jsonify, request, send_file, send_from_directory
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

SITE = Path(__file__).resolve().parent.parent
API = '/api/ats/v1'
PH = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
DUMMY_HASH = PH.hash(secrets.token_urlsafe(32))
EMIRATES = ['Abu Dhabi','Dubai','Sharjah','Ajman','Umm Al Quwain','Ras Al Khaimah','Fujairah','Multiple Emirates','Remote / UAE']
SECTORS = ['Corporate & Professional','Technology & Digital','Engineering & Technical','Operations & Project Delivery','Energy & Industrial','Ports & Maritime','Facilities & Hospitality','Other']
TYPES = ['Permanent','Contract','Temporary','On-demand','EOR']
VISA = ['UAE citizen','Golden / Green residence','Family-sponsored residence','Employment residence','Visit / tourist visa','Outside UAE','Other / discuss with recruiter']
STAGES = {'Applied':['Screening','Rejected','Withdrawn'], 'Screening':['Shortlisted','Rejected','Withdrawn'], 'Shortlisted':['Interview','Rejected','Withdrawn'], 'Interview':['Offer','Shortlisted','Rejected','Withdrawn'], 'Offer':['Hired','Interview','Rejected','Withdrawn'], 'Hired':[], 'Rejected':[], 'Withdrawn':[]}
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','recruiter')), active INTEGER NOT NULL DEFAULT 1, must_change INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id), csrf TEXT NOT NULL, created REAL NOT NULL, touched REAL NOT NULL);
CREATE TABLE IF NOT EXISTS attempts(bucket TEXT NOT NULL, ts REAL NOT NULL);
CREATE INDEX IF NOT EXISTS attempt_idx ON attempts(bucket,ts);
CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY, reference TEXT UNIQUE, title TEXT NOT NULL, sector TEXT NOT NULL, emirate TEXT NOT NULL, location TEXT NOT NULL, employment_type TEXT NOT NULL, summary TEXT NOT NULL, description TEXT NOT NULL, responsibilities TEXT NOT NULL, requirements TEXT NOT NULL, benefits TEXT NOT NULL DEFAULT '', salary_min REAL, salary_max REAL, closing_date TEXT NOT NULL, owner_id INTEGER NOT NULL REFERENCES users(id), status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','pending','published','closed')), review_note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL, published_at TEXT, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY, reference TEXT UNIQUE, job_id INTEGER NOT NULL REFERENCES jobs(id), full_name TEXT NOT NULL, email TEXT NOT NULL COLLATE NOCASE, phone TEXT NOT NULL, current_location TEXT NOT NULL, visa_status TEXT NOT NULL, visa_expiry TEXT, current_salary REAL, expected_salary REAL, notice_days INTEGER NOT NULL, experience_years REAL NOT NULL, cover_note TEXT NOT NULL DEFAULT '', consent_at TEXT NOT NULL, privacy_version TEXT NOT NULL, cv_key TEXT NOT NULL, cv_name TEXT NOT NULL, cv_mime TEXT NOT NULL, cv_sha256 TEXT NOT NULL, cv_scan TEXT NOT NULL, stage TEXT NOT NULL DEFAULT 'Applied', created_at TEXT NOT NULL, UNIQUE(job_id,email));
CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY, application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE, actor_id INTEGER REFERENCES users(id), from_stage TEXT, to_stage TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE, actor_id INTEGER NOT NULL REFERENCES users(id), note TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, actor_id INTEGER REFERENCES users(id), action TEXT NOT NULL, target TEXT NOT NULL, details TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);
PRAGMA user_version=1;
'''

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
class Problem(Exception):
    def __init__(self, message, status=400): self.message, self.status = message, status

def create_app(config=None):
    app = Flask(__name__, static_folder=None)
    production = os.environ.get('ATS_ENV','development') == 'production'
    app.config.update(DATA_DIR=os.environ.get('ATS_DATA_DIR',str(SITE.parent/'tawreed-ats-data')), PRODUCTION=production,
        MAX_CONTENT_LENGTH=9*1024*1024, MAX_FORM_MEMORY_SIZE=150000, MAX_FORM_PARTS=35,
        PUBLIC_ORIGIN=os.environ.get('ATS_PUBLIC_ORIGIN',''), SCANNER=os.environ.get('ATS_CLAMSCAN',''), TESTING=False)
    if config: app.config.update(config)
    if os.environ.get('ATS_TRUST_PROXY')=='1':
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
    if app.config['PRODUCTION'] and (not app.config['PUBLIC_ORIGIN'].startswith('https://') or not app.config['SCANNER']):
        raise RuntimeError('Production requires HTTPS ATS_PUBLIC_ORIGIN and ATS_CLAMSCAN executable. Configure the reverse proxy before starting.')
    data = Path(app.config['DATA_DIR']).resolve()
    if data == SITE or SITE in data.parents: raise RuntimeError('ATS_DATA_DIR must be outside the public website directory.')
    data.mkdir(parents=True,exist_ok=True,mode=0o700); (data/'resumes').mkdir(exist_ok=True,mode=0o700)
    os.chmod(data,0o700); os.chmod(data/'resumes',0o700)
    app.config['DB_PATH'] = str(data/'ats.sqlite3')
    def db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DB_PATH'],timeout=15)
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys=ON'); g.db.execute('PRAGMA journal_mode=WAL')
        return g.db
    app.db = db
    with app.app_context():
        db().executescript(SCHEMA); db().commit(); os.chmod(app.config['DB_PATH'],0o600)
    @app.teardown_appcontext
    def close_db(_):
        conn=g.pop('db',None)
        if conn is not None: conn.close()
    def audit(action,target,details=''):
        db().execute('INSERT INTO audit(actor_id,action,target,details,created_at) VALUES(?,?,?,?,?)',(g.user['id'] if g.user else None,action,str(target),details,now()))
    def session_new(uid=None):
        token=secrets.token_urlsafe(48); csrf=secrets.token_urlsafe(32); ts=time.time()
        db().execute('DELETE FROM sessions WHERE touched<? OR created<?',(ts-1800,ts-28800))
        db().execute('INSERT INTO sessions VALUES(?,?,?,?,?)',(digest(token),uid,csrf,ts,ts))
        db().commit(); g.new_cookie=token; g.session=db().execute('SELECT * FROM sessions WHERE token_hash=?',(digest(token),)).fetchone()
        return g.session
    def throttle(bucket,limit,window):
        key=digest(bucket); ts=time.time()
        db().execute('DELETE FROM attempts WHERE ts<?',(ts-86400,))
        count=db().execute('SELECT count(*) FROM attempts WHERE bucket=? AND ts>?',(key,ts-window)).fetchone()[0]
        if count>=limit: raise Problem('Too many attempts. Please try again later.',429)
        db().execute('INSERT INTO attempts VALUES(?,?)',(key,ts)); db().commit()
    def public_user(u): return {k:u[k] for k in ('id','name','email','role','active','must_change')}
    def require(role=None, allow_change=False):
        def deco(fn):
            @wraps(fn)
            def wrapped(*args,**kwargs):
                if not g.user: raise Problem('Please sign in to the recruitment workspace.',401)
                if role and g.user['role']!=role: raise Problem('Administrator access is required.',403)
                if g.user['must_change'] and not allow_change: raise Problem('Change your temporary password before continuing.',403)
                return fn(*args,**kwargs)
            return wrapped
        return deco
    def text(data,key,maximum=200,required=True,minimum=1):
        value=data.get(key,'')
        if not isinstance(value,str): raise Problem(f'{key.replace("_"," ").capitalize()} must be text.')
        value=value.strip()
        if (required and len(value)<minimum) or len(value)>maximum or '\x00' in value:
            raise Problem(f'{key.replace("_"," ").capitalize()} must contain {minimum if required else 0}–{maximum} characters.')
        return value
    def email(data):
        value=text(data,'email',254).lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value): raise Problem('Enter a valid email address.')
        return value
    def password(data,key='password'):
        value=data.get(key,'')
        if not isinstance(value,str) or not 12<=len(value)<=128: raise Problem('Use a password of 12–128 characters.')
        return value
    def number(data,key,minimum=0,maximum=10000000,optional=True,integer=False):
        raw=data.get(key,'')
        if raw in ('',None):
            if optional: return None
            raise Problem(f'{key.replace("_"," ").capitalize()} is required.')
        try: value=float(raw)
        except (TypeError,ValueError): raise Problem(f'{key.replace("_"," ").capitalize()} must be a number.')
        if not minimum<=value<=maximum or (integer and value!=int(value)): raise Problem(f'{key.replace("_"," ").capitalize()} is outside the allowed range.')
        return int(value) if integer else value
    def iso_date(data,key,required=True):
        value=text(data,key,10,required)
        if not value and not required:return None
        try: date.fromisoformat(value)
        except ValueError: raise Problem(f'{key.replace("_"," ").capitalize()} must be a valid date.')
        return value
    def get_json():
        data=request.get_json(silent=True)
        if not isinstance(data,dict):raise Problem('A JSON object is required.')
        return data
    def job_access(jid):
        row=db().execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
        if not row: raise Problem('Vacancy not found.',404)
        if g.user['role']!='admin' and row['owner_id']!=g.user['id']: raise Problem('This vacancy is assigned to another recruiter.',403)
        return row
    def application_access(aid):
        row=db().execute('SELECT a.*,j.owner_id,j.title job_title,j.reference job_reference FROM applications a JOIN jobs j ON j.id=a.job_id WHERE a.id=?',(aid,)).fetchone()
        if not row: raise Problem('Application not found.',404)
        if g.user['role']!='admin' and row['owner_id']!=g.user['id']: raise Problem('This application belongs to another recruiter.',403)
        return row
    @app.before_request
    def prepare():
        g.user=None;g.session=None;g.new_cookie=None;g.clear_cookie=False
        if not request.path.startswith(API): return
        expected=app.config['PUBLIC_ORIGIN'] or request.host_url.rstrip('/')
        if app.config['PRODUCTION'] and request.host!=urlparse(expected).netloc:raise Problem('Unrecognised host.',400)
        if request.method not in ('GET','HEAD','OPTIONS'):
            origin=request.headers.get('Origin')
            if origin and origin.rstrip('/')!=expected.rstrip('/'): raise Problem('Cross-origin requests are not permitted.',403)
        token=request.cookies.get('ats_session','')
        if token:
            s=db().execute('SELECT * FROM sessions WHERE token_hash=?',(digest(token),)).fetchone()
            if s and time.time()-s['touched']<1800 and time.time()-s['created']<28800:
                g.session=s
                if s['user_id']:
                    g.user=db().execute('SELECT * FROM users WHERE id=? AND active=1',(s['user_id'],)).fetchone()
                    if not g.user:g.session=None
                if g.session:db().execute('UPDATE sessions SET touched=? WHERE token_hash=?',(time.time(),s['token_hash']));db().commit()
            else:
                db().execute('DELETE FROM sessions WHERE token_hash=?',(digest(token),));db().commit();g.clear_cookie=True
        if request.method not in ('GET','HEAD','OPTIONS'):
            if not g.session or not hmac.compare_digest(request.headers.get('X-CSRF-Token',''),g.session['csrf']): raise Problem('Your session expired. Refresh the page and try again.',403)
    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options']='nosniff';response.headers['X-Frame-Options']='SAMEORIGIN' if request.path=='/assets/office-map.html' else 'DENY';response.headers['Referrer-Policy']='same-origin'
        if request.path.startswith(API):
            response.headers['Cache-Control']='no-store'
            response.headers['Content-Security-Policy']="default-src 'none'; frame-ancestors 'none'"
        elif request.path in ('/jobs.html','/job-details.html','/recruiter-login.html','/recruiter.html'):
            response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
            response.headers['Cache-Control']='no-store'
        if app.config['PRODUCTION']:response.headers['Strict-Transport-Security']='max-age=31536000'
        if getattr(g,'new_cookie',None):response.set_cookie('ats_session',g.new_cookie,httponly=True,secure=app.config['PRODUCTION'],samesite='Strict',path=API,max_age=28800)
        elif getattr(g,'clear_cookie',False):response.delete_cookie('ats_session',path=API)
        return response
    @app.errorhandler(Problem)
    def problem(e):return jsonify(error=e.message),e.status
    @app.errorhandler(HTTPException)
    def http_error(e):
        if request.path.startswith(API):return jsonify(error='File or request is too large (CV limit: 8 MB).' if e.code==413 else e.description),e.code
        return e
    @app.errorhandler(sqlite3.IntegrityError)
    def conflict(e):
        db().rollback();return jsonify(error='This record already exists or conflicts with another update.'),409
    @app.errorhandler(Exception)
    def unexpected(e):
        db().rollback();app.logger.exception('ATS request failed')
        return jsonify(error='The request could not be completed. Please try again.'),500
    @app.get(API+'/session')
    def session_info():
        if not g.session:
            throttle('session-ip:'+request.remote_addr,120,3600)
            session_new()
        return jsonify(csrf=g.session['csrf'],user=public_user(g.user) if g.user else None)
    @app.post(API+'/login')
    def login():
        data=get_json();identity=text(data,'email',254).lower();pw=data.get('password','')
        throttle('login-ip:'+request.remote_addr,30,900);throttle('login-user:'+identity,8,900)
        u=db().execute('SELECT * FROM users WHERE email=? COLLATE NOCASE AND active=1',(identity,)).fetchone()
        valid=False
        if isinstance(pw,str) and len(pw)<=128:
            try:valid=PH.verify(u['password_hash'] if u else DUMMY_HASH,pw)
            except (VerificationError,InvalidHashError):pass
        if not u or not valid:raise Problem('Email or password is incorrect.',401)
        db().execute('DELETE FROM sessions WHERE token_hash=?',(g.session['token_hash'],));g.user=u
        audit('login',u['id']);session_new(u['id'])
        return jsonify(csrf=g.session['csrf'],user=public_user(u))
    @app.post(API+'/logout')
    def logout():
        db().execute('DELETE FROM sessions WHERE token_hash=?',(g.session['token_hash'],));db().commit();g.clear_cookie=True;return jsonify(ok=True)
    @app.post(API+'/password')
    @require(allow_change=True)
    def change_password():
        data=get_json();new=password(data,'new_password')
        try:PH.verify(g.user['password_hash'],data.get('current_password',''))
        except (VerificationError,InvalidHashError):raise Problem('Current password is incorrect.',400)
        db().execute('UPDATE users SET password_hash=?,must_change=0 WHERE id=?',(PH.hash(new),g.user['id']))
        db().execute('DELETE FROM sessions WHERE user_id=?',(g.user['id'],));audit('password_changed',g.user['id']);session_new(g.user['id'])
        return jsonify(ok=True,csrf=g.session['csrf'])
    @app.get(API+'/options')
    def options():return jsonify(emirates=EMIRATES,sectors=SECTORS,employment_types=TYPES,visa_statuses=VISA,stages=list(STAGES))
    @app.get(API+'/jobs')
    def jobs_public():
        where=['status="published"','closing_date>=?'];args=[date.today().isoformat()]
        for field in ('sector','emirate','employment_type'):
            if request.args.get(field):where.append(field+'=?');args.append(request.args[field])
        q=request.args.get('q','').strip()[:100]
        if q:where.append('(instr(lower(title),lower(?))>0 OR instr(lower(summary),lower(?))>0)');args.extend([q,q])
        try:page=max(1,min(int(request.args.get('page',1)),10000))
        except ValueError:raise Problem('Invalid page number.')
        condition=' AND '.join(where);total=db().execute('SELECT count(*) FROM jobs WHERE '+condition,args).fetchone()[0]
        fields='id,reference,title,sector,emirate,location,employment_type,summary,salary_min,salary_max,closing_date,published_at'
        rows=db().execute('SELECT '+fields+' FROM jobs WHERE '+condition+' ORDER BY published_at DESC,id DESC LIMIT 12 OFFSET ?',args+[(page-1)*12]).fetchall()
        return jsonify(jobs=[dict(x) for x in rows],total=total,page=page,pages=max(1,(total+11)//12))
    @app.get(API+'/jobs/<reference>')
    def job_public(reference):
        row=db().execute('SELECT * FROM jobs WHERE reference=? AND status="published" AND closing_date>=?',(reference,date.today().isoformat())).fetchone()
        if not row:raise Problem('This vacancy is closed or not available.',404)
        result=dict(row)
        for key in ('owner_id','review_note','version'):result.pop(key,None)
        return jsonify(job=result)
    def validate_cv(file):
        if not file or not file.filename:raise Problem('Attach your CV as a PDF or DOCX file.')
        filename=secure_filename(file.filename)[:150];ext=Path(filename).suffix.lower();raw=file.read(8*1024*1024+1)
        if not raw or len(raw)>8*1024*1024:raise Problem('CV must be a non-empty PDF or DOCX, up to 8 MB.')
        if ext=='.pdf':
            if not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-4096:]:raise Problem('The file is not a valid PDF.')
            if re.search(rb'/(JavaScript|JS|Launch|EmbeddedFile|RichMedia)\b',raw,re.I):raise Problem('Use a PDF without scripts, attachments or embedded media.')
            mime='application/pdf'
        elif ext=='.docx':
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    names=z.namelist();total=sum(x.file_size for x in z.infolist())
                    if len(names)>1000 or total>40*1024*1024 or any(x.startswith('/') or '..' in Path(x).parts for x in names):raise ValueError()
                    if not {'[Content_Types].xml','word/document.xml'}.issubset(names):raise ValueError()
                    if any(re.search(r'(vbaProject|embeddings/|activeX/|\.(exe|js|bat|cmd)$)',x,re.I) for x in names):raise ValueError()
                    for name in names:
                        if name.endswith('.rels'):
                            rel=ET.fromstring(z.read(name))
                            if any(x.attrib.get('TargetMode')=='External' and 'hyperlink' not in x.attrib.get('Type','') for x in rel):raise ValueError()
                    ET.fromstring(z.read('word/document.xml'))
            except (zipfile.BadZipFile,ValueError,ET.ParseError,RuntimeError,KeyError):raise Problem('Use a valid DOCX without macros, embedded objects or external templates.')
            mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:raise Problem('Only PDF and DOCX CVs are accepted.')
        key=secrets.token_hex(24)+ext;path=data/'resumes'/key
        with path.open('xb') as out:out.write(raw)
        os.chmod(path,0o600)
        scan='not-scanned-local-development'
        scanner=app.config['SCANNER']
        if scanner:
            try:result=subprocess.run([scanner,'--no-summary',str(path)],capture_output=True,timeout=40)
            except (OSError,subprocess.TimeoutExpired):path.unlink(missing_ok=True);raise Problem('CV scanning is unavailable. Please try again later.',503)
            if result.returncode!=0:
                path.unlink(missing_ok=True)
                raise Problem('CV could not pass the security scan. Please upload a clean file.' if result.returncode==1 else 'CV scanning is unavailable. Please try again later.',422 if result.returncode==1 else 503)
            scan='clamav-passed'
        return key,filename,mime,hashlib.sha256(raw).hexdigest(),scan
    @app.post(API+'/jobs/<reference>/applications')
    def apply(reference):
        throttle('apply-ip:'+request.remote_addr,15,3600)
        f=request.form
        if f.get('website'):raise Problem('Unable to accept this submission.')
        if f.get('consent')!='yes':raise Problem('Consent to process this application is required.')
        candidate_email=email(f);throttle('apply-email:'+candidate_email,6,3600)
        name=text(f,'full_name',150);phone=text(f,'phone',35)
        if not re.fullmatch(r'[+\d ()\-]{7,35}',phone):raise Problem('Enter a valid telephone number including country code.')
        location=text(f,'current_location',180);visa=text(f,'visa_status',80)
        if visa not in VISA:raise Problem('Select a valid visa status.')
        expiry=iso_date(f,'visa_expiry',False);current=number(f,'current_salary');expected=number(f,'expected_salary')
        notice=number(f,'notice_days',0,365,False,True);experience=number(f,'experience_years',0,65,False)
        note=text(f,'cover_note',4000,False)
        j=db().execute('SELECT * FROM jobs WHERE reference=? AND status="published" AND closing_date>=?',(reference,date.today().isoformat())).fetchone()
        if not j:raise Problem('This vacancy no longer accepts applications.',409)
        if db().execute('SELECT id FROM applications WHERE job_id=? AND email=?',(j['id'],candidate_email)).fetchone():raise Problem('An application using this email has already been received for this vacancy.',409)
        key,filename,mime,sha,scan=validate_cv(request.files.get('cv'))
        try:
            db().execute('BEGIN IMMEDIATE')
            if not db().execute('SELECT id FROM jobs WHERE id=? AND status="published" AND closing_date>=?',(j['id'],date.today().isoformat())).fetchone():raise Problem('This vacancy no longer accepts applications.',409)
            cur=db().execute('INSERT INTO applications(job_id,full_name,email,phone,current_location,visa_status,visa_expiry,current_salary,expected_salary,notice_days,experience_years,cover_note,consent_at,privacy_version,cv_key,cv_name,cv_mime,cv_sha256,cv_scan,created_at) VALUES('+','.join('?'*20)+')',(j['id'],name,candidate_email,phone,location,visa,expiry,current,expected,notice,experience,note,now(),'2026-10-16',key,filename,mime,sha,scan,now()))
            aid=cur.lastrowid;ref='TWD-APP-'+secrets.token_hex(5).upper()
            db().execute('UPDATE applications SET reference=? WHERE id=?',(ref,aid));db().execute('INSERT INTO history(application_id,to_stage,note,created_at) VALUES(?,?,?,?)',(aid,'Applied','Candidate submission received.',now()));audit('application_received',ref);db().commit()
        except Exception:
            db().rollback();(data/'resumes'/key).unlink(missing_ok=True);raise
        return jsonify(reference=ref,message='Your application has been received. Please save your reference. Our recruitment team will contact you if your profile is shortlisted.'),201
    @app.get(API+'/staff/jobs')
    @require()
    def staff_jobs():
        cond='' if g.user['role']=='admin' else ' WHERE j.owner_id=?';args=[] if not cond else [g.user['id']]
        rows=db().execute('SELECT j.*,u.name owner_name,(SELECT count(*) FROM applications a WHERE a.job_id=j.id) application_count FROM jobs j JOIN users u ON u.id=j.owner_id'+cond+' ORDER BY j.updated_at DESC',args).fetchall()
        return jsonify(jobs=[dict(x) for x in rows])
    def job_values(d):
        result={k:text(d,k,n) for k,n in [('title',150),('sector',80),('emirate',40),('location',160),('employment_type',30),('summary',700),('description',12000),('responsibilities',10000),('requirements',10000)]}
        for key,choices in [('sector',SECTORS),('emirate',EMIRATES),('employment_type',TYPES)]:
            if result[key] not in choices:raise Problem(f'Select a valid {key.replace("_"," ")}.')
        result['benefits']=text(d,'benefits',6000,False);result['salary_min']=number(d,'salary_min');result['salary_max']=number(d,'salary_max')
        if result['salary_min'] is not None and result['salary_max'] is not None and result['salary_max']<result['salary_min']:raise Problem('Maximum salary must be at least the minimum salary.')
        result['closing_date']=iso_date(d,'closing_date')
        if result['closing_date']<date.today().isoformat():raise Problem('Closing date cannot be in the past.')
        owner=number(d,'owner_id',1,10000000,False,True) if g.user['role']=='admin' and d.get('owner_id') else g.user['id']
        if not db().execute('SELECT id FROM users WHERE id=? AND active=1',(owner,)).fetchone():raise Problem('Assign an active recruiter or administrator.')
        result['owner_id']=owner;return result
    @app.post(API+'/staff/jobs')
    @require()
    def create_job():
        values=job_values(get_json());values.update(created_at=now(),updated_at=now())
        cur=db().execute('INSERT INTO jobs('+','.join(values)+') VALUES('+','.join('?'*len(values))+')',list(values.values()));jid=cur.lastrowid
        ref=f'TWD-{date.today().year}-{jid:05d}';db().execute('UPDATE jobs SET reference=? WHERE id=?',(ref,jid));audit('vacancy_created',ref);db().commit()
        return jsonify(id=jid,reference=ref),201
    @app.put(API+'/staff/jobs/<int:jid>')
    @require()
    def update_job(jid):
        d=get_json();old=job_access(jid);values=job_values(d)
        if d.get('version')!=old['version']:raise Problem('This vacancy changed since you opened it. Refresh before saving.',409)
        # Any content edit removes prior publication approval. Published vacancies must be resubmitted.
        values.update(status='draft',updated_at=now(),review_note='',version=old['version']+1)
        db().execute('UPDATE jobs SET '+','.join(k+'=?' for k in values)+' WHERE id=? AND version=?',list(values.values())+[jid,old['version']])
        if db().execute('SELECT changes()').fetchone()[0]!=1:raise Problem('This vacancy changed. Refresh before saving.',409)
        audit('vacancy_edited_approval_reset',old['reference']);db().commit();return jsonify(ok=True)
    @app.post(API+'/staff/jobs/<int:jid>/transition')
    @require()
    def transition_job(jid):
        d=get_json();j=job_access(jid);action=text(d,'action',30);note=text(d,'note',1500,False)
        rules={'submit':(['draft','closed'],'pending'),'approve':(['pending'],'published'),'return':(['pending'],'draft'),'close':(['draft','pending','published'],'closed')}
        if action not in rules:raise Problem('Invalid vacancy action.')
        before,after=rules[action]
        if action in ('approve','return') and g.user['role']!='admin':raise Problem('Only an administrator can approve or return a vacancy.',403)
        if j['status'] not in before:raise Problem('This vacancy is no longer in the expected state. Refresh the list.',409)
        if action=='return' and not note:raise Problem('Provide a review note for the recruiter.')
        if after in ('published','pending') and j['closing_date']<date.today().isoformat():raise Problem('Update the closing date before submitting or publishing.')
        db().execute('UPDATE jobs SET status=?,review_note=?,updated_at=?,published_at=CASE WHEN ?="published" THEN ? ELSE published_at END,version=version+1 WHERE id=? AND version=?',(after,note,now(),after,now(),jid,j['version']))
        if db().execute('SELECT changes()').fetchone()[0]!=1:raise Problem('Vacancy changed. Refresh and retry.',409)
        audit('vacancy_'+action,j['reference'],note);db().commit();return jsonify(ok=True,status=after)
    @app.get(API+'/staff/applications')
    @require()
    def applications():
        where=['1=1'];args=[]
        if g.user['role']!='admin':where.append('j.owner_id=?');args.append(g.user['id'])
        for key,col in [('job_id','a.job_id'),('stage','a.stage')]:
            if request.args.get(key):where.append(col+'=?');args.append(request.args[key])
        q=request.args.get('q','').strip()[:120]
        if q:where.append('(instr(lower(a.full_name),lower(?))>0 OR instr(lower(a.email),lower(?))>0 OR instr(lower(a.reference),lower(?))>0)');args.extend([q]*3)
        try:page=max(1,min(10000,int(request.args.get('page',1))))
        except ValueError:raise Problem('Invalid page number.')
        base=' FROM applications a JOIN jobs j ON j.id=a.job_id WHERE '+' AND '.join(where)
        total=db().execute('SELECT count(*)'+base,args).fetchone()[0]
        rows=db().execute('SELECT a.id,a.reference,a.full_name,a.email,a.stage,a.visa_status,a.notice_days,a.created_at,j.title job_title,j.reference job_reference'+base+' ORDER BY a.created_at DESC,a.id DESC LIMIT 30 OFFSET ?',args+[(page-1)*30]).fetchall()
        return jsonify(applications=[dict(x) for x in rows],total=total,page=page,pages=max(1,(total+29)//30))
    @app.get(API+'/staff/applications/<int:aid>')
    @require()
    def application(aid):
        row=dict(application_access(aid));row.pop('cv_key');row['allowed_stages']=STAGES[row['stage']]
        history=db().execute('SELECT h.*,u.name actor FROM history h LEFT JOIN users u ON u.id=h.actor_id WHERE application_id=? ORDER BY h.id',(aid,)).fetchall()
        notes=db().execute('SELECT n.*,u.name actor FROM notes n JOIN users u ON u.id=n.actor_id WHERE application_id=? ORDER BY n.id DESC',(aid,)).fetchall()
        return jsonify(application=row,history=[dict(x) for x in history],notes=[dict(x) for x in notes])
    @app.post(API+'/staff/applications/<int:aid>/stage')
    @require()
    def stage(aid):
        row=application_access(aid);d=get_json();target=text(d,'stage',30);note=text(d,'note',3000,False)
        if target not in STAGES[row['stage']]:raise Problem('That pipeline transition is not allowed.',409)
        db().execute('UPDATE applications SET stage=? WHERE id=? AND stage=?',(target,aid,row['stage']))
        if db().execute('SELECT changes()').fetchone()[0]!=1:raise Problem('Application changed. Refresh and retry.',409)
        db().execute('INSERT INTO history(application_id,actor_id,from_stage,to_stage,note,created_at) VALUES(?,?,?,?,?,?)',(aid,g.user['id'],row['stage'],target,note,now()));audit('application_stage',row['reference'],row['stage']+' -> '+target);db().commit();return jsonify(ok=True)
    @app.post(API+'/staff/applications/<int:aid>/notes')
    @require()
    def add_note(aid):
        row=application_access(aid);note=text(get_json(),'note',4000)
        db().execute('INSERT INTO notes(application_id,actor_id,note,created_at) VALUES(?,?,?,?)',(aid,g.user['id'],note,now()));audit('candidate_note_added',row['reference']);db().commit();return jsonify(ok=True),201
    @app.get(API+'/staff/applications/<int:aid>/cv')
    @require()
    def download_cv(aid):
        row=application_access(aid);path=data/'resumes'/row['cv_key']
        if not path.is_file():raise Problem('CV file is unavailable. Contact the administrator.',404)
        audit('cv_downloaded',row['reference']);db().commit()
        response=send_file(path,as_attachment=True,download_name=row['cv_name'],mimetype=row['cv_mime'],conditional=False)
        response.headers['Content-Security-Policy']="sandbox; default-src 'none'";return response
    @app.delete(API+'/staff/applications/<int:aid>')
    @require('admin')
    def delete_application(aid):
        row=application_access(aid);db().execute('DELETE FROM applications WHERE id=?',(aid,));audit('application_deleted',row['reference']);db().commit();(data/'resumes'/row['cv_key']).unlink(missing_ok=True);return jsonify(ok=True)
    @app.get(API+'/staff/users')
    @require('admin')
    def users():return jsonify(users=[public_user(x) for x in db().execute('SELECT * FROM users ORDER BY name')])
    @app.post(API+'/staff/users')
    @require('admin')
    def add_user():
        d=get_json();name=text(d,'name',150);mail=email(d);pw=password(d);role=d.get('role','recruiter')
        if role not in ('admin','recruiter'):raise Problem('Invalid role.')
        cur=db().execute('INSERT INTO users(name,email,password_hash,role,must_change,created_at) VALUES(?,?,?,?,1,?)',(name,mail,PH.hash(pw),role,now()));audit('account_created',cur.lastrowid,role);db().commit();return jsonify(ok=True),201
    @app.patch(API+'/staff/users/<int:uid>')
    @require('admin')
    def update_user(uid):
        d=get_json();db().execute('BEGIN IMMEDIATE');u=db().execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
        if not u:raise Problem('Account not found.',404)
        role=d.get('role',u['role']);active=d.get('active',bool(u['active']))
        if role not in ('admin','recruiter') or not isinstance(active,bool):raise Problem('Invalid account settings.')
        if u['role']=='admin' and u['active'] and (role!='admin' or not active) and db().execute('SELECT count(*) FROM users WHERE active=1 AND role="admin"').fetchone()[0]<=1:raise Problem('At least one active administrator must remain.',409)
        db().execute('UPDATE users SET role=?,active=? WHERE id=?',(role,int(active),uid));db().execute('DELETE FROM sessions WHERE user_id=?',(uid,));audit('account_updated',uid);db().commit();return jsonify(ok=True)
    @app.post(API+'/staff/users/<int:uid>/reset-password')
    @require('admin')
    def reset_user(uid):
        if not db().execute('SELECT id FROM users WHERE id=?',(uid,)).fetchone():raise Problem('Account not found.',404)
        pw=password(get_json());db().execute('UPDATE users SET password_hash=?,must_change=1 WHERE id=?',(PH.hash(pw),uid));db().execute('DELETE FROM sessions WHERE user_id=?',(uid,));audit('password_reset',uid);db().commit();return jsonify(ok=True)
    @app.get(API+'/staff/audit')
    @require('admin')
    def audit_log():return jsonify(events=[dict(x) for x in db().execute('SELECT a.*,u.name actor FROM audit a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC LIMIT 150')])
    @app.get('/api/health')
    def health():return jsonify(status='ok')
    @app.get('/')
    def home():return send_from_directory(SITE,'index.html')
    @app.get('/<path:filename>')
    def static_site(filename):
        parts=Path(filename).parts
        if any(p.startswith('.') or p=='..' for p in parts):raise Problem('Not found.',404)
        if len(parts)==1 and filename.endswith('.html') and (SITE/filename).is_file():return send_from_directory(SITE,filename)
        if filename=='assets/office-map.html':return send_from_directory(SITE,filename)
        if len(parts)>=2 and parts[0] in ('assets','css','js') and Path(filename).suffix.lower() in ('.css','.js','.svg','.png','.jpg','.jpeg','.webp','.ico','.woff2','.woff','.pdf'):
            return send_from_directory(SITE,filename)
        raise Problem('Not found.',404)
    return app
