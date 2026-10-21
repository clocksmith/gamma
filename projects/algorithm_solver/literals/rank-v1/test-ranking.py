"""Marginal ranking must account for overlap and variant reselection."""
import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location("ranking",Path(__file__).with_name("search.py"));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ss={1:{"long":"abcabcabcXXXXXX","short":"abcY"},2:{"a":"abcabcZ","b":"abZ"}}
vocab=list(m.rw.base.ALPHABET)+["ab","c","bc","abcabc"]
state=m.joint.evaluate(ss,vocab,8)
for fragment in ["abc","abcabcabc","abcY","bcZ","not_present"]:
    got=m.exact_add(ss,state,fragment,8)
    # Score every variant through the independent forward parser.
    expected,_=m.audit.score(ss,set(state["vocab"])|{fragment},8)
    assert got["selections"]==expected["selections"] and got["package_bytes"]==expected["package_bytes"]
assert m.estimated(ss,state,"abcabcabc")>0
assert m.exact_add(ss,state,"abcabcabc",8)["selections"]==state["selections"]
print("5 independent marginal checks and misleading-variant frequency check passed")
