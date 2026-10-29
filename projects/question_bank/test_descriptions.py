import unittest
from descriptions import validate, excerpt, cited_leetcode, summarize, attach

class DescriptionsTests(unittest.TestCase):
    def record(self):
        return {'source_post_id':'a','source_type':'ALGORITHM','title':'Test task','uid':'hack2hire:post:a',
                'variants':[{'id':'x','content_status':'not_acquired'},{'id':'y','content_status':'public_spec_synopsis'}]}

    def envelope(self, text='Design a queue with enqueue and dequeue.'):
        return {'url':'https://example.test/a','response_sha256':'fixture',
                'payload':{'status':{'code':200},'data':{'id':'a','type':'ALGORITHM','title':'Test task',
                 'contentPreview':text,'company':{'DATABRICKS':{'frequency':2}},'stages':['ONSITE']}}}

    def test_description_identity_mismatch_rejected(self):
        payload=self.envelope()['payload'];payload['data']['id']='other'
        with self.assertRaises(ValueError):validate(payload,self.record())

    def test_short_excerpt_skips_recommendation_boilerplate(self):
        text='*(A variation of [359. Logger Rate Limiter](https://leetcode.com/problems/logger-rate-limiter/). Solve it first.)*\n\n'+' '.join('word'+str(i) for i in range(60))
        result=excerpt(text)
        self.assertTrue(result.startswith('word0 word1'))
        self.assertEqual(len(result.removesuffix(' …').split()),25)

    def test_source_citation_is_related_not_equivalent(self):
        relation=cited_leetcode('[variant](https://leetcode.com/problems/two-sum/description/)',
                                 [{'slug':'two-sum','id':'1','title':'Two Sum'}])[0]
        self.assertEqual(relation['id'],'1')
        self.assertEqual(relation['relationship'],'source_cited_related_problem')
        self.assertFalse(relation['merge_allowed'])

    def test_group_preview_never_promoted_to_full_variant(self):
        record=self.record();summary=summarize(record,self.envelope(),[])
        attach([record],{'records':[summary]})
        self.assertEqual(record['variants'][0]['content_status'],'group_preview_available')
        self.assertEqual(record['variants'][1]['content_status'],'public_spec_synopsis')
        self.assertEqual(record['source_company_attributes'],{'DATABRICKS':{'frequency':2}})
        self.assertNotIn('excerpt',record['description'])
        self.assertTrue(record['description_matches_listing_version'])
        self.assertEqual(record['description']['scope'],'group-level; not a complete variant specification')

    def test_source_reference_does_not_overwrite_different_title_candidate(self):
        record=self.record()
        record['leetcode_overlap']={'status':'exact_title_candidate','candidates':[{'id':'224'}], 'merge_allowed':False}
        text='A variation of [772](https://leetcode.com/problems/basic-calculator-iii/).'
        reference=[{'slug':'basic-calculator-iii','id':'772','title':'Basic Calculator III'}]
        attach([record], {'records':[summarize(record,self.envelope(text),reference)]})
        self.assertEqual(record['leetcode_overlap']['candidates'][0]['id'],'224')
        self.assertEqual(record['source_leetcode_relationships'][0]['id'],'772')
        self.assertFalse(record['leetcode_overlap']['merge_allowed'])

    def test_stale_description_version_remains_explicit(self):
        record=self.record();record['source_updated_at']='new'
        envelope=self.envelope();envelope['payload']['data']['updatedDate']='old'
        attach([record],{'records':[summarize(record,envelope,[])]})
        self.assertFalse(record['description_matches_listing_version'])

    def test_empty_preview_is_not_acquisition_success(self):
        record=self.record();summary=summarize(record,self.envelope(''),[])
        attach([record],{'records':[summary]})
        self.assertEqual(summary['description']['status'],'empty_source_preview')
        self.assertEqual(record['variants'][0]['content_status'],'not_acquired')

if __name__ == '__main__':unittest.main()
