"""CLI default/profile integration controls; stop before binding or token creation."""
import argparse,json,pathlib,sys,unittest
from unittest.mock import patch
from algsolve import composition_bridge as bridge
from algsolve.approved_library import ApprovedLibrary

class BeforeServerBind(Exception):pass

def capture_cli(argv):
    parsed=[];endpoints=[];original=argparse.ArgumentParser.parse_args
    def parse(parser,*args,**kwargs):
        result=original(parser,*args,**kwargs);parsed.append(result);return result
    def stop(endpoint,*_args,**_kwargs):
        endpoints.append(endpoint);raise BeforeServerBind()
    with patch.object(sys,'argv',['composition-bridge',*argv]),patch.object(argparse.ArgumentParser,'parse_args',parse),patch.object(bridge,'ThreadingHTTPServer',side_effect=stop),patch.object(bridge.secrets,'token_urlsafe',side_effect=AssertionError('Token generation forbidden')) as token:
        try:bridge.main()
        except BeforeServerBind:pass
        else:raise AssertionError('CLI did not stop at expected server boundary')
        token.assert_not_called()
    assert len(parsed)==len(endpoints)==1
    return parsed[0],endpoints[0]

class CompositionDefault(unittest.TestCase):
    def test_default_resolves_to_bound_candidate_profile(self):
        args,endpoint=capture_cli([])
        catalog=ApprovedLibrary.load(args.approved_library)
        declared=catalog.manifest['evidence']['launcher_default']
        self.assertEqual(args.approved_library,bridge.ROOT/declared['relative_catalog'])
        catalog.verify_runtime(bridge.ROOT)
        self.assertEqual(endpoint[0],'127.0.0.1')
        self.assertEqual(endpoint[1],args.port)
    def test_explicit_profile_and_port_are_preserved(self):
        chosen=bridge.ROOT/'caller-selected-profile.json'
        args,endpoint=capture_cli(['--approved-library',str(chosen),'--port','8876'])
        self.assertEqual(args.approved_library,chosen)
        self.assertEqual(endpoint,('127.0.0.1',8876))

if __name__=='__main__':unittest.main(verbosity=2)
