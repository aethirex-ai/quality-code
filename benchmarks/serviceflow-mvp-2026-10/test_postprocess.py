"""Synthetic compatibility controls; no native sessions/models or app work."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import postprocess
pc=postprocess.phase_collect

class OptionalIterationParser(unittest.TestCase):
    def fixture(self,root,rows):
        site=root/'site';(site/'evidence').mkdir(parents=True)
        raw=('\n'.join(json.dumps(row) for row in rows)+'\n').encode()
        path=site/'evidence/issues.jsonl';path.write_bytes(raw)
        return site,path,raw

    def invoke(self,site):
        native={'completion_state':'PASS','tokens':{'input_tokens':100,'cached_input_tokens':40,'output_tokens':20},
                'observed_tokens':{'input_tokens':100,'cached_input_tokens':40,'output_tokens':20},
                'standard_short_estimated_usd':None,'flags':['standard_short_pricing_inapplicable'],
                'cost_components_usd':{'estimated_total':'1.23'}}
        original=pc.legacy.iteration_summary
        def frozen_collect(condition,sessions):
            self.assertEqual((condition,sessions),('single','owned-fake-sessions'))
            value=copy.deepcopy(native)
            value['iteration_evidence']=pc.legacy.iteration_summary(site,1,2)
            return value
        with patch.object(pc,'collect',frozen_collect):
            result=postprocess.collect('single','owned-fake-sessions')
        self.assertIs(pc.legacy.iteration_summary,original)
        self.assertEqual({k:v for k,v in result.items() if k!='iteration_evidence'},native)
        return result['iteration_evidence']

    def test_ownerless_raw_records_retained_and_counts_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            site,path,raw=self.fixture(Path(d),[{'id':'issue-1','status':'fixed'},{'id':'issue-2','status':'observed'}])
            with self.assertRaisesRegex(ValueError,'known owner'):pc.legacy.iteration_summary(site)
            value=self.invoke(site)
            self.assertEqual(value,{'state':'unparsed','error':'Issue requires stable id and known owner','counts':None,
                'raw_evidence_retained':True,'independent_iteration_review':'iteration-review.json'})
            self.assertEqual(path.read_bytes(),raw)

    def test_valid_owner_raw_summary_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            site,path,raw=self.fixture(Path(d),[{'id':'issue-1','owner':'backend','status':'fixed'}])
            expected=pc.legacy.iteration_summary(site,1,2)
            self.assertEqual(self.invoke(site),expected)
            self.assertEqual(expected['distinct_reported_issue_ids'],1)
            self.assertEqual(path.read_bytes(),raw)

    def test_counter_or_source_value_error_propagates_and_wrapper_restored(self):
        for message in ['native counter mismatch','source inventory invalid']:
            with self.subTest(message=message):
                original=pc.legacy.iteration_summary
                with patch.object(pc,'collect',side_effect=ValueError(message)):
                    with self.assertRaisesRegex(ValueError,message):postprocess.collect('single','fake')
                self.assertIs(pc.legacy.iteration_summary,original)

    def test_iteration_non_value_error_propagates_and_wrapper_restored(self):
        def fail(*args,**kwargs):raise RuntimeError('unexpected optional parser bug')
        def frozen_collect(*args,**kwargs):return pc.legacy.iteration_summary('synthetic')
        with patch.object(pc.legacy,'iteration_summary',fail),patch.object(pc,'collect',frozen_collect):
            with self.assertRaisesRegex(RuntimeError,'unexpected optional parser bug'):postprocess.collect('single','fake')
            self.assertIs(pc.legacy.iteration_summary,fail)

    def test_active_metadata_refused_without_native_read_and_wrapper_restored(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);directory=root/'runs/single';directory.mkdir(parents=True)
            (directory/'metadata.json').write_text(json.dumps({'state':'INCOMPLETE','end_unix':None}))
            original=pc.legacy.iteration_summary
            with patch.object(pc,'ROOT',root),patch.object(pc.legacy,'native_accounting',side_effect=AssertionError('native read forbidden')):
                with self.assertRaisesRegex(ValueError,'active'):postprocess.collect('single','forbidden')
            self.assertIs(pc.legacy.iteration_summary,original)

if __name__=='__main__':unittest.main()
