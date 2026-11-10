#!/usr/bin/env python3
"""News Bites v0.6: conservative, source-linked RSS curation. Python stdlib only."""
import datetime as dt
import email.utils
import html
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parents[1]
MALTA = ZoneInfo('Europe/Malta')
FEEDS = [
    ('BBC News · World', 'Major World Events', 'https://feeds.bbci.co.uk/news/world/rss.xml'),
    ('BBC News · Science', 'Science & Technology', 'https://feeds.bbci.co.uk/news/science_and_environment/rss.xml'),
    ('BBC News · Business', 'Business & Marketing', 'https://feeds.bbci.co.uk/news/business/rss.xml'),
    ('BBC News · Health', 'Health & Wellness', 'https://feeds.bbci.co.uk/news/health/rss.xml'),
    ('BBC News · Arts', 'Art, Artists & History of Art', 'https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml'),
    ('The Guardian · World', 'Major World Events', 'https://www.theguardian.com/world/rss'),
    ('Deutsche Welle', 'Major World Events', 'https://rss.dw.com/xml/rss-en-all'),
    ('Times of Malta', 'Politics & Government', 'https://timesofmalta.com/news/rss/'),
]
STOP = set('a an and are as at after before by for from has have in into is it its of on or the their to with over amid about says say new latest live update updates news report reports'.split())
IMPACT = {
    'war': 5, 'invasion': 6, 'ceasefire': 5, 'peace': 4, 'election': 5, 'president': 3,
    'prime': 2, 'parliament': 3, 'government': 2, 'court': 2, 'supreme': 3,
    'earthquake': 5, 'flood': 3, 'wildfire': 4, 'hurricane': 4, 'emergency': 3,
    'pandemic': 5, 'outbreak': 4, 'vaccine': 3, 'research': 2, 'discovery': 3,
    'climate': 3, 'economy': 3, 'inflation': 3, 'interest': 2, 'rates': 2,
    'budget': 2, 'treaty': 4, 'sanctions': 3, 'killed': 2, 'deaths': 3,
    'malta': 3, 'maltese': 3, 'eu': 2, 'european': 2,
}
CATEGORY_TERMS = [
    ('Crime, War & Justice', ('war', 'military', 'attack', 'court', 'police', 'trial', 'killed', 'justice', 'prison', 'explosion', 'ceasefire')),
    ('Politics & Government', ('election', 'government', 'minister', 'parliament', 'president', 'policy', 'diplomat', 'vote')),
    ('Environment & Climate', ('climate', 'flood', 'wildfire', 'carbon', 'emissions', 'environment', 'biodiversity')),
    ('Health & Wellness', ('health', 'hospital', 'medical', 'vaccine', 'disease', 'outbreak', 'patient')),
    ('Science & Technology', ('science', 'technology', 'research', 'space', 'satellite', 'artificial intelligence', 'scientist')),
    ('Business & Marketing', ('business', 'economy', 'inflation', 'market', 'bank', 'company', 'trade', 'advertising')),
    ('Books & Authors', ('book', 'novel', 'author', 'literature', 'publishing')),
    ('Art, Artists & History of Art', ('art', 'museum', 'artist', 'exhibition', 'painting', 'gallery')),
]

def clean(s):
    s = re.sub(r'<[^>]*>', ' ', s or '')
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()

def tokens(title):
    return {w for w in re.findall(r'[a-z0-9]+', title.lower()) if len(w) > 2 and w not in STOP}

def same_event(a, b):
    """Conservative heuristic: do not merge merely because both mention a country."""
    ta, tb = tokens(a['title']), tokens(b['title'])
    shared = ta & tb
    if len(shared) < 2:
        return False
    overlap = len(shared) / max(1, min(len(ta), len(tb)))
    seq = SequenceMatcher(None, ' '.join(sorted(ta)), ' '.join(sorted(tb))).ratio()
    return (len(shared) >= 3 and overlap >= .56) or (len(shared) >= 2 and seq >= .78)

def categorize(item):
    title = item['title'].lower()
    scores = [(sum(1 for word in terms if re.search(r'\b'+re.escape(word)+r'\b', title)), category) for category, terms in CATEGORY_TERMS]
    count, category = max(scores)
    return category if count else item['cat']

def score(item, corroboration=1):
    words = tokens(item['title'])
    importance = sum(IMPACT.get(w, 0) for w in words)
    importance = min(importance, 12)
    age_bonus = max(0, 3 - item['age']/12)
    malta_bonus = 2 if 'Times of Malta' in item['source'] else 0
    return round(importance + age_bonus + malta_bonus + min(corroboration-1, 2)*2, 2)

def parse_date(s):
    try:
        d = email.utils.parsedate_to_datetime(s)
        return d.astimezone(dt.timezone.utc) if d else None
    except (TypeError, ValueError, OverflowError):
        return None

def collect(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    out, failures = [], []
    for source, cat, url in FEEDS:
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'NewsBitesPersonalReader/0.6 (source-linked RSS preview)', 'Accept': 'application/rss+xml, application/xml, text/xml'})
            with urllib.request.urlopen(request, timeout=14) as response:
                raw = response.read(1_500_001)
            if len(raw) > 1_500_000:
                raise ValueError('Feed too large')
            root = ET.fromstring(raw)
            entries = root.findall('.//item')
            if not entries:
                raise ValueError('No RSS items')
            for entry in entries[:40]:
                title, link = clean(entry.findtext('title')), (entry.findtext('link') or '').strip()
                published = parse_date(entry.findtext('pubDate'))
                description = clean(entry.findtext('description'))
                if not (title and description and published and link.startswith('https://')):
                    continue
                age = (now - published).total_seconds()/3600
                if not (-2 <= age <= 48):
                    continue
                out.append({'cat': cat, 'title': title[:200], 'summary': description[:240], 'source': source, 'url': link, 'date': published.isoformat(), 'age': age})
        except Exception as exc:
            failures.append(f'{source}: {type(exc).__name__}: {str(exc)[:100]}')
    return out, failures

def cluster(items):
    groups = []
    for item in sorted(items, key=lambda x: x['age']):
        group = next((g for g in groups if any(same_event(item, other) for other in g)), None)
        if group is None:
            groups.append([item])
        elif not any(x['url'] == item['url'] for x in group):
            group.append(item)
    return groups

def choose(items, limit=12):
    candidates = []
    for group in cluster(items):
        lead = dict(group[0])
        lead['cat'] = categorize(lead)
        lead['sources'] = [{'name': x['source'], 'url': x['url'], 'date': x['date']} for x in group[:4]]
        lead['source_count'] = len(set(x['source'] for x in group))
        lead['score'] = score(lead, lead['source_count'])
        candidates.append(lead)
    candidates.sort(key=lambda x: (-x['score'], x['age']))
    selected, source_counts, cat_counts, malta_count = [], {}, {}, 0
    for item in candidates:
        local = 'Times of Malta' in item['source']
        if local and malta_count >= 3:
            continue
        if source_counts.get(item['source'], 0) >= 4 or cat_counts.get(item['cat'], 0) >= 5:
            continue
        selected.append(item)
        source_counts[item['source']] = source_counts.get(item['source'], 0) + 1
        cat_counts[item['cat']] = cat_counts.get(item['cat'], 0) + 1
        malta_count += int(local)
        if len(selected) == limit:
            break
    return selected

def escape(s):
    return html.escape(str(s), quote=True)

def render(morning, generated_at, afternoon=None):
    template = (ROOT/'template.html').read_text(encoding='utf-8')
    top = ''.join(f'<button class="toprow" data-jump="story-{i}"><span class="num">{i+1:02}</span><span><strong>{escape(s["title"])}</strong><small>{escape(s["cat"])}</small></span></button>' for i,s in enumerate(morning[:3]))
    def card(s, ident):
        sources = ' · '.join(f'<a href="{escape(x["url"])}" target="_blank" rel="noopener noreferrer">{escape(x["name"])} ↗</a>' for x in s.get('sources', [])[:3])
        return (f'<article class="story" id="{ident}"><div class="eyebrow">{escape(s["cat"])}</div>'
                f'<h3>{escape(s["title"])}</h3><p>{escape(s["summary"])}</p>'
                '<div class="why"><strong>Publisher description — not independently verified</strong>'
                '<p>This description comes from a source RSS feed. News Bites has not independently confirmed its claims.</p></div>'
                '<details class="expanded"><summary>Read more</summary>'
                '<p>For detailed reporting, background and supporting evidence, consult the original publisher. '
                'An independently researched explanation is not available for this story yet.</p></details>'
                f'<div class="actions"><span class="source">{sources} · {escape(s["date"][:10])}</span></div></article>')
    cards = ''.join(card(s, f'story-{i}') for i,s in enumerate(morning))
    if afternoon:
        cards += ('<div class="sectionhead"><h2>4 PM developments</h2></div>'
                  '<p class="sub">Additional source-linked developments since the morning edition; not independently verified.</p>')
        cards += ''.join(card(s, f'afternoon-{i}') for i,s in enumerate(afternoon))
    template = template.replace('<!-- TOPROWS -->', top).replace('<!-- STORIES -->', cards)
    template = template.replace('<!-- EDITION_DATE -->', escape(generated_at.strftime('%d %B %Y, %H:%M Malta time')))
    template = template.replace('<!-- STORY_COUNT -->', str(len(morning)))
    audio = [{'title': s['title'], 'summary': s['summary'], 'why': ''} for s in morning[:3]]
    template = template.replace('/* AUDIO_DATA */', json.dumps(audio, ensure_ascii=True).replace('<', '\\u003c'))
    return template

def main():
    now = dt.datetime.now(MALTA)
    mode = os.environ.get('NEWS_BITES_MODE', 'morning').lower()
    if mode not in ('morning', 'afternoon'):
        raise ValueError('NEWS_BITES_MODE must be morning or afternoon')
    items, warnings = collect()
    for warning in warnings:
        print('Feed warning:', warning, file=sys.stderr)
    ranked = choose(items)
    edition_path = ROOT/'edition.json'
    if mode == 'afternoon':
        if not edition_path.exists():
            print('No existing morning edition; no afternoon update')
            return 0
        edition = json.loads(edition_path.read_text(encoding='utf-8'))
        if edition.get('edition_date') != now.date().isoformat():
            print('Morning edition is not from today; keeping previous edition unchanged')
            return 0
        morning = edition['stories']
        morning_time = dt.datetime.fromisoformat(edition['generated_at'])
        previous_urls = {s['url'] for s in morning}
        previous_urls.update(s['url'] for s in edition.get('afternoon', []))
        afternoon = [s for s in ranked if s['url'] not in previous_urls
                     and dt.datetime.fromisoformat(s['date']) > morning_time.astimezone(dt.timezone.utc)
                     and s['score'] >= 6]
        afternoon = [s for s in afternoon if not any(same_event(s, x) for x in morning)][:3]
        if not afternoon:
            print('No qualifying major new developments at 4 PM; no change')
            return 0
        edition['afternoon'] = afternoon
        edition['afternoon_checked_at'] = now.isoformat()
        generated = morning_time
    else:
        if len(ranked) < 3:
            print('Too few usable headlines; retaining prior published edition', file=sys.stderr)
            return 1
        morning = ranked
        afternoon = []
        generated = now
        edition = {'edition_date': now.date().isoformat(), 'generated_at': now.isoformat(),
                   'mode': 'Publisher RSS preview; automated heuristic ranking, not fact-checked',
                   'stories': morning, 'afternoon': [], 'feed_warnings': warnings}
    output = render(morning, generated, afternoon)
    (ROOT/'index.html').write_text(output, encoding='utf-8')
    edition_path.write_text(json.dumps(edition, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Updated {mode} edition: {len(morning)} morning stories, {len(afternoon)} afternoon developments')
    return 0

if __name__ == '__main__':
    sys.exit(main())
