import io, json, sys, tempfile, unittest, zipfile
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app, PH, now, SECTORS, EMIRATES
PASSWORD='Test-only-Password-2026!'
HASH=PH.hash(PASSWORD)
PDF=b'%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\ntrailer << /Root 1 0 R >>\n%%EOF\n'
class ATS(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.app=create_app({'TESTING':True,'DATA_DIR':self.tmp.name,'PRODUCTION':False})
        with self.app.app_context():
            db=self.app.db()
            for i,(name,role) in enumerate([('Admin','admin'),('Recruiter','recruiter'),('Other','recruiter')],1):db.execute('INSERT INTO users(id,name,email,password_hash,role,created_at) VALUES(?,?,?,?,?,?)',(i,name,name.lower()+'@example.test',HASH,role,now()))
            db.commit()
        self.admin,self.ac=self.login('admin');self.rec,self.rc=self.login('recruiter');self.other,self.oc=self.login('other');self.public=self.app.test_client();self.pc=self.public.get('/api/ats/v1/session').json['csrf']
    def tearDown(self):self.tmp.cleanup()
    def login(self,name):
        c=self.app.test_client();csrf=c.get('/api/ats/v1/session').json['csrf'];r=c.post('/api/ats/v1/login',json={'email':name+'@example.test','password':PASSWORD},headers={'X-CSRF-Token':csrf});self.assertEqual(r.status_code,200,r.json);return c,r.json['csrf']
    def call(self,client,csrf,path,method='post',data=None):return getattr(client,method)('/api/ats/v1'+path,json=data or {},headers={'X-CSRF-Token':csrf})
    def payload(self):return dict(title='Technical delivery specialist',sector=SECTORS[2],emirate=EMIRATES[1],location='Dubai, UAE',employment_type='Contract',summary='Technical project delivery with documented site responsibilities.',description='Coordinate the assigned technical delivery scope and review site readiness.',responsibilities='Review requirements.\nCoordinate delivery records.',requirements='Relevant technical experience and effective communication.',benefits='Agreed contractual benefits.',closing_date=(date.today()+timedelta(days=60)).isoformat(),salary_min=5000,salary_max=7000)
    def job(self,publish=True):
        r=self.call(self.rec,self.rc,'/staff/jobs',data=self.payload());self.assertEqual(r.status_code,201,r.json);j=r.json
        if publish:
            self.assertEqual(self.call(self.rec,self.rc,f'/staff/jobs/{j["id"]}/transition',data={'action':'submit'}).status_code,200)
            self.assertEqual(self.call(self.admin,self.ac,f'/staff/jobs/{j["id"]}/transition',data={'action':'approve'}).status_code,200)
        return j
    def apply(self,j,cv=PDF,filename='candidate.pdf',mail='candidate@example.test'):
        fields=dict(full_name='Test Candidate',email=mail,phone='+971 50 000 0000',current_location='Dubai, UAE',visa_status='Employment residence',notice_days='30',experience_years='5',current_salary='5000',expected_salary='6000',consent='yes',cv=(io.BytesIO(cv),filename))
        return self.public.post('/api/ats/v1/jobs/'+j['reference']+'/applications',data=fields,headers={'X-CSRF-Token':self.pc})
    def test_approval_required_and_public_filter(self):
        j=self.job(False);self.assertEqual(self.public.get('/api/ats/v1/jobs').json['total'],0)
        self.assertEqual(self.call(self.rec,self.rc,f'/staff/jobs/{j["id"]}/transition',data={'action':'approve'}).status_code,403)
        self.call(self.rec,self.rc,f'/staff/jobs/{j["id"]}/transition',data={'action':'submit'})
        self.assertEqual(self.public.get('/api/ats/v1/jobs/'+j['reference']).status_code,404)
        self.call(self.admin,self.ac,f'/staff/jobs/{j["id"]}/transition',data={'action':'approve'})
        self.assertEqual(self.public.get('/api/ats/v1/jobs?emirate=Dubai').json['total'],1)
        self.assertEqual(self.public.get('/api/ats/v1/jobs?emirate=Abu+Dhabi').json['total'],0)
    def test_application_cv_and_record_permissions(self):
        j=self.job();r=self.apply(j);self.assertEqual(r.status_code,201,r.json)
        rows=self.rec.get('/api/ats/v1/staff/applications').json['applications'];aid=rows[0]['id']
        self.assertEqual(self.other.get('/api/ats/v1/staff/applications').json['total'],0)
        for suffix in ('','/cv'):
            self.assertEqual(self.public.get(f'/api/ats/v1/staff/applications/{aid}'+suffix).status_code,401)
            self.assertEqual(self.other.get(f'/api/ats/v1/staff/applications/{aid}'+suffix).status_code,403)
        download=self.rec.get(f'/api/ats/v1/staff/applications/{aid}/cv');self.assertEqual(download.data,PDF);self.assertIn('attachment',download.headers['Content-Disposition']);download.close()
        self.assertNotIn('cv_key',self.rec.get(f'/api/ats/v1/staff/applications/{aid}').json['application'])
        self.assertEqual(self.apply(j).status_code,409)
        self.assertEqual(len(list((Path(self.tmp.name)/'resumes').iterdir())),1)
    def test_pipeline_notes_and_audit(self):
        j=self.job();self.apply(j);aid=self.rec.get('/api/ats/v1/staff/applications').json['applications'][0]['id']
        self.assertEqual(self.call(self.rec,self.rc,f'/staff/applications/{aid}/stage',data={'stage':'Hired'}).status_code,409)
        for stage in ['Screening','Shortlisted','Interview','Offer','Hired']:self.assertEqual(self.call(self.rec,self.rc,f'/staff/applications/{aid}/stage',data={'stage':stage,'note':'Reviewed evidence.'}).status_code,200)
        self.assertEqual(self.call(self.rec,self.rc,f'/staff/applications/{aid}/notes',data={'note':'Private test note.'}).status_code,201)
        d=self.rec.get(f'/api/ats/v1/staff/applications/{aid}').json;self.assertEqual(len(d['history']),6);self.assertEqual(len(d['notes']),1);self.assertEqual(d['application']['allowed_stages'],[])
        self.assertTrue(any(e['action']=='application_stage' for e in self.admin.get('/api/ats/v1/staff/audit').json['events']))
    def test_unsafe_uploads_rejected(self):
        j=self.job()
        for raw,name in [(b'MZ executable','cv.pdf'),(PDF,'cv.exe'),(b'%PDF-1.4 /JavaScript (alert) %%EOF','cv.pdf'),(b'junk','cv.docx'),(b'x'*(8*1024*1024+1),'cv.pdf')]:
            self.assertIn(self.apply(j,raw,name).status_code,(400,413))
        self.assertEqual(len(list((Path(self.tmp.name)/'resumes').iterdir())),0)
    def test_docx_validation(self):
        j=self.job();stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:
            z.writestr('[Content_Types].xml','<Types/>');z.writestr('word/document.xml','<document/>')
        self.assertEqual(self.apply(j,stream.getvalue(),'cv.docx').status_code,201)
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:
            z.writestr('[Content_Types].xml','<Types/>');z.writestr('word/document.xml','<document/>');z.writestr('word/vbaProject.bin',b'bad')
        self.assertEqual(self.apply(j,stream.getvalue(),'cv.docx',mail='othercandidate@example.test').status_code,400)
    def test_csrf_origin_and_session_rotation(self):
        self.assertEqual(self.rec.post('/api/ats/v1/staff/jobs',json=self.payload()).status_code,403)
        self.assertEqual(self.rec.post('/api/ats/v1/staff/jobs',json=self.payload(),headers={'X-CSRF-Token':self.rc,'Origin':'https://evil.example'}).status_code,403)
        old=self.rec.get_cookie('ats_session',path='/api/ats/v1').value
        changed=self.call(self.rec,self.rc,'/password',data={'current_password':PASSWORD,'new_password':'Another-test-password-2026!'})
        self.assertEqual(changed.status_code,200);self.assertNotEqual(old,self.rec.get_cookie('ats_session',path='/api/ats/v1').value)
        attacker=self.app.test_client();attacker.set_cookie('ats_session',old,path='/api/ats/v1');self.assertIsNone(attacker.get('/api/ats/v1/session').json['user'])
    def test_roles_accounts_and_last_admin(self):
        self.assertEqual(self.rec.get('/api/ats/v1/staff/users').status_code,403)
        self.assertEqual(self.call(self.rec,self.rc,'/staff/users',data={'name':'Bad','email':'bad@example.test','password':PASSWORD}).status_code,403)
        self.assertEqual(self.call(self.admin,self.ac,'/staff/users/1',method='patch',data={'active':False}).status_code,409)
        self.assertEqual(self.call(self.admin,self.ac,'/staff/users',data={'name':'New','email':'new@example.test','password':PASSWORD,'role':'recruiter'}).status_code,201)
        new,csrf=self.login('new');self.assertEqual(new.get('/api/ats/v1/staff/jobs').status_code,403)
        self.assertEqual(self.call(new,csrf,'/password',data={'current_password':PASSWORD,'new_password':'Fresh-long-password-2026!'}).status_code,200)
        self.assertEqual(new.get('/api/ats/v1/staff/jobs').status_code,200)
        self.call(self.admin,self.ac,'/staff/users/2',method='patch',data={'active':False});self.assertEqual(self.rec.get('/api/ats/v1/staff/jobs').status_code,401)
    def test_edit_reapproval_stale_update_and_close(self):
        j=self.job();current=self.rec.get('/api/ats/v1/staff/jobs').json['jobs'][0];p=self.payload();p['version']=current['version']
        self.assertEqual(self.call(self.rec,self.rc,f'/staff/jobs/{j["id"]}',method='put',data=p).status_code,200)
        self.assertEqual(self.public.get('/api/ats/v1/jobs').json['total'],0)
        self.assertEqual(self.call(self.rec,self.rc,f'/staff/jobs/{j["id"]}',method='put',data=p).status_code,409)
        self.assertEqual(self.call(self.other,self.oc,f'/staff/jobs/{j["id"]}',method='put',data=p).status_code,403)
        self.call(self.rec,self.rc,f'/staff/jobs/{j["id"]}/transition',data={'action':'close'});self.assertEqual(self.apply(j).status_code,409)
    def test_delete_erases_cv_and_cascades(self):
        j=self.job();self.apply(j);aid=self.rec.get('/api/ats/v1/staff/applications').json['applications'][0]['id']
        self.assertEqual(self.call(self.rec,self.rc,f'/staff/applications/{aid}',method='delete').status_code,403)
        self.assertEqual(self.call(self.admin,self.ac,f'/staff/applications/{aid}',method='delete').status_code,200)
        self.assertEqual(list((Path(self.tmp.name)/'resumes').iterdir()),[])
        with self.app.app_context():self.assertEqual(self.app.db().execute('SELECT count(*) FROM history').fetchone()[0],0)
    def test_private_paths_never_served(self):
        for path in ['/backend/app.py','/backend/requirements.txt','/../tawreed-ats-data/ats.sqlite3','/.env','/docs/anything.md']:
            self.assertEqual(self.public.get(path).status_code,404,path)
        with self.public.get('/jobs.html') as response:
            self.assertEqual(response.status_code,200)
            self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
    def test_invalid_job_values(self):
        for key,value in [('closing_date','2020-01-01'),('salary_max',-1),('sector','Bad'),('title',''),('emirate','Bad')]:
            payload=self.payload();payload[key]=value;self.assertEqual(self.call(self.rec,self.rc,'/staff/jobs',data=payload).status_code,400,key)
    def test_data_persists_across_restart(self):
        self.job();second=create_app({'TESTING':True,'DATA_DIR':self.tmp.name,'PRODUCTION':False});self.assertEqual(second.test_client().get('/api/ats/v1/jobs').json['total'],1)
    def test_login_throttling(self):
        c=self.app.test_client();csrf=c.get('/api/ats/v1/session').json['csrf']
        for _ in range(8):self.assertEqual(self.call(c,csrf,'/login',data={'email':'missing@example.test','password':'wrong'}).status_code,401)
        self.assertEqual(self.call(c,csrf,'/login',data={'email':'missing@example.test','password':'wrong'}).status_code,429)
    def test_scanner_fails_closed_and_session_expires(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        j=self.job();self.app.config['SCANNER']='/configured/scanner'
        for code,status in [(1,422),(2,503)]:
            with patch('app.subprocess.run',return_value=SimpleNamespace(returncode=code)):
                self.assertEqual(self.apply(j).status_code,status)
            self.assertEqual(list((Path(self.tmp.name)/'resumes').iterdir()),[])
        with patch('app.subprocess.run',return_value=SimpleNamespace(returncode=0)):
            self.assertEqual(self.apply(j).status_code,201)
        with self.app.app_context():
            self.assertEqual(self.app.db().execute('SELECT cv_scan FROM applications').fetchone()[0],'clamav-passed')
            self.app.db().execute('UPDATE sessions SET touched=0 WHERE user_id=2');self.app.db().commit()
        self.assertEqual(self.rec.get('/api/ats/v1/staff/jobs').status_code,401)
    def test_production_requires_https_and_scanner(self):
        with self.assertRaises(RuntimeError):create_app({'DATA_DIR':self.tmp.name,'PRODUCTION':True,'PUBLIC_ORIGIN':'http://example.test','SCANNER':''})
if __name__=='__main__':unittest.main(verbosity=2)
