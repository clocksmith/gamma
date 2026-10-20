"""BigInt round-trips and type spoofing failures at the host judgment boundary."""
import importlib.util,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location("row_verify",ROOT/"verify.py");v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
with tempfile.TemporaryDirectory() as td:
    p=Path(td);(p/"program.js").write_text("function solve(){return 9007199254740993n;}")
    (p/"inputs.json").write_text(json.dumps({"entry":"solve","calls":[{"args":[]}]}))
    output=subprocess.check_output(["node",str(ROOT/"harness.cjs")],cwd=p,text=True)
    rec=json.loads(output.splitlines()[0]);case={"args":[],"expected":9007199254740993}
    assert v.judge_record(62,case,"return",rec)[0]
    assert not v.judge_record(62,case,"return",{**rec,"result_type":"object"})[0]
    assert not v.judge_record(62,case,"return",{**rec,"result_type":"number","result":9007199254740992})[0]
    assert not v.judge_record(62,case,"return",{**rec,"args_after":[1]})[0]
    boolean={**rec,"result_type":"boolean","result":True}
    assert v.judge_record(97,{"args":[],"expected":True},"return",boolean)[0]
    assert not v.judge_record(97,{"args":[],"expected":1},"return",boolean)[0]
print("6 result transport/type/effect checks passed")
