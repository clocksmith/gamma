import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from .boundary_policy import authorize_before_open, validate_policy


def encode(value):
    return json.dumps(value, sort_keys=True).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class BoundaryPolicyTests(unittest.TestCase):
    def fixture(self):
        ids = ['leetcode:' + str(i) for i in range(1, 6)]  # Synthetic only.
        u = {'schema':'gamma.catalogue-universe.v1', 'eligible_problem_ids':ids,
             'protected_problem_ids':ids[2:4], 'metadata_sha256':'a'*64, 'eligibility_policy':'synthetic test'}
        closure = {'schema':'gamma.historical-key-closure-proof.v1', 'status':'review candidate',
                   'keys':['lc:third'], 'families':['third'], 'problem_ids':[ids[2]],
                   'known_uids_only':['doocs:3'], 'full815_uid_closure_reconstructed':False,
                   'witnesses':[{'key':'lc:third', 'family':'third', 'problem_id':ids[2],
                                 'membership_witnesses':['narrow_exclusion_key']}]}
        labels = ['previously_authorized_400', 'known_corpus_nonreserved_pending_independent_review',
                  'historical_reserved382', 'final100_exact_id_reserved', 'unresolved_global_identity_alias_metadata_only']
        c = {'schema':'gamma.all4081-boundary-classification-review.v1', 'new_source_access_authorized':False,
             'current_allowlist_unchanged':True, 'full_current4081_alias_closure_complete':False,
             'rows':[{'problem_id':pid, 'status':label, 'source_access_currently_authorized':i==0}
                     for i,(pid,label) in enumerate(zip(ids,labels))], 'counts':dict.fromkeys(labels,1)}
        raw = {'universe':encode(u), 'closure':encode(closure), 'classification':encode(c)}
        proof = {'schema':'gamma.boundary-metadata-receipt.v3', 'status':'review candidate',
                 'owner_published_index_keys':{}, 'historical_metadata_commit':'b'*40, 'proof':'reviewed subset theorem',
                 'premises':['synthetic'], 'source_payload_reads':0, 'statement_payload_reads':0, 'case_payload_reads':0,
                 'new_source_access_authorized':False, 'canonical_f625_recomputed':False,
                 'raw_a4a_index_entries_recomputed':False, 'metadata_input_refs':[], 'limits':[],
                 'private_outputs':[{'path':k+'.json','sha256':sha(raw[k]),'bytes':len(raw[k])} for k in ('closure','classification')],
                 'counts':{'all4081':5,'historical_reserved_keys':1,'historical_reserved_families':1,
                           'historical_reserved_numeric_ids':1,'known_exact_id_nonreserved':2,'currently_source_authorized':1,
                           'additional_exact_id_candidates':1,'unresolved_exterior_ids':1,'corpus_keys':3,'final100':1}}
        raw['proof'] = encode(proof)
        aliases = {'schema':'gamma.corpus-key-numeric-alias-map.v1','metadata_revision':3,
                   'to_universe_sha256':sha(raw['universe']),'proof_sha256':sha(raw['proof']),
                   'closure_sha256':sha(raw['closure']),'corpus_metadata_sha256':'c'*64,
                   'by_key':{'lc:first':ids[0],'lc:second':ids[1],'lc:third':ids[2]},
                   'known_corpus_keys':['lc:first','lc:second','lc:third'],'outside_corpus_reserved_keys':[],
                   'source_payload_reads':0,'case_payload_reads':0}
        raw['identity_aliases'] = encode(aliases)
        policy = {'schema':'gamma.all4081-source-access-policy.v2','metadata_revision':3,'population_size':5,'language_slots':10,
                  'universe_sha256':sha(raw['universe']),
                  'evidence_sha256':{k:sha(raw[k]) for k in ('proof','closure','classification','identity_aliases')},
                  'supersedes_policy_sha256':'d'*64,'authorized_existing_source_problem_ids':[ids[0]],
                  'authorized_source_acquisition_problem_ids':ids[:2],'known_protected_problem_ids':ids[2:4],
                  'unknown_problem_ids':ids[4:],'outside_authorized_count':3,'authority':'synthetic trusted operator',
                  'approval_scope':'prospective-exact-known-corpus-source-and-statement-acquisition',
                  'new_source_access_authorized':True,'source_publication_authorized':False,'case_access_authorized':False,
                  'qualification_changed':False,'current_serving_runtime_checked':False,'final100_membership_complete':True,
                  'historical382_key_closure_complete':True,'full4081_alias_closure_complete':False}
        raw['policy'] = encode(policy)
        return raw, {k:sha(v) for k,v in raw.items()}

    def mutate(self, raw, anchors, name, change):
        value = json.loads(raw[name]); change(value); raw[name] = encode(value); anchors[name] = sha(raw[name])
        if name not in ('policy','universe'):
            p = json.loads(raw['policy']); p['evidence_sha256'][name] = anchors[name]
            raw['policy'] = encode(p); anchors['policy'] = sha(raw['policy'])

    def test_authorizes_only_existing_and_reviewed_additional(self):
        raw, pins = self.fixture(); p = validate_policy(raw,pins)
        for pid in ('leetcode:1','leetcode:2'):
            for lang in ('python','javascript'):
                result = p.authorize(pid, language=lang)
                self.assertTrue(result['authorized']); self.assertTrue(result['requires_identity_bound_locator'])
                for flag in ('semantic_qualification_created','source_publication_authorized','case_access_authorized','current_serving_runtime_verified'):
                    self.assertIs(result[flag],False)
        self.assertEqual(p.existing,frozenset({'leetcode:1'}))

    def test_reserved_unknown_and_outside_universe_denied(self):
        raw,pins=self.fixture();p=validate_policy(raw,pins)
        for pid in ('leetcode:3','leetcode:4','leetcode:5','leetcode:6'):
            with self.subTest(pid=pid), self.assertRaises(PermissionError):p.authorize(pid,language='python')

    def test_invalid_identity_language_and_cases_denied(self):
        raw,pins=self.fixture();p=validate_policy(raw,pins)
        for pid in (None,1,True,[],{},'1','leetcode:01','leetcode:0','leetcode:-1','leetcode:１','leetcode:1\n','leetcode:1/../../x'):
            with self.subTest(pid=pid), self.assertRaises(PermissionError):p.authorize(pid,language='python')
        for lang in (None,[],True,'ruby'):
            with self.assertRaises(PermissionError):p.authorize('leetcode:1',language=lang)
        for kind in ('cases','tests','publication','training','serving',None,[]):
            with self.assertRaises(PermissionError):p.authorize('leetcode:1',language='python',payload_kind=kind)
        self.assertEqual(p.authorize('leetcode:1',language='python',payload_kind='statement')['payload_kind'],'statement')

    def test_every_external_hash_is_mandatory(self):
        for name in self.fixture()[0]:
            raw,pins=self.fixture();raw[name]+=b' '
            with self.subTest(name=name),self.assertRaises(ValueError):validate_policy(raw,pins)
        raw,pins=self.fixture();pins.pop('closure')
        with self.assertRaises(ValueError):validate_policy(raw,pins)

    def test_policy_cannot_confer_other_authority(self):
        for name in ('source_publication_authorized','case_access_authorized','qualification_changed','current_serving_runtime_checked','full4081_alias_closure_complete'):
            raw,pins=self.fixture();self.mutate(raw,pins,'policy',lambda p:p.update({name:True}))
            with self.subTest(name=name),self.assertRaises(ValueError):validate_policy(raw,pins)

    def test_reserved_and_unknown_cannot_be_added_to_allowlist(self):
        for pid in ('leetcode:3','leetcode:5'):
            raw,pins=self.fixture();self.mutate(raw,pins,'policy',lambda p:p['authorized_source_acquisition_problem_ids'].append(pid))
            with self.assertRaises(ValueError):validate_policy(raw,pins)

    def test_missing_duplicate_unknown_fields_and_boolean_counts_rejected(self):
        changes=[lambda p:p.update(extra='source payload'),lambda p:p.pop('authority'),
                 lambda p:p.update(population_size=True),lambda p:p['authorized_existing_source_problem_ids'].append('leetcode:1'),
                 lambda p:p.update(new_source_access_authorized=1)]
        for change in changes:
            raw,pins=self.fixture();self.mutate(raw,pins,'policy',change)
            with self.assertRaises(ValueError):validate_policy(raw,pins)
        raw,pins=self.fixture();raw['policy']=raw['policy'][:-1]+b',"schema":"duplicate"}';pins['policy']=sha(raw['policy'])
        with self.assertRaises(ValueError):validate_policy(raw,pins)

    def test_identity_redirect_and_proof_rebinding_rejected(self):
        changes=[lambda a:a['by_key'].update({'lc:first':'leetcode:5'}),
                 lambda a:a.update(proof_sha256='0'*64),lambda a:a.update(to_universe_sha256='0'*64)]
        for change in changes:
            raw,pins=self.fixture();self.mutate(raw,pins,'identity_aliases',change)
            with self.assertRaises(ValueError):validate_policy(raw,pins)

    def test_proof_and_classification_are_not_replaceable_by_counts(self):
        raw,pins=self.fixture();self.mutate(raw,pins,'proof',lambda p:p.update(private_outputs=[]))
        with self.assertRaises(ValueError):validate_policy(raw,pins)
        raw,pins=self.fixture();self.mutate(raw,pins,'classification',lambda c:c['rows'].pop())
        with self.assertRaises(ValueError):validate_policy(raw,pins)

    def test_alias_and_classification_scalar_types_are_strict(self):
        for change in (lambda a:a.update(metadata_revision=3.0), lambda a:a.update(corpus_metadata_sha256='not a digest'), lambda a:a.update(source_payload_reads=False)):
            raw,pins=self.fixture();self.mutate(raw,pins,'identity_aliases',change)
            with self.assertRaises(ValueError):validate_policy(raw,pins)

    def test_verified_snapshot_copies_no_mutable_input_authority(self):
        raw,pins=self.fixture();p=validate_policy(raw,pins)
        raw.clear();pins.clear()
        self.assertEqual(p.authorized,frozenset({'leetcode:1','leetcode:2'}))
        with self.assertRaises(AttributeError):p.authorized.add('leetcode:5')

    def test_preopen_rechecks_live_metadata_and_never_follows_payload_path(self):
        raw,pins=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            paths={k:str(Path(directory)/k) for k in raw}
            for k,p in paths.items():Path(p).write_bytes(raw[k])
            value=authorize_before_open('leetcode:2',paths,pins,language='javascript')
            self.assertTrue(value['authorized'])
            Path(paths['policy']).write_bytes(raw['policy']+b' ')
            with self.assertRaises(ValueError):authorize_before_open('leetcode:2',paths,pins,language='javascript')
            self.assertEqual(set(Path(directory).iterdir()),{Path(x) for x in paths.values()})


if __name__=='__main__':unittest.main()
