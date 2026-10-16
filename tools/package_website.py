"""Verify and package the editable local website; Python standard library only."""
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from html.parser import HTMLParser
import hashlib,json,subprocess,sys,zipfile
SITE=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,str(SITE/'tools/verify_website.py')],check=True)
class Catalogue(HTMLParser):
 def __init__(self):super().__init__();self.cards=0;self.targets=[];self.images=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'data-service-card' in a:self.cards+=1
  if tag=='a' and 'service-detail-link' in a.get('class',''):self.targets.append(a.get('href'))
  if tag=='img' and a.get('src','').startswith('https://images.unsplash.com/'):self.images.append(a['src'])
parser=Catalogue();parser.feed((SITE/'index.html').read_text())
expected=['services.html#white-collar','services.html#blue-collar','eor-payroll.html#eor','eor-payroll.html#payroll','emiratisation.html','services.html#hospitality-fm','services.html#overseas-corridors','about.html#governance']
assert parser.cards==8 and parser.targets==expected,'Core service catalogue mismatch'
for image in parser.images:
 q=parse_qs(urlparse(image).query)
 assert all(q.get(k)==[v] for k,v in {'auto':'format','fit':'crop','w':'1000','q':'80'}.items()),'Image parameters incomplete'
files=[p for p in sorted(SITE.rglob('*')) if p.is_file() and p.name not in ('SHA256.json','.DS_Store') and '__pycache__' not in p.parts and not p.is_relative_to(SITE/'tools/qa')]
manifest={p.relative_to(SITE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(SITE/'SHA256.json').write_text(json.dumps(manifest,indent=2))
archive=SITE.parent/'Tory_Workforce_Solutions_Website.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in files+[SITE/'SHA256.json']:z.write(p,Path('tory-website')/p.relative_to(SITE))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'archive':str(archive),'pages':len(list(SITE.glob('*.html'))),'core_services':8,'files':len(files)+1,'bytes':archive.stat().st_size},indent=2))
