"""Static AST/text inspection only; never import candidate modules."""
import ast
from pathlib import Path
import unittest
ROOT=Path(__file__).parent
class SourceContracts(unittest.TestCase):
    def test_cycle_api_has_no_judge_pos(self):
        for pid in (141,142):
            tree=ast.parse((ROOT/'python'/f'{pid}.py').read_text())
            solve=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='solve')
            self.assertEqual([a.arg for a in solve.args.args],['head'])
    def test_constructor_exports(self):
        expected={129:'TreeNode',133:'Node',138:'Node',141:'ListNode',142:'ListNode',143:'ListNode',144:'TreeNode'}
        for pid,name in expected.items():
            tree=ast.parse((ROOT/'python'/f'{pid}.py').read_text())
            self.assertIn(name,[n.name for n in tree.body if isinstance(n,ast.ClassDef)])
            js=(ROOT/'javascript'/f'{pid}.js').read_text()
            self.assertIn('module.exports.'+name+'=',js)
    def test_solution_method_binding(self):
        methods={126:'findLadders',129:'sumNumbers',132:'minCut',133:'cloneGraph',138:'copyRandomList',140:'wordBreak',141:'hasCycle',142:'detectCycle',143:'reorderList',144:'preorderTraversal'}
        for pid,name in methods.items():
            tree=ast.parse((ROOT/'python'/f'{pid}.py').read_text());solution=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Solution')
            self.assertIn(name,[n.name for n in solution.body if isinstance(n,ast.FunctionDef)])
            self.assertIn('module.exports.'+name+'=',(ROOT/'javascript'/f'{pid}.js').read_text())
if __name__=='__main__':unittest.main()
