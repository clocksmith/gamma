"""Prepare public invented-input pins only; never execute the measurement."""
import argparse
from pathlib import Path
import synthetic


def main(output):
    synthetic.checks()
    value=synthetic.prepare()
    synthetic.write(output,value)
    return {'path':str(output),'sha256':synthetic.sha(output),
            'code_files':len(value['code_hashes']),'runtime_files':len(value['runtime_hashes']),
            'oracle_tests':value['oracle_tests'],'measurement_launched':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(synthetic.json.dumps(main(args.output),sort_keys=True))
