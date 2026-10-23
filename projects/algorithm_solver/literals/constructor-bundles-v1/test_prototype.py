"""Synthetic exact codec/decoder and admission-barrier checks; no corpus IO."""
import itertools
import unittest
import prototype as p
import optimizer
c=p.codec

class BundleTests(unittest.TestCase):
    def test_both_constructor_families_have_strict_all_operand_complementarity(self):
        texts,nodes,initial,banned,_=p.counterexample()
        base=p.evaluate_bundle(texts,nodes,initial,[],[],banned)
        self.assertEqual(base['selections'],24)
        for family in ('prefix','identifier'):
            node=next(n for n in nodes['0'][family] if n['key'] and texts['0'][n['start']:n['end']]=='Math.max(longAlpha,longBeta)')
            bundle=[node['key'],c.literal('longAlpha'),c.literal('longBeta')]
            for size in range(3):
                for subset in itertools.combinations(bundle,size):
                    trial=p.evaluate_bundle(texts,nodes,initial,subset,[],banned)
                    self.assertEqual(trial['selections'],24)
                    self.assertEqual(trial['constructor_codes'],0)
            complete=p.evaluate_bundle(texts,nodes,initial,bundle,[],banned)
            self.assertEqual(complete['selections'],23);self.assertEqual(complete['constructor_codes'],1)
            self.assertEqual(complete['argument_codes'],2)
            self.assertEqual(optimizer.used_operand_literals(complete),{c.literal('longAlpha'),c.literal('longBeta')})
            self.assertEqual(c.decode_many(complete['keys'],complete['rows']),texts)
            self.assertEqual(complete['package_bytes'],complete['dictionary_bytes']+4*41+23)
            # The mechanism saves one selection but does not get dictionary
            # metadata for free; this fixture does not establish readiness.
            self.assertGreater(complete['package_bytes'],base['package_bytes'])

    def test_atomic_install_at_256_slots_preserves_mandatory_characters(self):
        texts,nodes,initial,banned,fillers=p.counterexample(True);self.assertEqual(len(initial),256)
        node=next(n for n in nodes['0']['prefix'] if n['key'] and texts['0'][n['start']:n['end']]=='Math.max(longAlpha,longBeta)')
        bundle=[node['key'],c.literal('longAlpha'),c.literal('longBeta')]
        for size in (1,2):
            for subset in itertools.combinations(bundle,size):
                self.assertEqual(p.evaluate_bundle(texts,nodes,initial,subset,fillers[:size],banned)['selections'],24)
        self.assertIsNone(p.evaluate_bundle(texts,nodes,initial,bundle,[],banned))
        trial=p.evaluate_bundle(texts,nodes,initial,bundle,fillers[:3],banned)
        self.assertEqual(len(trial['keys']),256);self.assertEqual(trial['selections'],23)
        self.assertTrue(set(map(c.literal,c.ALPHABET))<=set(trial['keys']))
        self.assertIsNone(p.evaluate_bundle(texts,nodes,initial,bundle,[c.literal('a')]+fillers[:2],banned))

    def test_operand_reuse_is_per_program_and_new_characters_are_not_restored(self):
        texts,nodes,initial,banned,_=p.counterexample()
        constructors,_,_=p.parent_search.pool(texts,nodes,banned)
        bundles,eligible=p.proposals(texts,nodes,initial,constructors['P']+constructors['I'],banned)
        self.assertTrue({'longAlpha','longBeta','longGamma','longDelta'}<=eligible)
        self.assertTrue(any(c.literal('longAlpha') in b['keys'] and b['kind']=='P' for b in bundles))
        self.assertTrue(all(len(b['keys'])<=5 for b in bundles))
        one={'0':texts['0']};single={'0':nodes['0']}
        proposed,eligible=p.proposals(one,single,initial,constructors['P']+constructors['I'],banned)
        self.assertFalse(eligible)
        self.assertFalse(any(c.literal('longAlpha') in b['keys'] for b in proposed))

    def test_unrelated_key_renumbering_preserves_cached_canonical_plan(self):
        texts={'p':'function solve(){let x=0;return 1234;}'};nodes=c.extract(texts)
        keys=c.order(map(c.literal,['function solve(){let x=0;return ',';}','12','34','1','234']))
        budget=p.parent_search.Budget(100,10)
        old=p.parent_search.evaluate(texts,nodes,keys,budget)
        inserted=c.literal('11') # absent from the source, sorts before retained12
        cached=p.parent_search.evaluate(texts,nodes,keys+[inserted],budget,old)
        fresh=p.parent_search.evaluate(texts,nodes,keys+[inserted],budget)
        self.assertIs(cached['rows']['p'],old['rows']['p'])
        self.assertEqual(cached['rows'],fresh['rows'])
        oldpacket=c.packet(keys,old['rows']['p']['tokens']);newpacket=c.packet(cached['keys'],cached['rows']['p']['tokens'])
        self.assertNotEqual(oldpacket[41:],newpacket[41:])
        self.assertEqual(c.decode_many(cached['keys'],cached['rows']),texts)
        # Removing the same absent key must preserve the original canonical IDs.
        back=p.parent_search.evaluate(texts,nodes,keys,budget,cached)
        self.assertEqual(back['rows'],old['rows'])
        self.assertEqual(c.packet(keys,back['rows']['p']['tokens']),oldpacket)

    def test_literal_merge_alternative_is_visible_not_suppressed(self):
        texts,nodes,initial,banned,_=p.counterexample()
        control=p.evaluate_bundle(texts,nodes,initial,[c.literal('Math.max(long')],[],banned,typed=False)
        self.assertLess(control['selections'],24)
        self.assertEqual(control['constructor_codes'],0)
        # This is a local complementarity witness, not a proof that32's entire
        # literal-merge search cannot escape or that bundles beat the control.
        self.assertEqual(control['selections'],20)

if __name__=='__main__':unittest.main()
