"""Delegate packed execution to the existing verifier under this source manifest."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('rewrite_verifier',ROOT.parent/'scale-v2/verify.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROOT=ROOT
if __name__=='__main__':module.main()
