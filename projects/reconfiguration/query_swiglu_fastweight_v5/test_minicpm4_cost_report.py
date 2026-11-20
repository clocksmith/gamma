import json
import os
import tempfile
import unittest
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
from minicpm4_cost_report import LOCK_HASH, digest, finalize, layout
from table_costs import ARMS, cost_interval, report


def fixture(table=0, rows=4):
    name = f'dev_42_s{table}_word'
    data = {
        'model': 'synthetic',
        'split': 'dev',
        'seed': 42,
        'task_count': rows,
        'rows': [],
        'specialties_compiled': [
            {
                'specialty_id': name,
                'readout_adapter_compile_ms': 12,
                'classifier_compile_ms': 2,
                'kv_snapshot': {'kv_build_ms': 2},
            }
        ],
    }
    for i in range(rows):
        for arm, ms in zip(ARMS, [2, 4, 1]):
            data['rows'].append(
                dict(
                    specialty_id=name,
                    task_id=table * rows + i,
                    arm=arm,
                    total_ms=ms,
                    multi_token=False,
                    expected='kappa' if i == 0 else 'north',
                    group=str(i),
                )
            )
    return data


class Costs(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)

    def paths(self, *datasets):
        files = []
        for i, d in enumerate(datasets):
            f = self.dir / f'r{i}.json'
            f.write_text(json.dumps(d))
            files.append(f)
        return files

    def test_positive_integer_intervals_both_sides(self):
        cases = [
            (10, -2, (5, None), (1, 5)),
            (5, -2, (3, None), (1, 2)),
            (-5, 2, (1, 2), (3, None)),
            (-4, 2, (1, 2), (2, None)),
            (0, 0, (1, None), (1, None)),
            (1, 0, None, (1, None)),
            (-1, 0, (1, None), None),
            (0, 1, None, (1, None)),
            (0, -1, (1, None), None),
            (F(2, 3), F(-2, 9), (3, None), (1, 3)),
        ]

        def pair(x):
            return (x['first'], x['last']) if x else None

        for gap, slope, a, b in cases:
            with self.subTest(gap=gap, slope=slope):
                self.assertEqual(pair(cost_interval(gap, slope)), a)
                self.assertEqual(pair(cost_interval(-gap, -slope)), b)

    def test_paired_costs_and_strata(self):
        data = fixture()
        paths = self.paths(data)
        name = data['specialties_compiled'][0]['specialty_id']
        rpt = report(
            paths,
            token_lengths={'north': 1, 'kappa': 2},
            layout={'r0.json': {name: (0, set(range(4)))}},
            overlap=[0, 1],
        )
        table = rpt['tables'][name]
        kv = table['comparisons']['kv_ctx']
        clf = table['comparisons']['probe_bare']
        self.assertEqual(kv['adapterAtLeastAsFastAtQueryCounts'], {'first': 5, 'last': None})
        self.assertEqual(kv['equalTimeAtQueryCounts'], {'first': 5, 'last': 5})
        self.assertEqual(kv['adapterMinusOtherAtObservedCountMs'], 2)
        self.assertIsNone(clf['adapterAtLeastAsFastAtQueryCounts'])
        self.assertEqual(clf['otherAtLeastAsFastAtQueryCounts'], {'first': 1, 'last': None})
        self.assertEqual(table['byTargetTokenLength']['singleTokenWord.1tokens']['count'], 3)
        self.assertEqual(table['byTargetTokenLength']['multiTokenWord.2tokens']['count'], 1)
        self.assertTrue(table['reportedBuildOverlapPossible'])
        cohort = rpt['cohorts']['allTables']
        self.assertEqual(cohort['observedQuestions'], 4)
        self.assertEqual(cohort['comparisons']['probe_bare']['perTableCounts']['noPayback'], 1)
        self.assertEqual(cohort['comparisons']['kv_ctx']['perTableCounts']['noPayback'], 0)

    def test_reject_duplicate_integer_missing_arm_and_unpaired_rows(self):
        d = fixture()
        for change, text in [
            (lambda x: x['rows'].append(x['rows'][0]), 'Duplicate arm'),
            (lambda x: x['rows'].pop(), 'Unpaired measurements'),
            (lambda x: x['rows'].__setitem__(slice(0, 3), []), 'Missing whole'),
            (lambda x: x['rows'][1].update(expected='different'), 'Unpaired table or target'),
            (lambda x: x['specialties_compiled'].clear(), 'Orphan or missing'),
        ]:
            with self.subTest(text=text):
                sample = deepcopy(d)
                change(sample)
                with self.assertRaisesRegex(ValueError, text):
                    report(self.paths(sample))

    def test_reject_cross_file_duplicate_integer_task(self):
        a, b = fixture(), fixture(1)
        for row in b['rows']:
            row['task_id'] -= 4
        with self.assertRaisesRegex(ValueError, 'Duplicate integer task ID'):
            report(self.paths(a, b))

    def test_confirmation_structure_and_no_early_access(self):
        plan = layout(96, 20261120)
        self.assertEqual(len(plan), 24)
        self.assertEqual(len({q for chunk in plan.values() for _, ids in chunk.values() for q in ids}), 1536)
        (self.dir / 'confirm-corrupt.json').write_text('deliberately invalid JSON')
        with self.assertRaisesRegex(ValueError, 'must have DONE'):
            finalize(self.dir, self.dir / 'out')
        self.assertFalse((self.dir / 'out').exists())

    @unittest.skipUnless(os.environ.get('B1_MINICPM_STUDY'), 'needs pinned tokenizer and source only')
    def test_after_done_synthetic_end_to_end(self):
        source = Path(os.environ['B1_MINICPM_STUDY'])
        study = self.dir / 'study'
        study.mkdir()
        (study / 'source').symlink_to(source / 'source')
        (study / 'engine').symlink_to(source / 'engine')
        (self.dir / 'models').symlink_to(source.parent / 'models')
        (study / 'timing-provenance.json').write_bytes((source / 'timing-provenance.json').read_bytes())
        hashes = {}
        for filename, tables in layout(96, 20261120).items():
            d = {
                'model': 'synthetic',
                'split': 'confirm',
                'seed': 20261120,
                'task_count': 64,
                'rows': [],
                'specialties_compiled': [],
            }
            for name, (index, _) in tables.items():
                template = fixture(index, 16)
                comp = template['specialties_compiled'][0]
                comp['specialty_id'] = name
                d['specialties_compiled'].append(comp)
                for row in template['rows']:
                    row['specialty_id'] = name
                    row['multi_token'] = index >= 48
                    row['expected'] = (
                        'red-1' if index >= 48 else ('kappa' if row['task_id'] % 4 == 0 else 'north')
                    )
                    d['rows'].append(row)
            f = study / filename
            f.write_text(json.dumps(d))
            hashes[filename] = digest(f)
        summary = study / 'confirmed-summary.json'
        summary.write_text(
            json.dumps(
                dict(
                    lock_sha256=LOCK_HASH,
                    valid_controls=True,
                    tables=96,
                    questions=1536,
                    receipt_sha256=hashes,
                )
            )
        )
        ledger = {**hashes, summary.name: digest(summary)}
        (study / 'receipt-digests.sha256').write_text(
            ''.join(h + '  ' + n + '\n' for n, h in ledger.items())
        )
        (study / 'DONE').touch()
        out = finalize(study, self.dir / 'costs')
        c = json.loads((out / 'costs.json').read_text())['cohorts']
        self.assertEqual(c['allTables']['observedQuestions'], 1536)
        self.assertEqual(c['reportedOverlapRange']['tables'], 4)
        self.assertEqual(c['outsideReportedOverlapRange']['tables'], 92)
        self.assertEqual(c['wordCode']['tables'], 48)
        self.assertEqual(c['twoPartCode']['tables'], 48)
        self.assertEqual(c['target.singleTokenWord.1tokens']['observedQuestions'], 576)
        self.assertEqual(c['target.multiTokenWord.2tokens']['observedQuestions'], 192)
        self.assertEqual(c['target.twoPartCode.3tokens']['observedQuestions'], 768)
        self.assertEqual(finalize(study, self.dir / 'costs'), out)
        first = study / 'confirm-00-04.json'
        first.write_text(first.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, 'digest mismatch'):
            finalize(study, self.dir / 'costs')


if __name__ == '__main__':
    unittest.main()
