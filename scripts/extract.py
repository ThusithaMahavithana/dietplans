"""Reproducible, lossless menu extraction. Never writes to sources/."""
from pathlib import Path
import re,json,hashlib,collections,difflib
ROOT=Path(__file__).resolve().parents[1]
raw=(ROOT/'sources/_chat.txt').read_text(); lines=raw.splitlines()
def clean(s):
 s=re.sub(r'[^\x20-\x7e\n]',' ',s)
 s=re.sub(r'[*_~#]','',s)
 return re.sub(r'[ \t]+',' ',s).strip().strip(' -')
def norm(s):
 s=clean(s).lower()
 for a,b in {'avacado':'avocado','avavado':'avocado','leetuce':'lettuce','catrot':'carrot','pruple':'purple','scrapped':'scraped','malum':'mallum','mallim':'mallum','mallim':'mallum','bullsyse':'bullseye','bullsey':'bullseye','bulseye':'bullseye','bullesaye':'bullseye','eggbullseye':'egg bullseye','eggomelette':'egg omelette','tbdp':'tbsp','bellpepper':'bell pepper','bellpeper':'bell pepper','origano':'oregano','mal dive':'maldive','cuttle fish':'cuttlefish','frist':'first','strawberries':'strawberry','kiwis':'kiwi','prawns':'prawn','sausages':'sausage','almonds':'almond','peanuts':'peanut','curries':'curry','vegetables':'vegetable','eggs':'egg','onions':'onion','nuts':'nut','samble':'sambal','onion levels':'onion leaves','onion laves':'onion leaves'}.items():
  s=re.sub(r'\b'+a+r'\b',b,s)
 s=re.sub(r'\b(one|two|three|four)\b',lambda m:{'one':'1','two':'2','three':'3','four':'4'}[m[1]],s)
 return re.sub(r'\s+',' ',s).strip()
starts=[i for i,l in enumerate(lines) if re.match(r'^\u200e?\[\d{4}-',l)]
messages=[]
for j,start in enumerate(starts):
 end=starts[j+1] if j+1<len(starts) else len(lines)
 head=lines[start]; body=re.sub(r'^.*?\] .*?: ','',head)+'\n'+'\n'.join(lines[start+1:end])
 messages.append(dict(start=start+1,end=end,body=body,date=head.lstrip('\u200e')[1:11]))
heading=re.compile(r'^\s*(?:first\s+meal|frist\s+meal|second\s+meal|dinner|lunch|breakfast)\s*[-:]*\s*$',re.I)
menus=[];excluded=[];audit=[];recipes=[]
for mi,msg in enumerate(messages):
 rows=msg['body'].splitlines(); hs=[(i,clean(l)) for i,l in enumerate(rows) if heading.match(clean(l))]
 if hs:
  for hi,(pos,label) in enumerate(hs):
   end=hs[hi+1][0] if hi+1<len(hs) else len(rows)
   text='\n'.join(rows[pos+1:end]).strip()
   if label.lower()=='breakfast': excluded.append(dict(start=msg['start']+pos,end=msg['start']+end-1,reason='Explicit breakfast',text=text));continue
   m=dict(id=f"menu-{msg['start']+pos:05d}",sourceLabel=label,category='Lunch' if re.match('first|frist|lunch',label,re.I) else 'Dinner',classification='Explicit' if label.lower() in ['lunch','dinner'] else 'Review',refs=[dict(start=msg['start']+pos,end=msg['start']+end-1,date=msg['date'],label=label)],raw=text,recipeTexts=[],recipeRefs=[],message=mi)
   menus.append(m)
  kind='menu'
 elif re.search(r'\bIngredients?\b',clean(msg['body']),re.I) and (re.search(r'\bMethod\b',clean(msg['body']),re.I) or 'Cheesy onion-garlic soup' in msg['body']):
  recipes.append(msg);kind='recipe'
 else:kind='non-menu'
 audit.append(dict(start=msg['start'],end=msg['end'],kind=kind))
# A recipe immediately following a dated menu supplements that menu, never becomes a second full-meal mention.
for rec in recipes:
 previous=[m for m in menus if m['refs'][0]['end']<rec['start']]
 if not previous:continue
 m=previous[-1]
 m['recipeTexts'].append(rec['body']);m['recipeRefs'].append(dict(start=rec['start'],end=rec['end']))
# Explicit follow-up quantity, retained with uncertainty about intended attachment.
for m in menus:
 if 'Spinach  & peanut salad' in m['raw']:
  rec=next(x for x in messages if clean(x['body']).lower()=='peanut 30g')
  m['recipeTexts'].append('Follow-up: Peanut 30g');m['recipeRefs'].append(dict(start=rec['start'],end=rec['end']));m['followupNote']='Peanut 30g appears later the same day; linked to the preceding spinach & peanut salad for review.'
def blocks(text):
 out=[]
 for l in text.splitlines():
  c=clean(l)
  if not re.search('[a-zA-Z0-9]',c):continue
  if '▫' in l and out:out.append([c])
  elif not out:out.append([c])
  else:out[-1].append(c)
 return out
# Keep preparation context within each dish; reorder dishes and ingredient-list tokens only.
def canonical(block):
 s=norm(' '.join(block))
 s=re.sub(r'\(\s*recipe\s*\)','',s)
 s=re.sub(r'\b(use|using|adding|add)\b','',s)
 return ' '.join(sorted(re.findall(r'\d+(?:/\d+)?|[a-z]+',s)))
lookup={};unique=[]
for m in menus:
 m['blocks']=blocks(m['raw'])
 # Hash includes recipe methods to avoid collapsing changes in preparation.
 key=json.dumps(sorted(canonical(b) for b in m['blocks']))+'|'+ '|'.join(norm(x) for x in m['recipeTexts'])
 if key in lookup:
  target=lookup[key];target['refs']+=m['refs'];target['recipeRefs']+=m['recipeRefs'];target['categories']=sorted(set(target['categories']+[m['category']]))
  if m['classification']=='Explicit':target['classification']='Explicit'
 else:
  m['categories']=[m['category']];lookup[key]=m;unique.append(m)
def portion(s):
 c=clean(s)
 hits=re.findall(r'\d+(?:\s*[-/]\s*\d+)?(?:\s+\d+/\d+)?\s*(?:g\b|tbsp\b|tbdp\b|cups?\b|teaspoons?\b|tea spoon\b|table spoon\b|ml\b)',c,re.I)
 if hits:
  if re.search(r'\b(one|two|three|four|\d+)\s*eggs?|\bor\b|/',c,re.I) and not re.search(r'\d+/\d+\s*tbsp',c,re.I):return c+' (source amounts)'
  return '; '.join(hits)
 if re.search(r'\b(one|two|three|four|few)\b|\d',c,re.I):return c+' (source count/amount)' 
 if re.search('taste|teste|required',c,re.I):return 'To taste (source wording)'
 return 'Not specified'
for m in unique:
 b=m['blocks'];first=b[1][0] if b and re.match(r'^(?:Red |Yellow )?Rice\b',b[0][0],re.I) and len(b)>1 else b[0][0]
 title=re.sub(r'\b\d+(?:/\d+)?\s*(?:g|tbsp)\b','',first,flags=re.I)
 title=re.sub(r'\(\s*Recipe\s*\)','',title,flags=re.I).strip(' ()-')
 m['title']=re.sub(r'\s+',' ',title).capitalize()+(' & rice' if b and re.match(r'^(?:Red |Yellow )?Rice\b',b[0][0],re.I) else '')
 m['dishes']=[dict(name=x[0],details=x[1:],quantity=portion(x[0])) for x in b]
 text=norm(m['raw']+'\n'+'\n'.join(m['recipeTexts']))
 tags=[]
 for tag,pat in [('Chicken',r'chicken'),('Fish',r'\bfish\b|salmon|tuna|sprats'),('Prawns',r'prawn|shrimp|kunisso'),('Cuttlefish',r'cuttlefish'),('Mutton',r'mutton'),('Eggs',r'\begg\b'),('Paneer',r'paneer'),('Soya',r'soya meat'),('Rice',r'\brice\b'),('Soup',r'soup'),('Omelette',r'omelette'),('Salad',r'salad'),('Fried',r'fried|fry|bullseye')]:
  if re.search(pat,text):tags.append(tag)
 m['tags']=tags
 allergens=[]
 for name,pat in [('Egg',r'\begg\b|mayonnaise|mayo'),('Milk',r'cheese|butter|paneer|mozzarella|cheddar|feta'),('Fish',r'\bfish\b|salmon|tuna|sprats|maldive'),('Crustaceans',r'prawn|shrimp|kunisso'),('Molluscs',r'cuttlefish'),('Peanut',r'peanut'),('Tree nuts',r'cashew|almond|mixed nut|\bnut\b'),('Soy',r'soya|soy'),('Mustard',r'mustard|musted')]:
  if re.search(pat,text):allergens.append(name)
 m['allergens']=allergens
 m['allergenNote']='Ingredient-based flags include alternatives. Check packaged ingredients and cross-contact; this is not an allergen-free guarantee.'
 if re.search('sausage|ham|bacon|mayonnaise|sauce|broth|batter',text):m['allergenNote']+=' Sausages, sauces, broth, mayonnaise or batter may contain additional milk, egg, soy or wheat; check labels.'
 if re.search(r'coconut oil\s*(?:&|and)\s*milk',text):m['allergenNote']+=' The source sometimes says only “milk” after coconut oil; confirm the milk type.'
 m['nutrition']={'status':'Insufficient portion information.','reason':'Vegetable, fruit, cooking-fat amounts, ingredient choices or recipe yield are incomplete; raw versus cooked weights are generally unspecified. No whole-meal calorie or macro total is inferred.'}
 m['suggestions']=['Specify vegetable and fruit portions before assessing meal balance.']
 if not re.search(r'\brice\b|wholegrain|pulse|lentil',text):m['suggestions'].append('No whole-grain or pulse component is specified. Consider one if it fits your overall eating plan.')
 if re.search(r'coconut oil|butter|cheese',text):m['suggestions'].append('Consider replacing some coconut oil or butter with an unsaturated oil; keep this optional change separate from the source recipe.')
 if re.search(r'sausage|ham|bacon|dry fish|sprats',text):m['suggestions'].append('Consider a less salty, minimally processed protein option; sodium depends on the product and preparation.')
 m['issues']=[]
 if m['classification']=='Review':m['issues'].append('Meal classification needs review: First meal → Lunch / Second meal → Dinner is a provisional browsing convention, not an explicit source label.')
 if re.search(r'(?:oil|butter)\s*tbsp',text):m['issues'].append('The source names tbsp without a number; the amount is Not specified.')
 if 'tbdp' in m['raw']:m['issues'].append('Source unit “tbdp” is preserved; interpreted as tbsp only for duplicate comparison.')
 if 'Tuna' in ' '.join(m['recipeTexts']) and 'Coconut oil' in m['raw']:m['issues'].append('Menu specifies coconut oil, linked cutlet recipe specifies olive oil; both retained, not combined or resolved.')
 if 'Hot Butter' in ' '.join(m['recipeTexts']):m['issues'].append('Recipe differs between ingredient list and method: deep-frying oil, extra butter, milk amount and tomato sauce are not consistently quantified.')
 if 'Cauliflower fried rice' in m['raw']:m['issues'].append('Method adds ginger, rampe, curry leaves, cinnamon and shrimp absent from the ingredient list; quantities Not specified. Recipe yield is not stated.')
 if 'followupNote' in m:m['issues'].append(m['followupNote'])
 if re.search(r'\b150\s*(?:\n|$)',clean(m['raw'])):m['issues'].append('An amount of 150 has no unit in the source; unit Not specified.')
 image_path=f"assets/meals/{m['id']}.jpg" if (ROOT/f"assets/meals/{m['id']}.jpg").exists() else f"assets/meals/{m['id']}.png"
 m['image']={'path':image_path,'status':'generated' if (ROOT/image_path).exists() else 'pending','caption':'AI-generated illustration · not an exact portion guide'}
 m['recipeIngredients']=[]
 for recipe in m['recipeTexts']:
  active=False
  for row in recipe.splitlines():
   c=clean(row)
   if re.search(r'\bIngredients?\b',c,re.I):active=True;continue
   if re.search(r'\bMethod\b',c,re.I) or c.startswith('Chop onions'):active=False
   if active and re.search('[a-zA-Z0-9]',c) and not c.startswith('(per '):m['recipeIngredients'].append({'text':c,'quantity':portion(c)})
 m['imagePrompt']=('Use case: photorealistic-natural. Asset: DietPlans full-meal catalogue '+m['id']+'. Realistic editorial food photograph, overhead camera, warm ivory tabletop, soft daylight from upper left, matte ivory plate and matching small bowls, landscape 3:2. Entire plate, all bowls and any specified drink completely visible with generous margin, nothing cropped. No cutlery, text, props, decorative food or unlisted garnish. Show ONLY the following source meal including all sides, fruit and condiments. Respect specified portions and preparation; unspecified portions are illustrative. For OR or slash alternatives depict only the FIRST named alternative, not all alternatives together; for an unspecified vegetable curry depict a neutral bowl of curry without adding identifiable unlisted vegetables. Do not add rice, bread or drink unless specified. Ingredients mentioned in the method must be included. Source:\n'+clean(m['raw'])+'\nLinked preparation:\n'+'\n'.join(clean(x) for x in m['recipeTexts']))
 # Closest distinct meal, with actual dish-level changes.
 candidates=[n for n in unique if n is not m and n['category']==m['category']]
 a=set(canonical(x) for x in b)
 if candidates:
  n=max(candidates,key=lambda n:len(a&set(canonical(x) for x in n['blocks']))/max(1,len(a|set(canonical(x) for x in n['blocks']))))
  nb=set(canonical(x) for x in n['blocks'])
  m['similar']={'id':n['id'],'thisMenu':['; '.join(x) for x in b if canonical(x) not in nb],'otherMenu':['; '.join(x) for x in n['blocks'] if canonical(x) not in a]}
 m.pop('message',None)
# Preserve exact raw excerpts and line provenance independently of display normalization.
summary={'sourceLines':len(lines),'sourceSha256':hashlib.sha256(raw.encode()).hexdigest(),'totalMentions':len(menus),'uniqueMenus':len(unique),'duplicatesMerged':len(menus)-len(unique),'unresolvedClassifications':sum(m['classification']=='Review' for m in unique),'explicitMenus':sum(m['classification']=='Explicit' for m in unique),'excludedBreakfasts':len(excluded),'recipeMessages':len(recipes),'lunch':sum('Lunch' in m['categories'] for m in unique),'dinner':sum('Dinner' in m['categories'] for m in unique)}
(ROOT/'data/menus.json').write_text(json.dumps({'summary':summary,'menus':unique},ensure_ascii=False,indent=2))
(ROOT/'data/image-prompts.json').write_text(json.dumps([{'id':m['id'],'path':m['image']['path'],'prompt':m['imagePrompt']} for m in unique],ensure_ascii=False,indent=2))
(ROOT/'reports/source-audit.json').write_text(json.dumps({'summary':summary,'messages':audit,'excluded':excluded},ensure_ascii=False,indent=2))
report=['# Extraction and deduplication review','',json.dumps(summary,indent=2),'','First/Second are provisional Lunch/Dinner browsing labels. All non-explicit classifications are flagged. No menu explicitly says it suits both meals. Explicit breakfast is excluded. Recipe messages supplement the preceding menu; they are not counted as full-meal mentions. No inferred ingredients or quantities replace source text.','', '## Comparison policy','Dish-level token comparison ignores punctuation, ingredient order, case, known spelling variants, number words and use/using/adding. Quantities and preparation words remain significant. Recipe methods must match. Alternatives stay within the original shared menu, not separate invented meals. Stable IDs use the first source heading line.','', '## All menu records']
for m in unique:report += [f"\n### {m['id']} — {m['title']}",f"Category: {', '.join(m['categories'])}; classification: {m['classification']}",'Mentions: '+', '.join(f"L{r['start']}–{r['end']}" for r in m['refs']),'Linked recipes: '+', '.join(f"L{r['start']}–{r['end']}" for r in m['recipeRefs']), 'Duplicate decision: '+('Merged identical contents / quantities / preparation.' if len(m['refs'])>1 else 'Kept as distinct.'), 'Review: '+' '.join(m['issues'])]
(ROOT/'reports/extraction.md').write_text('\n'.join(report))
print(json.dumps(summary,indent=2))
print('Recipe links:',[(m['id'],[r['start'] for r in m['recipeRefs']]) for m in unique if m['recipeRefs']])
