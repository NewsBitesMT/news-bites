#!/usr/bin/env python3
"""Conservative RSS headline preview: no AI, no invented claims, stdlib only."""
import datetime as dt, email.utils, html, json, pathlib, re, sys, urllib.request, xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parents[1]
FEEDS=[
 ('BBC News · World','Major World Events','https://feeds.bbci.co.uk/news/world/rss.xml'),
 ('BBC News · Science','Science & Technology','https://feeds.bbci.co.uk/news/science_and_environment/rss.xml'),
 ('BBC News · Business','Business & Marketing','https://feeds.bbci.co.uk/news/business/rss.xml'),
 ('BBC News · Health','Health & Wellness','https://feeds.bbci.co.uk/news/health/rss.xml'),
 ('BBC News · Arts','Art, Artists & History of Art','https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml'),
 ('The Guardian · World','Major World Events','https://www.theguardian.com/world/rss'),
 ('Deutsche Welle','Major World Events','https://rss.dw.com/xml/rss-en-all'),
 ('Times of Malta · News','Politics & Government','https://timesofmalta.com/news/rss/'),
]
def clean(s):
 s=re.sub(r'<[^>]*>',' ',s or '')
 return re.sub(r'\s+',' ',html.unescape(s)).strip()
def parse_date(s):
 try:
  d=email.utils.parsedate_to_datetime(s)
  return d.astimezone(dt.timezone.utc) if d else None
 except (TypeError,ValueError,OverflowError):return None
def collect():
 now=dt.datetime.now(dt.timezone.utc); out=[]; failures=[]
 for source,category,url in FEEDS:
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'NewsBitesPersonalReader/0.5 (+RSS headlines only)','Accept':'application/rss+xml, application/xml, text/xml'})
   with urllib.request.urlopen(req,timeout=14) as response:
    raw=response.read(1_500_001)
   if len(raw)>1_500_000:raise ValueError('Feed too large')
   root=ET.fromstring(raw)
   items=root.findall('.//item')
   if not items:raise ValueError('No RSS items')
   for item in items[:35]:
    title=clean(item.findtext('title')); link=(item.findtext('link') or '').strip()
    date=parse_date(item.findtext('pubDate'))
    description=clean(item.findtext('description'))
    if not (title and link.startswith('https://') and date):continue
    age=(now-date).total_seconds()/3600
    if age < -2 or age>48:continue
    # Do not publish feed body text as our own summary; retain only short source attribution.
    out.append({'cat':category,'title':title[:200],'summary':description[:240], 'source':source,'url':link,'date':date.isoformat(),'age':age})
  except Exception as exc:failures.append(f'{source}: {type(exc).__name__}: {str(exc)[:90]}')
 return out,failures

def choose(items,limit=12):
 seen=set(); selected=[]; counts={}; malta=0
 for item in sorted(items,key=lambda x:x['age']):
  norm=re.sub(r'[^a-z0-9 ]','',item['title'].lower())
  norm=' '.join(norm.split()[:10]);
  if norm in seen:continue
  seen.add(norm)
  is_malta='Malta' in item['source']
  if is_malta and malta>=3:continue
  if counts.get(item['source'],0)>=4:continue
  if not item['summary']:continue
  selected.append(item);counts[item['source']]=counts.get(item['source'],0)+1
  if is_malta:malta+=1
  if len(selected)>=limit:break
 return selected

def main():
 items,failures=collect(); selected=choose(items)
 for f in failures:print('Feed warning:',f,file=sys.stderr)
 if len(selected)<3:
  print('Not enough fresh source items. Preserving previously published edition.',file=sys.stderr)
  return 1
 now=dt.datetime.now(ZoneInfo('Europe/Malta'))
 edition={'generated_at':now.isoformat(),'mode':'SOURCE HEADLINE PREVIEW — not independently verified or AI summarized','stories':selected,'feed_warnings':failures}
 # Build output using the existing v0.4 styling; text inserted as escaped HTML.
 template=(ROOT/'template.html').read_text(encoding='utf-8')
 def e(s):return html.escape(str(s),quote=True)
 top=''.join(f'<button class="toprow" data-jump="story-{i}"><span class="num">{i+1:02}</span><span><strong>{e(s["title"])}</strong><small>{e(s["cat"])}</small></span></button>' for i,s in enumerate(selected[:3]))
 cards=''.join(f'<article class="story" id="story-{i}"><div class="eyebrow">{e(s["cat"])}</div><h3>{e(s["title"])}</h3><p>{e(s["summary"])}</p><div class="why"><strong>Publisher description</strong><p>This text comes from the publisher’s RSS feed; it has not been independently verified or rewritten by News Bites.</p></div><details class="expanded"><summary>Read more</summary><p>For full reporting, context and supporting evidence, read the original article. News Bites is not yet generating independent expanded explanations for live stories.</p></details><div class="actions"><a class="source" href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">{e(s["source"])} · {e(s["date"][:10])} · Read original ↗</a></div></article>' for i,s in enumerate(selected))
 template=template.replace('<!-- TOPROWS -->',top).replace('<!-- STORIES -->',cards)
 template=template.replace('<!-- EDITION_DATE -->',e(now.strftime('%d %B %Y, %H:%M Malta time')))
 template=template.replace('<!-- STORY_COUNT -->',str(len(selected)))
 # JSON data only for top-three audio. Escaped against script termination.
 audio=[{'title':s['title'],'summary':s['summary'],'why':''} for s in selected[:3]]
 template=template.replace('/* AUDIO_DATA */',json.dumps(audio,ensure_ascii=True).replace('<','\\u003c'))
 (ROOT/'index.html').write_text(template,encoding='utf-8')
 (ROOT/'edition.json').write_text(json.dumps(edition,ensure_ascii=False,indent=2),encoding='utf-8')
 print(f'Published {len(selected)} source-linked headline previews, {now.isoformat()}')
 return 0
if __name__=='__main__':sys.exit(main())
