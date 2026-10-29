"""Source-linked interview inventory; no solution admission or protected payload reads."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'hack2hire'
API = 'https://api.hack2hire.com/algro/v1/post/filter'
LC_API = 'https://leetcode.com/api/problems/all/'
CATEGORIES = {
    'ALGORITHM': ('coding', 'coding-questions'),
    'SD': ('system-design', 'system-design'),
    'ML_SD': ('ml-system-design', 'ml-system-design'),
    'SQL': ('sql', 'sql-questions'),
    'OOD': ('object-oriented-design', 'object-oriented-design'),
}
STOP = {'a', 'an', 'the', 'of', 'to', 'in', 'and', 'with', 'for', 'by', 'design', 'find', 'implement'}


def get_json(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Gamma-question-bank-metadata/1.0'}), timeout=40) as response:
                raw = response.read()
            return json.loads(raw), hashlib.sha256(raw).hexdigest()
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError('Unreachable request state')


def collect_category(kind, fetch=get_json):
    result, receipts, seen = [], [], set()
    total = None
    page = 1
    while total is None or len(result) < total:
        url = API + '?' + urlencode({'type': kind, 'page': page, 'perPage': 100})
        payload, digest = fetch(url)
        if payload.get('status', {}).get('code') != 200:
            raise ValueError('Source did not return success: ' + url)
        data = payload['data']
        if total is None:
            total = data['total']
        if data['total'] != total or data['page'] != page or not isinstance(total, int):
            raise ValueError('Pagination identity or denominator changed')
        rows = data['data']
        if not rows and len(result) < total:
            raise ValueError('Incomplete pagination')
        for row in rows:
            if row['id'] in seen or row['type'] != kind:
                raise ValueError('Duplicate identity or category mismatch')
            seen.add(row['id'])
            result.append(row)
        if len(result) > total:
            raise ValueError('Source exceeded advertised denominator')
        receipts.append({'url': url, 'response_sha256': digest, 'page': page,
                         'reported_total': total, 'returned_records': len(rows)})
        page += 1
    return result, receipts


def normalized(title):
    return ' '.join(re.findall(r'[a-z0-9]+', unicodedata.normalize('NFKD', title).casefold()))


def lc_metadata(payload):
    rows = []
    for item in payload['stat_status_pairs']:
        stat = item['stat']
        rows.append({'id': str(stat['frontend_question_id']), 'title': stat['question__title'],
                     'slug': stat['question__title_slug'], 'paid_only': item.get('paid_only'),
                     'url': 'https://leetcode.com/problems/' + stat['question__title_slug'] + '/'})
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate LeetCode metadata identity')
    return rows


class Overlap:
    def __init__(self, rows):
        self.rows = rows
        self.exact = defaultdict(list)
        self.tokens = defaultdict(set)
        for index, row in enumerate(rows):
            self.exact[normalized(row['title'])].append(row)
            for word in set(normalized(row['title']).split()) - STOP:
                self.tokens[word].add(index)

    def classify(self, title, category):
        exact = self.exact.get(normalized(title), [])
        if exact:
            return {'status': 'exact_title_candidate' if category in ('coding', 'sql') else 'related_concept_title_candidate',
                    'evidence': 'normalized title only; specification equivalence not reviewed',
                    'candidates': [{**row, 'title_score': 1.0} for row in exact], 'merge_allowed': False}
        words = set(normalized(title).split()) - STOP
        indexes = set().union(*(self.tokens[w] for w in words)) if words else set()
        ranked = []
        for index in indexes:
            row = self.rows[index]
            other = set(normalized(row['title']).split()) - STOP
            if len(words & other) < 2:
                continue
            score = .6 * len(words & other) / len(words | other) + .4 * SequenceMatcher(None, normalized(title), normalized(row['title'])).ratio()
            if score >= .68:
                ranked.append({**row, 'title_score': round(score, 4)})
        ranked.sort(key=lambda row: (-row['title_score'], row['id']))
        return {'status': 'possible_title_overlap' if ranked else 'no_title_match_found',
                'evidence': 'lexical title comparison only; no match does not establish novelty',
                'candidates': ranked[:3], 'merge_allowed': False}


def variant_rows(post):
    questions = post.get('codingQuestions') or []
    if questions:
        ids = [q['id'] for q in questions]
        if len(set(ids)) != len(ids):
            raise ValueError('Duplicate variant identity')
        return [{'id': qid, 'ordinal': i + 1} for i, qid in enumerate(ids)]
    return [{'id': None, 'ordinal': 1}]


def build_record(post, matcher):
    category, route = CATEGORIES[post['type']]
    base = 'https://www.hack2hire.com/question-bank/questions/' + route + '/' + post['id']
    variants = variant_rows(post)
    for variant in variants:
        variant['uid'] = 'hack2hire:' + (variant['id'] or post['id'])
        variant['url'] = base + ('/practice?questionId=' + variant['id'] if variant['id'] else '')
        variant['content_status'] = 'not_acquired'
    return {'uid': 'hack2hire:post:' + post['id'], 'source_post_id': post['id'],
            'title': post['title'], 'category': category, 'source_type': post['type'],
            'source_algorithm_tags': post.get('algorithmTags') or [],
            'topics': [tag.casefold().replace('_', '-') for tag in (post.get('algorithmTags') or [])],
            'companies': sorted((post.get('company') or {}).keys()),
            'source_difficulty': post.get('difficulty'), 'source_frequency': post.get('frequency'),
            'source_updated_at': post.get('updatedDate'),
            'anonymous_listing_locked': post.get('isLocked'),
            'url': base, 'variants': variants,
            'leetcode_overlap': matcher.classify(post['title'], category),
            'qualification_status': 'unqualified_intake', 'solution_count': 0,
            'license': 'not established; source-linked metadata only'}


def apply_reviews(records):
    path = DEST / 'reviews.json'
    if not path.exists():
        return
    reviews = json.loads(path.read_text())
    by_post = {r['source_post_id']: r for r in records}
    for review in reviews['groups']:
        record = by_post[review['post_id']]
        record['specification_review'] = review
        if review.get('leetcode_relationship'):
            record['reviewed_leetcode_relationship'] = review['leetcode_relationship']
        by_variant = {v['id']: v for v in record['variants']}
        for detail in review.get('variants', []):
            variant = by_variant[detail['id']]
            variant['review'] = detail
            variant['content_status'] = detail['content_status']


def write_report(bank):
    lines = ['# Hack2Hire intake report', '',
             'Snapshot: ' + bank['retrieved_at_utc'], '',
             'Complete public listing inventory; detailed acquisition remains incomplete. '
             'This is unqualified interview-practice intake, separate from Algorithm Solver evaluation.', '',
             '| Category | Groups | Entries / variants |', '| --- | ---: | ---: |']
    for category in sorted(bank['counts']['categories']):
        rows = [r for r in bank['records'] if r['category'] == category]
        lines.append(f"| {category} | {len(rows)} | {sum(len(r['variants']) for r in rows)} |")
    lines += ['', '## Acquisition and overlap gaps', '',
              'Browser check on 2026-10-28: Chrome A (XY) displayed Log In; clicking it opened a blank /login page. '
              'Authenticated access is unverified. Anonymous listing lock flags do not establish the user’s subscription or access.', '',
              f"LeetCode comparison uses {bank['leetcode_metadata_records']:,} official public title/ID/slug records. "
              'Title matches are candidates, never automatic merges. No title match is not evidence of a novel problem. '
              'Full input/output, constraints, tie-breaking and variant comparisons remain pending except for the limited reviews below.', '',
              'Content statuses: `' + json.dumps(bank['counts']['content_status'], sort_keys=True) + '`.', '',
              'Overlap statuses: `' + json.dumps(bank['counts']['overlap_status'], sort_keys=True) + '`.', '',
              '## Databricks coding', '', '| Problem | Variants | Review |', '| --- | ---: | --- |']
    for r in bank['records']:
        if r['category'] == 'coding' and 'DATABRICKS' in r['companies']:
            review = r.get('specification_review', {})
            lines.append(f"| [{r['title']}]({r['url']}) | {len(r['variants'])} | {review.get('summary', 'Detailed specification not reviewed.')} |")
    lines += ['', '## LeetCode title candidates', '', '| Hack2Hire | Category | Status | LeetCode |', '| --- | --- | --- | --- |']
    for r in bank['records']:
        o = r['leetcode_overlap']
        if o['candidates']:
            links = ', '.join(f"[{c['id']}: {c['title']}]({c['url']})" for c in o['candidates'])
            lines.append(f"| [{r['title']}]({r['url']}) | {r['category']} | {o['status']} | {links} |")
    lines += ['', '## Complete index', '', '| Problem | Category | Variants | Companies | Topics |', '| --- | --- | ---: | --- | --- |']
    for r in bank['records']:
        lines.append(f"| [{r['title'].replace('|', '/')} ]({r['url']}) | {r['category']} | {len(r['variants'])} | {', '.join(r['companies'])} | {', '.join(r.get('topics', []))} |")
    (DEST / 'REPORT.md').write_text('\n'.join(lines) + '\n')


def counts(records):
    return {'question_groups': len(records), 'variants': sum(len(r['variants']) for r in records),
            'categories': dict(sorted(Counter(r['category'] for r in records).items())),
            'overlap_status': dict(sorted(Counter(r['leetcode_overlap']['status'] for r in records).items())),
            'locked_groups': sum(r['anonymous_listing_locked'] is True for r in records),
            'content_status': dict(Counter(v['content_status'] for r in records for v in r['variants']))}


def fetch_bank():
    DEST.mkdir(parents=True, exist_ok=True)
    lc, lc_hash = get_json(LC_API)
    reference = lc_metadata(lc)
    matcher, records, receipts = Overlap(reference), [], []
    for kind in CATEGORIES:
        posts, requests = collect_category(kind)
        records.extend(build_record(post, matcher) for post in posts)
        receipts.extend(requests)
        print(kind, len(posts), flush=True)
    if len({r['uid'] for r in records}) != len(records):
        raise ValueError('Cross-category duplicate group identity')
    variants = [v['uid'] for r in records for v in r['variants']]
    if len(set(variants)) != len(variants):
        raise ValueError('Cross-group duplicate variant identity')
    apply_reviews(records)
    records.sort(key=lambda r: (r['category'], normalized(r['title']), r['uid']))
    bank = {'schema': 'gamma.external-question-bank.v1', 'source': 'hack2hire',
            'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
            'leetcode_metadata_records': len(reference),
            'content_scope': 'complete listing metadata; limited original public-specification summaries; no solutions',
            'counts': counts(records), 'records': records}
    (DEST / 'bank.json').write_text(json.dumps(bank, indent=2, ensure_ascii=False) + '\n')
    (DEST / 'leetcode-metadata.json').write_text(json.dumps(reference, indent=2, ensure_ascii=False) + '\n')
    (DEST / 'fetch-receipt.json').write_text(json.dumps({'requests': receipts,
            'leetcode_metadata': {'url': LC_API, 'response_sha256': lc_hash, 'records': len(reference)},
            'credentials_used': False, 'protected_payloads_opened': False,
            'solution_or_statement_payloads_opened': False}, indent=2) + '\n')
    write_report(bank)
    print(json.dumps(bank['counts'], indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['fetch', 'list', 'stats'])
    parser.add_argument('--company')
    parser.add_argument('--category', choices=[v[0] for v in CATEGORIES.values()])
    parser.add_argument('--overlap')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    if args.command == 'fetch':
        fetch_bank()
        return
    bank = json.loads((DEST / 'bank.json').read_text())
    rows = [r for r in bank['records'] if
            (not args.company or args.company.casefold() in [c.casefold() for c in r['companies']]) and
            (not args.category or r['category'] == args.category) and
            (not args.overlap or r['leetcode_overlap']['status'] == args.overlap)]
    if args.command == 'stats':
        print(json.dumps(counts(rows), indent=2))
    elif args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        for row in rows:
            print(f"{row['category']} | {row['title']} | {len(row['variants'])} variant(s) | {row['leetcode_overlap']['status']} | {row['url']}")


if __name__ == '__main__':
    main()
