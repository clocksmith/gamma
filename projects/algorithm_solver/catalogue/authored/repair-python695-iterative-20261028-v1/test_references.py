"""Reference controls only; never import or execute the repaired candidate."""
import importlib.util
from pathlib import Path
import unittest

SPEC=importlib.util.spec_from_file_location('repair695_cases',Path(__file__).with_name('cases.py'))
cases=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(cases)


def disjoint_set_area(grid):
    parent={};size={}
    def find(x):
        while parent[x]!=x:x=parent[x]
        return x
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            if not value:continue
            cell=(r,c);parent[cell]=cell;size[cell]=1
            for neighbor in ((r-1,c),(r,c-1)):
                if neighbor in parent:
                    a,b=find(cell),find(neighbor)
                    if a!=b:parent[b]=a;size[a]+=size[b]
    return max((size[x] for x in parent if parent[x]==x),default=0)


class ReferenceTests(unittest.TestCase):
    def test_existing_reference_matches_disjoint_sets(self):
        rows=cases.build_cases();self.assertEqual(len(rows),72)
        for row in rows:
            grid=row['args'][0];before=[r[:] for r in grid]
            self.assertEqual(row['expected'],disjoint_set_area(grid));self.assertEqual(grid,before)

    def test_invalid_domain_rejected(self):
        for args in ([],[[]],[[[True]]],[[[2]]],[[[0]*51]],[[[0],[0,1]]]):
            with self.assertRaises(ValueError):cases.oracle.validate_generated(695,args)

if __name__=='__main__':unittest.main()
