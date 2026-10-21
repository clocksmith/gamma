"""Small exact-literal candidate/energy interface. Never executes source programs."""
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Protocol
import hashlib
import importlib.util
from itertools import zip_longest
import json
import math
import statistics
import time

ROOT = Path(__file__).resolve().parent
LITERALS = ROOT.parent
CORE = LITERALS/'joint-v1/reachable_core.py'
CORE_SHA = '74b69275995f068ab227cdbc895984c2aa14ed98a971ff3d86bda14264ca7899'
CODEC = LITERALS/'readable-v1/literal_codec.py'
CODEC_SHA = '64585df01200488e834540986f8ef99703dd99cecc76808a2b9654e1ea318afe'
GATES = ('output', 'mutation', 'alias', 'numeric', 'complexity', 'domain')
TRACKS = ('compression', 'readable')

class Ineligible(ValueError):
    pass

def raw_hash(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def identity(value):
    return raw_hash(canonical(value))

def require(condition, message):
    if not condition:
        raise Ineligible(message)

def pinned_module(name, path, expected):
    require(raw_hash(path.read_bytes()) == expected, 'dependency hash changed')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

core = pinned_module('gamma_energy_exact_core', CORE, CORE_SHA)
codec = pinned_module('gamma_energy_exact_codec', CODEC, CODEC_SHA)

@dataclass(frozen=True)
class CandidatePiece:
    piece_id: str
    text: str
    track: str
    provenance: tuple[str, ...]
    contract_refs: tuple[str, ...] = ()
    kind: str = 'candidate_piece'

@dataclass(frozen=True)
class PartialAssembly:
    problem_id: str
    source_variant: str
    piece_ids: tuple[str, ...]
    prefix_sha256: str
    open_holes: tuple[str, ...]
    control_bits: int = 0
    kind: str = 'partial_assembly'

@dataclass(frozen=True)
class VocabularyState:
    piece_ids: tuple[str, ...]
    choices: tuple[tuple[str, str], ...]
    width: int
    track: str
    kind: str = 'vocabulary_solution_state'

def state_identity(state):
    return identity(asdict(state))

def load_dataset(path, expected_sha):
    raw = Path(path).read_bytes()
    require(raw_hash(raw) == expected_sha, 'dataset identity changed')
    data = json.loads(raw)
    validate_dataset(data)
    return data

def validate_dataset(data):
    require(data['schema'] == 'gamma.energy-dataset.v1', 'dataset schema')
    require(data['evidence_class'] in ('synthetic_fixture_only', 'exposed-development'), 'unsupported evidence class')
    require(data['reviewed_manifest'] is True, 'coordinator-reviewed manifest required')
    require(data['split']['exposed_development'] is True, 'this interface cannot claim untouched evaluation')
    require(data['split']['frozen_before_scoring'] is True, 'split not frozen')
    assignments = data['split']['families']
    require(set(assignments.values()) <= {'train', 'validation', 'test'}, 'unknown split')
    protected = data['excluded']
    require(set(protected) == {'problem_ids', 'family_ids', 'source_sha256', 'aliases'}, 'exclusion schema')
    seen_sources, seen_problems, seen_aliases, problem_contracts = {}, {}, {}, {}
    for key, variant in data['variants'].items():
        require(key == variant['id'] and variant['language'] in ('javascript', 'python'), 'variant identity/language')
        require(variant['problem_id'] not in protected['problem_ids'], 'protected problem')
        family = variant['family_id']
        require(family in assignments and family not in protected['family_ids'], 'missing or protected family')
        identities = {variant['problem_id'], *variant['aliases']}
        require(not (identities & (set(protected['aliases']) | set(protected['problem_ids']))), 'protected alias or canonical identity')
        for alias in identities:
            require(isinstance(alias,str) and bool(alias), 'invalid alias')
            require(alias not in seen_aliases or seen_aliases[alias]==family, 'alias split leakage')
            seen_aliases[alias]=family
        sha = raw_hash(variant['source'].encode())
        require(sha == variant['source_sha256'] and sha not in protected['source_sha256'], 'source hash/protection')
        require(variant['problem_id'] not in seen_problems or seen_problems[variant['problem_id']] == family, 'problem split leakage')
        require(sha not in seen_sources or seen_sources[sha] == family, 'source split leakage')
        seen_sources[sha], seen_problems[variant['problem_id']] = family, family
        require(variant['implicit_code'] is False, 'hidden source injection')
        require(variant['contract_id'] in data['contracts'], 'unknown contract')
        contract = data['contracts'][variant['contract_id']]
        require(contract['problem_id'] == variant['problem_id'] and contract['language'] == variant['language'], 'contract target differs')
        for gate in GATES:
            require(isinstance(contract[gate], str) and bool(contract[gate]), 'missing effect/domain contract')
        require(variant['contract_sha256'] == identity(contract), 'contract identity differs')
        target = (variant['problem_id'], variant['language'])
        require(target not in problem_contracts or problem_contracts[target] == variant['contract_sha256'], 'source alternatives have different contracts')
        problem_contracts[target] = variant['contract_sha256']
        for span in variant['helper_spans']:
            require(type(span['start']) is int and type(span['end']) is int and 0 <= span['start'] < span['end'] <= len(variant['source']), 'helper span invalid')
            require(raw_hash(variant['source'][span['start']:span['end']].encode()) == span['sha256'], 'helper not included in source')
        spans = sorted((s['start'], s['end']) for s in variant['helper_spans'])
        require(all(a[1] <= b[0] for a,b in zip(spans,spans[1:])), 'overlapping helper accounting')
        for field in ('operand_bits', 'control_bits'):
            require(type(variant[field]) is int and variant[field] >= 0, 'uncounted operand/control costs')
        require(variant['operand_bits']==variant['control_bits']==0, 'v1 flat literals have no operand/control side channel; use a separately implemented charged representation')
    return True

def qualification(data, variant):
    qid = variant['qualification_id']
    require(qid in data['qualifications'], 'missing qualification envelope')
    receipt = data['qualifications'][qid]
    fields = {'source_sha256','contract_sha256','status','gates','evidence_class'}
    fields |= ({'independent_reviewed','tests_passed','tests_total','runtime_sha256','proof_files'} if data['evidence_class']=='exposed-development' else {'candidate_execution'})
    require(fields <= receipt.keys(), 'qualification envelope fields missing')
    require(receipt['source_sha256'] == variant['source_sha256'] and receipt['contract_sha256'] == variant['contract_sha256'], 'qualification not source/contract bound')
    require(receipt['status'] == 'passed' and all(receipt['gates'].get(k) is True for k in GATES), 'qualification gate failed')
    require(receipt['evidence_class'] == data['evidence_class'], 'qualification evidence class differs')
    if data['evidence_class'] == 'exposed-development':
        require(receipt['independent_reviewed'] is True and receipt['tests_passed'] == receipt['tests_total'] and type(receipt['tests_total']) is int and receipt['tests_total'] > 0, 'incomplete qualification')
        runtime=receipt['runtime_sha256']
        require(bool(receipt['proof_files']) and isinstance(runtime,str) and len(runtime)==64 and all(c in '0123456789abcdef' for c in runtime), 'missing execution evidence')
        for pin in receipt['proof_files']:
            path = Path(pin['path'])
            require(path.is_absolute() and not any(p.is_symlink() for p in (path, *path.parents)), 'qualification proof symlink/relative path')
            try:
                digest = raw_hash(path.read_bytes())
            except OSError as error:
                raise Ineligible('qualification proof unavailable') from error
            require(digest == pin['sha256'], 'qualification proof changed')
    else:
        require(receipt['candidate_execution'] is False, 'synthetic fixture misclassified')
    return receipt

def eligible(data, pieces, state):
    validate_dataset(data)
    require(isinstance(state, VocabularyState), 'partial/piece object is not a solved state')
    require(state.width in (6, 7, 8) and state.track in TRACKS, 'width/track')
    require(0 < len(state.piece_ids) <= 2**state.width and len(set(state.piece_ids)) == len(state.piece_ids), 'dictionary cap/duplicates')
    require(len(state.choices) == len(dict(state.choices)) and bool(state.choices), 'choice identity')
    selected = {}
    for problem, key in state.choices:
        require(key in data['variants'], 'unknown source variant')
        variant = data['variants'][key]
        require(variant['problem_id'] == problem, 'choice problem differs')
        qualification(data, variant)
        selected[problem] = variant
    require(len({v['language'] for v in selected.values()}) == 1, 'mixed language state')
    strings = []
    for key in state.piece_ids:
        require(key in pieces, 'unknown piece')
        piece = pieces[key]
        require(piece.kind == 'candidate_piece' and piece.track == state.track and bool(piece.text), 'piece track/empty')
        require(key == raw_hash(piece.text.encode()), 'piece identity differs')
        require(piece.provenance and all(p in data['variants'] for p in piece.provenance), 'piece provenance missing')
        require(all(piece.text in data['variants'][p]['source'] for p in piece.provenance), 'piece is not an exact occurrence')
        require(not any(piece.text == v['source'] for v in data['variants'].values()), 'whole-program piece')
        require(all(ref in data['contracts'] for ref in piece.contract_refs), 'unknown component contract reference')
        strings.append(piece.text)
    require(len(set(strings)) == len(strings), 'duplicate exact string')
    return selected, strings

def exact_measure(data, pieces, state):
    selected, strings = eligible(data, pieces, state)
    vocab = core.order(strings, ())
    binary = [s.encode() for s in vocab]
    dictionary = b'LTD1' + len(binary).to_bytes(4, 'big') + b''.join(len(s).to_bytes(4, 'big') + s for s in binary)
    rows, owners = [], {s: set() for s in vocab}
    for problem, variant in sorted(selected.items()):
        text = variant['source']
        sequence = core.segment(text, core.trie(vocab))
        require(sequence is not None, 'unreachable selected source')
        require(core.minimum_count(text, vocab) == len(sequence), 'independent DP mismatch')
        packet = codec.packet(sequence, state.width, dictionary)
        codec.verify_packet(packet, dictionary, binary, text.encode())
        for i in set(sequence):
            owners[vocab[i]].add(problem)
        require(variant['operand_bits'] == variant['control_bits'] == 0, 'flat-literal side channel unsupported')
        rows.append({'problem_id': problem, 'variant_id': variant['id'], 'source_sha256': variant['source_sha256'],
                     'qualification_id': variant['qualification_id'], 'source_bytes': len(text.encode()),
                     'helper_bytes': sum(len(text[s['start']:s['end']].encode()) for s in variant['helper_spans']),
                     'selections': len(sequence), 'payload_bits': state.width*len(sequence),
                     'framing_bits': 328, 'literal_padding_bits': 8*(len(packet)-41)-state.width*len(sequence),
                     'operand_bits': variant['operand_bits'], 'control_bits': variant['control_bits'],
                     'extra_padding_bits': 0, 'packet_bytes': len(packet),
                     'character_selections': sum(len(vocab[i]) == 1 for i in sequence),
                     'sequence': sequence, 'packet_sha256': raw_hash(packet)})
    counts = [r['selections'] for r in rows]
    packet_bytes = sum(r['packet_bytes'] for r in rows)
    return {'state_id': state_identity(state), 'evidence_class': data['evidence_class'],
            'coverage': len(rows), 'denominator': len(state.choices), 'rows': rows,
            'selections': sum(counts), 'median': statistics.median(counts), 'p95': sorted(counts)[math.ceil(.95*len(counts))-1], 'worst': max(counts),
            'input_bits': packet_bytes*8, 'dictionary_bytes': len(dictionary), 'dictionary_utf8_bytes': sum(map(len,binary)),
            'packet_bytes': packet_bytes, 'package_bits': (len(dictionary)+packet_bytes)*8,
            'decoder_bytes': CODEC.stat().st_size, 'package_with_decoder_bits': (len(dictionary)+packet_bytes+CODEC.stat().st_size)*8,
            'entries': len(vocab), 'unused_capacity': 2**state.width-len(vocab),
            'reused_entries': sum(len(v)>1 for v in owners.values()),
            'reused_noncharacter_entries': sum(len(v)>1 and len(k)>1 for k,v in owners.items()),
            'character_selections': sum(r['character_selections'] for r in rows),
            'dictionary_sha256': raw_hash(dictionary), 'whole_program_entries': 0}

def features(data, pieces, state):
    selected, strings = eligible(data, pieces, state)
    source_bytes = sum(len(v['source'].encode()) for v in selected.values())
    reuse = sum(len({p for p,v in selected.items() if s in v['source']})>1 for s in strings)
    return {'entries': len(strings), 'dictionary_utf8_bytes': sum(len(s.encode()) for s in strings),
            'source_bytes': source_bytes, 'multi_problem_occurrences': reuse,
            'width': state.width, 'problems': len(selected),
            'character_entries': sum(len(s)==1 for s in strings)}

def mine_pieces(data, variant_ids, track, human_seeds=()):
    require(track in TRACKS, 'track')
    variants = {k:data['variants'][k] for k in sorted(variant_ids)}
    texts = set()
    for variant in variants.values():
        source = variant['source']
        texts.update(source.splitlines(keepends=True))
        if track == 'compression':
            texts.update(source)
            for width in (2,4,8):
                texts.update(source[i:i+width] for i in range(len(source)-width+1))
    for text in human_seeds:
        require(text and any(text in v['source'] for v in variants.values()), 'human seed absent from sources')
        texts.add(text)
    whole = {v['source'] for v in data['variants'].values()}
    result = {}
    for text in sorted(texts-whole-{''}):
        provenance = tuple(k for k,v in variants.items() if text in v['source'])
        # Keep one-character coverage controls but recurrence mining counts problems, not variants.
        support = {variants[k]['problem_id'] for k in provenance}
        if len(support)>1 or text in human_seeds or len(text)==1 or track=='readable':
            key=raw_hash(text.encode())
            result[key]=CandidatePiece(key,text,track,provenance)
    return result

def validate_partial(data, pieces, state, vocabulary):
    require(isinstance(state, PartialAssembly), 'partial schema')
    require(isinstance(vocabulary,VocabularyState) and vocabulary.width in (6,7,8), 'partial vocabulary schema')
    require(all(isinstance(hole,str) and hole for hole in state.open_holes), 'partial hole annotation')
    require(type(state.control_bits) is int and state.control_bits>=0, 'partial control accounting')
    require(state.source_variant in data['variants'], 'unknown partial target')
    target=data['variants'][state.source_variant]
    require(target['problem_id']==state.problem_id, 'partial problem differs')
    require(all(key in vocabulary.piece_ids and key in pieces for key in state.piece_ids), 'partial piece not available')
    prefix=''.join(pieces[key].text for key in state.piece_ids)
    require(raw_hash(prefix.encode())==state.prefix_sha256 and target['source'].startswith(prefix), 'partial prefix differs')
    return {'kind':'partial_assembly','complete':not state.open_holes and prefix==target['source'],
            'qualified_solution':False,'selected_bits':len(state.piece_ids)*vocabulary.width,
            'control_bits':state.control_bits,'remaining_bytes':len(target['source'][len(prefix):].encode())}

def neighbors(data, pieces, state, limit=128):
    require(type(limit) is int and limit>0, 'neighborhood bound')
    validate_dataset(data)
    emitted=set();count=0
    current=set(state.piece_ids);available=sorted(set(pieces)-current)
    additions=(('add',(),(key,),None) for key in available)
    deletions=(('delete',(key,),(),None) for key in sorted(current))
    swaps=(('swap',(old,),(new,),None) for old in sorted(current) for new in available)
    rewrites=(('rewrite',(),(),(problem,key)) for problem,old in state.choices for key,v in sorted(data['variants'].items()) if v['problem_id']==problem and key!=old and v['language']==data['variants'][old]['language'] and v['contract_sha256']==data['variants'][old]['contract_sha256'])
    # Deterministic round-robin prevents a finite prefix of additions starving rewrites.
    moves=(move for group in zip_longest(additions,deletions,swaps,rewrites) for move in group if move is not None)
    for kind,remove,add,rewrite in moves:
        ids=tuple(sorted(current-set(remove)|set(add)))
        if not ids or len(ids)>2**state.width:
            continue
        choices=dict(state.choices)
        if rewrite:
            choices[rewrite[0]]=rewrite[1]
        child=VocabularyState(ids,tuple(sorted(choices.items())),state.width,state.track)
        sha=state_identity(child)
        if sha in emitted:
            continue
        emitted.add(sha);count+=1
        yield {'kind':kind,'remove':remove,'add':add,'rewrite':rewrite},child
        if count>=limit:
            break

class LearnedEnergyScorer(Protocol):
    model_id: str
    model_bytes: int
    scorer_version: str
    scorer_seed: int
    scorer_artifact_sha256: str
    trained_source_hashes: tuple[str, ...]
    training_manifest_sha256: str
    def energy(self, values: dict[str, int]) -> float: ...

def compare(data, pieces, states, learned: LearnedEnergyScorer | None, *, max_evaluations, max_cpu_seconds, evaluation_split='validation'):
    validate_dataset(data)
    require(type(max_evaluations) is int and max_evaluations>0 and 0<max_cpu_seconds<=20, 'comparison budget')
    require(evaluation_split in ('validation','test'), 'comparison split')
    if learned is not None:
        require(isinstance(learned.model_id,str) and bool(learned.model_id) and type(learned.model_bytes)is int and learned.model_bytes>=0, 'model identity/cost')
        require(isinstance(learned.scorer_version,str) and bool(learned.scorer_version) and type(learned.scorer_seed)is int, 'scorer version/seed')
        artifact=learned.scorer_artifact_sha256
        require(isinstance(artifact,str) and len(artifact)==64 and all(c in '0123456789abcdef' for c in artifact), 'scorer artifact identity')
        hashes={v['source_sha256'] for v in data['variants'].values() if data['split']['families'][v['family_id']]=='train'}
        require(set(learned.trained_source_hashes)<=hashes, 'training leakage/unregistered training source')
        require(learned.training_manifest_sha256==identity({'dataset_id':data['corpus_id'],'split':data['split'],'trained_source_hashes':sorted(learned.trained_source_hashes)}),'training manifest identity differs')
    start=time.process_time();records=[];rejected=[];oracle_seconds=score_seconds=0.0;attempts=0;matched=None
    for state in states:
        if attempts>=max_evaluations or time.process_time()-start>=max_cpu_seconds:
            break
        attempts+=1
        try:
            require(isinstance(state,VocabularyState),'only complete vocabulary/source states can be scored')
            comparison_key=(state.width,state.track,tuple(sorted(p for p,_ in state.choices)),tuple(sorted((p,data['variants'][k]['language'],data['variants'][k]['contract_sha256']) for p,k in state.choices)))
            if matched is None:
                matched=comparison_key
            require(comparison_key==matched,'unmatched width/track/problem/language/contract set')
            for _, key in state.choices:
                require(data['split']['families'][data['variants'][key]['family_id']]==evaluation_split,'comparison split mixing')
            allowed_provenance = {'train','validation'}
            for key in state.piece_ids:
                require(key in pieces, 'unknown piece')
                require(all(data['split']['families'][data['variants'][p]['family_id']] in allowed_provenance for p in pieces[key].provenance), 'test-derived candidate leakage')
            t=time.process_time();measure=exact_measure(data,pieces,state);oracle_seconds+=time.process_time()-t
            values=features(data,pieces,state)
        except (Ineligible, KeyError) as error:
            rejected.append({'state_id':state_identity(state),'reason':str(error),'energy_called':False})
            continue
        prediction=None
        if learned is not None:
            t=time.process_time();prediction=learned.energy(values);score_seconds+=time.process_time()-t
            if type(prediction) not in (int,float) or not math.isfinite(prediction):
                raise ValueError('nonfinite learned energy; comparison invalid')
        records.append({'state_id':state_identity(state),'state':asdict(state),'features':values,
                        'labels':measure,'predicted_energy':prediction})
    order=sorted(records,key=lambda r:(r['labels']['package_bits'],r['labels']['input_bits'],r['state_id']))
    predicted=sorted(records,key=lambda r:(r['predicted_energy'],r['state_id'])) if learned else []
    return {'schema':'gamma.energy-comparison.v1','evidence_class':data['evidence_class'],
            'model_id':learned.model_id if learned else None,'model_bytes':learned.model_bytes if learned else 0,
            'scorer_version':learned.scorer_version if learned else None,
            'scorer_seed':learned.scorer_seed if learned else None,
            'scorer_artifact_sha256':learned.scorer_artifact_sha256 if learned else None,
            'scorer_supplied':learned is not None,'training_performed':False,'candidate_programs_executed':0,
            'learned_scorer_calls':len(records) if learned else 0,
            'evaluation_split':evaluation_split,
            'matched_width_track_problems':matched,
            'budget':{'max_evaluations':max_evaluations,'max_cpu_seconds':max_cpu_seconds},
            'exact_evaluation_attempts':attempts,'eligible':len(records),'rejected':rejected,
            'oracle_cpu_seconds':oracle_seconds,'scorer_cpu_seconds':score_seconds,
            'elapsed_cpu_seconds':time.process_time()-start,'exact_best':order[0]['state_id'] if order else None,
            'best_coverage':order[0]['labels']['coverage'] if order else 0,
            'coverage_denominator':len(matched[2]) if matched else 0,
            'predicted_best':predicted[0]['state_id'] if predicted else None,
            'top1_package_bit_regret':predicted[0]['labels']['package_bits']-order[0]['labels']['package_bits'] if predicted else None,
            'records':records,'limitations':['Offline ranking comparison: all eligible proposals receive exact cost evaluation.','No search-speed, neural-training, correctness or generalization result.']}
