from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[5]
p=ROOT/"projects/algorithm_solver/catalogue/development-66-20261029-v1/validate-study.py"
s=importlib.util.spec_from_file_location("validate_authored_study",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
if __name__=="__main__":m.validate(Path(__file__).resolve().parent)
