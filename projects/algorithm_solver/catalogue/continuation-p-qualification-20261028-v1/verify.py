"""Independent retained-evidence host replay entry; no candidate execution."""
import importlib.util
from pathlib import Path
def verify(args):
    spec=importlib.util.spec_from_file_location('p_official_replay_controller',Path(__file__).with_name('protocol.py'))
    owner=importlib.util.module_from_spec(spec);spec.loader.exec_module(owner)
    return owner.run_or_replay(args,replay=True)
