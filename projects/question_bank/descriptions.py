"""Resumable public description intake; no auth, solutions or execution endpoints."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import bank

CACHE = bank.ROOT.parents[1] / 'data/question_bank/hack2hire/details'
INDEX = bank.DEST / 'descriptions.json'
BASE = 'https://api.hack2hire.com/algro/v1/post/'


def validate(payload, record):
    if payload.get('status', {}).get('code') != 200:
        raise ValueError('Source response did not report success')
    data = payload['data']
    if data['id'] != record['source_post_id'] or data['type'] != record['source_type']:
        raise ValueError('Description identity/category does not match listing')
    return data


def plain_preview(markdown):
    # Skip the boilerplate LeetCode cross-reference before selecting a short excerpt.
    parts = markdown.split('\n\n', 1)
    text = parts[1] if len(parts) == 2 and 'leetcode.com' in parts[0].casefold() and 'variation' in parts[0].casefold() else markdown
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'<[^>]*>', ' ', text)
    text = re.sub(r'[`*_#>|]', '', text)
    text = ''.join(c for c in html.unescape(text) if unicodedata.category(c) != 'So' and c not in ('\ufe0f', '\u200d'))
    return ' '.join(text.split())


def excerpt(text, limit=25):
    words = plain_preview(text).split()
    return ' '.join(words[:limit]) + (' …' if len(words) > limit else '')


def cited_leetcode(text, reference):
    by_slug = {r['slug']: r for r in reference}
    slugs = sorted(set(re.findall(r'https?://(?:www\.)?leetcode\.com/problems/([^\s)/?#]+)', text)))
    return [{'slug': slug, 'id': by_slug.get(slug, {}).get('id'),
             'title': by_slug.get(slug, {}).get('title'),
             'url': 'https://leetcode.com/problems/' + slug + '/',
             'relationship': 'source_cited_related_problem',
             'evidence': 'Explicit link in source description/preview; specification equivalence not established',
             'merge_allowed': False} for slug in slugs]


TOPIC_RULES = {
    'caching': r'\bcach(?:e|es|ing)\b|\bcdn\b',
    'storage': r'\bstorage\b|\bfilesystem\b|\bfile system\b|\bobject store\b',
    'databases': r'\bdatabase\b|\bsql\b|\btransaction\b|\bpostgres\b',
    'queues-streaming': r'\bqueue\b|\bkafka\b|\bstream(?:ing)?\b|\bpub.?sub\b',
    'concurrency': r'\bconcurren\w*\b|\bthread.safe\b|\batomic\b|\brace condition\b',
    'rate-limiting': r'\brate.limit\w*\b|\bthrottl\w*\b',
    'search-retrieval': r'\bsearch\b|\bretrieval\b|\bvector index\b',
    'recommendations-ranking': r'\brecommend\w*\b|\branking\b|\brerank\w*\b',
    'ml-training-serving': r'\bmodel serving\b|\binference\b|\btraining\b|\bfeature store\b',
    'scheduling': r'\bschedul\w*\b|\bdispatcher\b',
    'observability': r'\bmonitor\w*\b|\bmetrics\b|\blogging\b|\bobservability\b',
    'payments-finance': r'\bpayment\w*\b|\bcredit\b|\bbanking\b|\btrading\b',
    'graphs': r'\bgraph\b|\bdag\b|\bdependency\b|\bshortest path\b',
    'time-series': r'\btime.series\b|\brolling window\b|\bconsecutive\b',
    'sql-window-functions': r'\bwindow function\b|\bpartition by\b|\brow_number\b|\bdense_rank\b',
    'sql-joins': r'\bjoin\b|\bjoins\b',
}


def summarize(record, envelope, reference):
    data = validate(envelope['payload'], record)
    preview = data.get('contentPreview') or ''
    if not isinstance(preview, str):
        raise ValueError('Description must be text or absent')
    local = 'data/question_bank/hack2hire/details/' + record['source_post_id'] + '.json'
    topics = [name for name, rule in TOPIC_RULES.items()
              if re.search(rule, record['title'] + '\n' + plain_preview(preview), re.I)]
    return {'source_post_id': record['source_post_id'],
            'description': {'status': 'public_group_preview' if preview.strip() else 'empty_source_preview',
                            'source_field': 'contentPreview', 'scope': 'group-level; not a complete variant specification',
                            'excerpt': excerpt(preview), 'source_characters': len(preview),
                            'content_sha256': hashlib.sha256(preview.encode()).hexdigest(),
                            'source_url': envelope['url'], 'local_source_cache': local,
                            'source_response_sha256': envelope['response_sha256'],
                            'retrieved_at_utc': envelope.get('retrieved_at_utc')},
            'source_company_attributes': data.get('company') or {},
            'source_stages': data.get('stages') or [],
            'source_last_report_seen': data.get('lastReportSeenData'),
            'source_difficulty': data.get('difficulty'),
            'source_title_at_description_fetch': data['title'],
            'description_source_updated_at': data.get('updatedDate'),
            'description_inferred_topics': topics,
            'inferred_topic_basis': 'keyword heuristics over title and public description; not verified requirements',
            'source_leetcode_relationships': cited_leetcode(preview, reference)}


def attach(records, index):
    by_id = {r['source_post_id']: r for r in records}
    for detail in index['records']:
        record = by_id.get(detail['source_post_id'])
        if record is None:
            continue
        record.update({k: v for k, v in detail.items() if k not in ('source_post_id', 'description')})
        record['description'] = {k: v for k, v in detail['description'].items() if k != 'excerpt'}
        record['description']['excerpt_index'] = 'descriptions.json#' + record['source_post_id']
        record['description_matches_listing_version'] = record.get('source_updated_at') == detail.get('description_source_updated_at')
        if record['description']['status'] == 'public_group_preview':
            for variant in record['variants']:
                variant['group_description_ref'] = record['uid']
                # Group prose cannot be promoted into a variant-specific contract.
                if variant['content_status'] == 'not_acquired':
                    variant['content_status'] = 'group_preview_available'


def index_cache():
    snapshot = json.loads((bank.DEST / 'bank.json').read_text())
    reference = json.loads((bank.DEST / 'leetcode-metadata.json').read_text())
    details = []
    for record in snapshot['records']:
        path = CACHE / (record['source_post_id'] + '.json')
        if path.exists():
            details.append(summarize(record, json.loads(path.read_text()), reference))
    index = {'schema': 'gamma.question-descriptions.v1',
             'indexed_at_utc': datetime.now(timezone.utc).isoformat(),
             'source_scope': 'public group descriptions/previews; no full-content, solution or execution endpoints',
             'counts': {'groups_indexed': len(details), 'groups_expected': len(snapshot['records']),
                        'description_status': dict(Counter(d['description']['status'] for d in details)),
                        'groups_with_source_leetcode_citations': sum(bool(d['source_leetcode_relationships']) for d in details)},
             'records': details}
    INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False) + '\n')
    attach(snapshot['records'], index)
    snapshot['counts'] = bank.counts(snapshot['records'])
    snapshot['content_scope'] = 'complete listing metadata; public group previews indexed separately from variant-specific specification reviews; no solutions'
    (bank.DEST / 'bank.json').write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + '\n')
    bank.write_report(snapshot)
    print(json.dumps(index['counts'], indent=2))


def acquire():
    records = json.loads((bank.DEST / 'bank.json').read_text())['records']
    CACHE.mkdir(parents=True, exist_ok=True)
    last = 0.0
    for record in records:
        target = CACHE / (record['source_post_id'] + '.json')
        if target.exists():
            cached = validate(json.loads(target.read_text())['payload'], record)
            if cached.get('updatedDate') == record.get('source_updated_at'):
                continue
        url = BASE + record['source_post_id']
        for attempt in range(90):
            time.sleep(max(0, 1.15 - (time.monotonic() - last)))
            last = time.monotonic()
            try:
                with urlopen(Request(url, headers={'User-Agent': 'Gamma-question-bank-metadata/1.0'}), timeout=40) as response:
                    raw = response.read()
                payload = json.loads(raw)
                validate(payload, record)
                envelope = {'url': url, 'response_sha256': hashlib.sha256(raw).hexdigest(),
                            'retrieved_at_utc': datetime.now(timezone.utc).isoformat(), 'payload': payload}
                temporary = target.with_suffix('.tmp')
                temporary.write_text(json.dumps(envelope, ensure_ascii=False))
                temporary.replace(target)
                break
            except HTTPError as error:
                if error.code == 429:
                    time.sleep(max(1, float(error.headers.get('Retry-After', '1'))))
                elif error.code in (500, 502, 503, 504) and attempt < 5:
                    time.sleep(2 ** attempt)
                else:
                    raise
        else:
            raise RuntimeError('Persistent rate limit; cache preserved, rerun acquire to resume')
        cached = len(list(CACHE.glob('*.json')))
        if cached % 25 == 0:
            print(f'{cached}/{len(records)} descriptions cached', flush=True)
    index_cache()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['acquire', 'index', 'show'])
    parser.add_argument('--id', help='Hack2Hire post ID for show')
    args = parser.parse_args()
    if args.command == 'acquire':
        acquire()
    elif args.command == 'index':
        index_cache()
    else:
        if not args.id or not re.fullmatch(r'[a-f0-9]{24}', args.id):
            parser.error('show requires a 24-character source post ID')
        path = CACHE / (args.id + '.json')
        if not path.exists():
            parser.error('Local description not cached; run acquire first')
        data = json.loads(path.read_text())['payload']['data']
        print(data['title'])
        print('Companies: ' + ', '.join((data.get('company') or {}).keys()))
        print('\n' + (data.get('contentPreview') or '[No public description provided]'))


if __name__ == '__main__':
    main()
