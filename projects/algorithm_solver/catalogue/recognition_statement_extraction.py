"""Conservative, source-bound statement extraction for private recognition candidates.

Only authorized definition text enters the six-field schema. Public examples,
preformatted blocks, hints and solution sections are excluded. This deterministic
projection is not an independent semantic review or implementation qualification.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

from . import boundary_policy
from . import recognition_description_schema as schema
from .recognition_documents import authority_bytes, pinned_metadata


class DefinitionBlocks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.pending = []
        self.skip = 0
        self.preformatted_blocks = 0
        self.images = 0
        self.inline_math = []

    def flush(self):
        value = re.sub(r'\s+', ' ', ''.join(self.pending)).strip()
        self.pending = []
        if value:
            self.blocks.append(value)

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'pre'):
            self.flush()
            self.skip += 1
            if tag == 'pre':
                self.preformatted_blocks += 1
            return
        if self.skip:
            return
        if tag == 'img':
            self.flush()
            self.images += 1
            self.blocks.append({'image': True})
            return
        if tag in ('p', 'li', 'ul', 'ol', 'div', 'section', 'h1', 'h2', 'h3', 'h4', 'br', 'tr'):
            self.flush()
        elif tag in ('td', 'th'):
            self.pending.append(' | ')
        elif tag == 'sup':
            self.pending.append('^(')
            self.inline_math.append('sup')
        elif tag == 'sub':
            self.pending.append('_(')
            self.inline_math.append('sub')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'pre'):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in ('p', 'li', 'ul', 'ol', 'div', 'section', 'h1', 'h2', 'h3', 'h4', 'tr'):
            self.flush()
        elif tag in ('sup', 'sub'):
            if not self.inline_math or self.inline_math.pop() != tag:
                raise ValueError('unbalanced mathematical markup')
            self.pending.append(')')

    def handle_data(self, value):
        if not self.skip:
            self.pending.append(value)


def sections(html):
    parser = DefinitionBlocks()
    parser.feed(html)
    parser.close()
    parser.flush()
    if parser.inline_math or parser.skip:
        raise ValueError('unclosed markup requires explicit review')
    groups = {'definition': [], 'constraints': [], 'optional_follow_up': []}
    excluded = {'example_blocks': 0, 'hint_or_solution_blocks': 0,
                'preformatted_blocks': parser.preformatted_blocks, 'images': parser.images, 'definition_images': 0}
    state = 'definition'
    for index, block in enumerate(parser.blocks):
        if isinstance(block, dict) and block == {'image': True}:
            if state in groups:
                excluded['definition_images'] += 1
            continue
        clean = re.sub(r'^[\s#*]+', '', block)
        if state == 'excluded':
            excluded['hint_or_solution_blocks'] += 1
            continue
        if re.match(r'(?i)^constraints(?:\s*:|\s*$)', clean):
            state = 'constraints'
            rest = re.sub(r'(?i)^constraints\s*:?\s*', '', clean)
            if rest:
                groups[state].append({'text': rest, 'block': index})
            continue
        if re.match(r'(?i)^follow[ -]?up\s*:', clean):
            state = 'optional_follow_up'
            groups[state].append({'text': clean, 'block': index})
            continue
        if re.match(r'(?i)^(?:examples?(?:\s*\d*)?(?:\s*:|\s*$)|input\s*:|output\s*:|explanation\s*:)', clean):
            state = 'examples'
        elif re.match(r'(?i)^(?:hints?(?:\s*\d*)?|solutions?|approach(?:\s*\d*)?|editorial)(?:\s*:|\s*$)', clean):
            state = 'excluded'
        if state == 'examples':
            excluded['example_blocks'] += 1
        elif state == 'excluded':
            excluded['hint_or_solution_blocks'] += 1
        else:
            groups[state].append({'text': block, 'block': index})
    if not groups['definition']:
        raise ValueError('no usable definition outside examples/hints/solutions')
    return groups, excluded


def _field(clauses, source_sha256):
    if not clauses:
        return schema.unknown_field()
    return {'status': 'partial', 'value': [r['text'] for r in clauses],
            'evidence': [{'source_sha256': source_sha256, 'selector': 'html.blocks[' + str(r['block']) + ']',
                          'evidence_class': 'authorized-statement-extraction'} for r in clauses],
            'unknown_reason': None}


def normalize_statement(html, row, *, policy_sha256):
    """Keep original clauses. Classification is conservative, not new semantics."""
    groups, excluded = sections(html)
    definition = groups['definition']
    selected = {name: [] for name in schema.FIELDS}
    selected['constraints'] = list(groups['constraints'])
    selected['distinguishing_details'] = list(groups['optional_follow_up'])
    for clause in definition:
        text = clause['text']
        if re.search(r'(?i)\bin[ -]place\b|\b(?:do not|must not|without) modify(?:ing)? (?:the )?(?:input|original)', text):
            selected['effects'].append(clause)
        elif re.match(r'(?i)^(?:return\b|print\b|output\b|your (?:function|method) (?:should|must) return\b)', text):
            selected['output'].append(clause)
        elif re.match(r'(?i)^(?:given\b|you are given\b|you have\b|there (?:is|are)\b|the input\b)', text):
            selected['input'].append(clause)
        elif re.match(r'(?i)^(?:find\b|determine\b|calculate\b|compute\b|design\b|implement\b|your task\b|you (?:must|need to|should)\b)', text):
            selected['intent'].append(clause)
        elif re.match(r'(?i)^(?:it is guaranteed\b|it is guaranteed that\b|you may assume\b|you can assume\b)', text):
            selected['constraints'].append(clause)
        else:
            selected['distinguishing_details'].append(clause)
    # Some definitions put the output directive in their initial input paragraph.
    # Preserve that whole exact clause rather than fabricate a result type or
    # mistake a hypothetical return-to-location operation for an API return.
    output_positions = {r['block'] for r in selected['output']}
    directive = re.compile(r'(?i)(?:^|[.;]\s*|,\s*|\band\s+|\bthen\s+|\byou (?:must|should|may|can)\s+)return\b')
    for clause in definition:
        if clause['block'] not in output_positions and directive.search(clause['text']):
            selected['output'].append(clause)
            output_positions.add(clause['block'])
    # A stated return clause is a goal as well, but never invent one from source.
    if not selected['intent']:
        selected['intent'] = selected['output'][:1] or definition[:1]
    fields = {name: _field(selected[name], row['sha256']) for name in schema.FIELDS}
    result = {'schema': schema.SCHEMA, 'problem_id': row['problem_id'], 'title': row['title'],
        'aliases': row['aliases'], 'fields': fields, 'evidence_class': 'authorized-statement-extraction',
        'permission': {'policy_sha256': policy_sha256, 'payload_kind': 'statement',
                       'scope': 'private-development-description', 'publication': 'not-granted-by-acquisition'},
        'provenance': {'source_sha256': row['sha256'], 'source_kind': 'authorized-statement',
                       'source_locator': row['original_path'],
                       'transformation': 'HTML definition/constraints only; exact clauses; examples/preformatted/hints/solutions excluded'},
        'semantic_review_status': 'needs-independent-semantic-review'}
    return result, {'excluded': excluded, 'section_clause_counts': {k: len(v) for k, v in groups.items()},
                    'field_clause_counts': {k: len(v) for k, v in selected.items()},
                    'optional_follow_up_is_not_mandatory': True,
                    'effects_inferred_from_solutions': False,
                    'explicit_reviewer_attention': ['image-dependent semantics are not inferred'] if excluded['definition_images'] else []}


def build_batch(plan, *, source_root):
    gate = pinned_metadata(plan['boundary_gate'])
    boundary = boundary_policy.validate_policy({k: Path(v).read_bytes() for k, v in gate['artifact_paths'].items()},
                                                gate['trusted_hashes'])
    if boundary.policy_sha256 != plan['expected_policy_sha256']:
        raise ValueError('current statement authority differs from planned policy')
    aliases_raw = Path(gate['artifact_paths']['identity_aliases']).read_bytes()
    if hashlib.sha256(aliases_raw).hexdigest() != gate['trusted_hashes']['identity_aliases']:
        raise ValueError('current alias pin differs')
    aliases = json.loads(aliases_raw)['by_key']
    rows = plan['rows']
    if len({r['problem_id'] for r in rows}) != len(rows):
        raise ValueError('duplicate statement batch identity')
    descriptions, audit = [], []
    for row in rows:
        pid = row['problem_id']
        if (not boundary_policy._ID.fullmatch(pid) or Path(row['path']).name != pid.split(':')[1] + '.md'
                or Path(row['original_path']).name != pid.split(':')[1] + '.md'
                or any(aliases.get(key) != pid for key in row['aliases'])):
            raise ValueError('exact statement identity/locator/alias binding required')
        authorization = boundary_policy.authorize_before_open(pid, gate['artifact_paths'], gate['trusted_hashes'],
                                                              language='javascript', payload_kind='statement')
        raw = authority_bytes({'path': row['path'], 'sha256': row['sha256']}, [str(Path(source_root))])
        if len(raw) != row['bytes']:
            raise ValueError('statement byte count differs')
        description, detail = normalize_statement(raw.decode('utf-8'), row, policy_sha256=boundary.policy_sha256)
        checked = schema.validate(description, authorized_ids=boundary.authorized, exact_aliases=aliases,
                                  expected_policy_sha256=boundary.policy_sha256)
        descriptions.append(description)
        audit.append({'problem_id': pid, 'source_sha256': row['sha256'], 'source_bytes': len(raw),
                      'authorization': authorization, 'validation': checked, **detail})
    return {'schema': 'gamma.recognition-description-batch.v2', 'batch_id': plan['batch_id'],
            'plan_sha256': schema.digest(plan),
            'builder_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'schema_module_sha256': hashlib.sha256(Path(schema.__file__).read_bytes()).hexdigest(),
            'descriptions': descriptions, 'read_audit': audit,
            'summary': schema.summarize(descriptions), 'protected_payload_reads': 0,
            'source_or_case_file_reads': 0, 'encoder_executed': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    plan = pinned_metadata({'path': args.plan, 'sha256': args.plan_sha256})
    result = build_batch(plan, source_root=args.source_root)
    with Path(args.output).open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
