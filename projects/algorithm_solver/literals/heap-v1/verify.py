"""Use the established literal execution path with this new frozen source pool."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("heap_verify",ROOT.parent/"scale-v2/verify.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.ROOT=ROOT
if __name__=="__main__":module.main()
