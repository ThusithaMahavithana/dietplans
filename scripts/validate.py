"""Data integrity and traceability checks, independent of the extraction implementation."""
import json, re, hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=(root/'sources/_chat.txt').read_text()
lines=source.splitlines()
data=json.loads((root/'data/menus.json').read_text());menus=data['menus'];s=data['summary']
assert len(lines)==s['sourceLines']==10405
assert hashlib.sha256(source.encode()).hexdigest()==s['sourceSha256']
assert len(menus)==s['uniqueMenus']
assert len({m['id'] for m in menus})==len(menus)
assert sum(len(m['refs']) for m in menus)==s['totalMentions']
assert s['totalMentions']-s['uniqueMenus']==s['duplicatesMerged']
covered=[]
for m in menus:
 assert m['dishes'] and m['raw'] and m['imagePrompt'] and m['categories']
 assert all(d['quantity'] for d in m['dishes'])
 assert set(m['categories']) <= {'Lunch','Dinner'}
 assert not any(r['label'].lower()=='breakfast' for r in m['refs'])
 for r in m['refs']:
  assert 1<=r['start']<=r['end']<=len(lines)
  assert re.search('meal|dinner|lunch',lines[r['start']-1],re.I)
  covered.append(r['start'])
 for r in m['recipeRefs']:assert 1<=r['start']<=r['end']<=len(lines)
 if m['classification']=='Review':assert any('classification' in i for i in m['issues'])
 assert m['image']['path'].split('/')[-1].split('.')[0]==m['id']
 if m['image']['status']=='generated':assert (root/m['image']['path']).stat().st_size>10000
 assert m['similar']['id'] in {x['id'] for x in menus} and m['similar']['id']!=m['id']
assert len(set(covered))==len(covered)
# Independent heading census catches misspellings and nonstandard bullet formats.
headings=[];breakfast=[]
for i,line in enumerate(lines,1):
 text=re.sub(r'[^A-Za-z ]','',line).lower().strip()
 text=' '.join(text.split())
 if text in ['first meal','frist meal','second meal','dinner','lunch']:headings.append(i)
 if text=='breakfast':breakfast.append(i)
assert set(headings)==set(covered),(set(headings)-set(covered),set(covered)-set(headings))
assert len(breakfast)==s['excludedBreakfasts']
prompts=json.loads((root/'data/image-prompts.json').read_text())
assert {p['id'] for p in prompts}=={m['id'] for m in menus}
# Known meaningful variations must survive as separate menus.
byid={m['id']:m for m in menus}
assert '250g' in byid['menu-08156']['raw'] and '200g' in byid['menu-05306']['raw']
assert byid['menu-08156']['id']!=byid['menu-05306']['id']
assert len(byid['menu-05227']['refs'])==4
assert '906' in str(byid['menu-00896']['recipeRefs']) and 'mint chutney' in ' '.join(byid['menu-00896']['recipeTexts'])
assert 'shrimp' in byid['menu-09319']['raw']
assert byid['menu-07349']['recipeRefs'][0]['start']==7373
generated=sum(m['image']['status']=='generated' for m in menus)
print(f"PASS: {len(headings)} meal mentions; {len(menus)} unique records; {s['duplicatesMerged']} merges; {generated}/{len(menus)} mapped images.")
print('PASS: full heading coverage, recipe linkage, breakfast exclusion, variation regression, source hash, IDs, image prompts and references.')
