from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
from collections import Counter
import json,re,sys
from xml.etree import ElementTree as ET

SITE=Path(__file__).resolve().parents[1]
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
class Inspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.stack=[];self.errors=[];self.ids=[];self.refs=[];self.labels=[];self.inputs=[];self.h1=0;self.viewport=False;self.lang=False;self.main=False;self.script=False;self.forms=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag not in VOID:self.stack.append(tag)
        if a.get('id'):self.ids.append(a['id'])
        if tag=='h1':self.h1+=1
        if tag=='html':self.lang=bool(a.get('lang'))
        if tag=='main':self.main=True
        if tag=='meta' and a.get('name')=='viewport':self.viewport=True
        if tag in ('a','link') and a.get('href') is not None:self.refs.append(('href',a['href']))
        if tag in ('img','script','iframe') and a.get('src') is not None:self.refs.append(('src',a['src']))
        if tag=='img' and a.get('data-offline-src'):self.refs.append(('src',a['data-offline-src']))
        if tag=='img' and 'alt' not in a:self.errors.append('Image without alt')
        if tag=='label' and 'for' in a:self.labels.append(a['for'])
        if tag=='form':self.forms.append(a)
        if tag in ('input','select','textarea') and a.get('id'):self.inputs.append((tag,a))
    def handle_endtag(self,tag):
        if tag in VOID:return
        if not self.stack or self.stack[-1]!=tag:self.errors.append('Unbalanced end tag '+tag)
        else:self.stack.pop()

def run():
    errors=[];pages={};links=0;assets=0
    for p in sorted(list(SITE.glob('*.html'))+list((SITE/'assets').rglob('*.html'))):
        obj=Inspector();obj.feed(p.read_text());pages[p]=obj
        errors.extend(f'{p.name}: {e}' for e in obj.errors)
        if obj.stack:errors.append(f'{p.name}: unclosed {obj.stack}')
        duplicates=[v for v,c in Counter(obj.ids).items() if c>1]
        if duplicates:errors.append(f'{p.name}: duplicate ids {duplicates}')
        if not obj.viewport or not obj.lang:errors.append(f'{p.name}: viewport or language missing')
        if p.parent==SITE:
            if obj.h1!=1 or not obj.main:errors.append(f'{p.name}: main or H1 invalid')
            if 'erpLoginModal' not in obj.ids:errors.append(f'{p.name}: portal modal missing')
            text=p.read_text()
            forbidden = re.findall(r'\b(?:Tory|Torid|Toreid)\b|99\.8%|50,000\+|zero-liability|100% Audit-Proof', text, flags=re.I)
            if forbidden:errors.append(f'{p.name}: unsupported identity or metric {forbidden}')
            if p.name=='index.html' and any(word not in text.lower() for word in ('recruitment','headhunting','temporary','outsourcing','eor')):errors.append('index.html: full agency service mix missing')
            headings=' '.join(re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>',text,flags=re.S|re.I))
            if re.search(r'oil and gas|\bports\b|\bmaritime\b|IT staffing|technical staffing',headings,re.I):errors.append(f'{p.name}: discreet specialism promoted to a heading')
            if p.name=='it-erp-consulting.html' and ('HRMS development' not in text or 'Techno-functional' not in text):errors.append('HR consultation and HRMS scope missing')
            if 'tailwind.config' not in text or '#302C65' not in text:errors.append(f'{p.name}: brand config missing')
            for tag,a in obj.inputs:
                if a.get('type') not in ('hidden','checkbox','range') and a['id'] not in obj.labels:errors.append(f'{p.name}: missing label {a["id"]}')
            for label in obj.labels:
                if label not in obj.ids:errors.append(f'{p.name}: label target absent {label}')
            for form in obj.forms:
                if form.get('action') and form.get('method','get').lower()=='get':errors.append(f'{p.name}: unsafe static GET form')
    for p,obj in pages.items():
        for kind,ref in obj.refs:
            url=urlparse(ref)
            if not ref or ref=='#':errors.append(f'{p.name}: dead reference {ref!r}');continue
            if url.scheme in ('https','http','mailto','tel','data'):continue
            if ref.startswith('//') or ref.startswith('/'):errors.append(f'{p.name}: non-relative local reference {ref}');continue
            target=(p.parent/unquote(url.path)).resolve() if url.path else p
            if not target.is_relative_to(SITE.resolve()):errors.append(f'{p.name}: reference escapes site {ref}');continue
            if not target.is_file():errors.append(f'{p.name}: missing target {ref}');continue
            # Check filename spelling and case through the parent's actual directory entries.
            if target.name not in {x.name for x in target.parent.iterdir()}:errors.append(f'{p.name}: case mismatch {ref}')
            if url.fragment and (target not in pages or unquote(url.fragment) not in pages[target].ids):errors.append(f'{p.name}: missing fragment {ref}')
            if kind=='href':links+=1
            else:assets+=1
    for svg in (SITE/'assets').rglob('*.svg'):
        try: ET.parse(svg)
        except ET.ParseError as e: errors.append(f'{svg.name}: malformed SVG {e}')
    css='\n'.join(p.read_text() for p in (SITE/'css').glob('*.css'))
    for ref in re.findall(r'url\([\'"]?([^\)\'\"]+)',css):
        if not (SITE/'css'/ref).resolve().is_file():errors.append('Missing CSS asset '+ref)
    result={'top_level_pages':len([p for p in pages if p.parent==SITE]),'embedded_html_assets':len([p for p in pages if p.parent!=SITE]),'internal_links_checked':links,'asset_references_checked':assets,'errors':errors,'status':'PASS' if not errors else 'FAIL'}
    dest=SITE/'docs/static-audit.json';dest.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    return 1 if errors else 0
if __name__=='__main__':sys.exit(run())
