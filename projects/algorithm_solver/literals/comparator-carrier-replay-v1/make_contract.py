"""Public-only pending builder; no pending generation before root review."""
import argparse
import copy
import common as c
import binding

def activate(current,pending):
    assert current==pending and pending['active'] is False
    value=copy.deepcopy(pending);value['active']=True;return value

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--activate',action='store_true');args=ap.parse_args()
    value=binding.build();path=c.HERE/'pending-contract.json'
    if args.activate:value=activate(value,c.read(path));path=c.HERE/'contract.json'
    c.write(path,value);print({'active':value['active'],'sha256':c.hashfile(path),'private_inputs_opened':False})
if __name__=='__main__':main()
