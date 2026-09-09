#!/usr/bin/env python3
"""Repeat the sealed native comparison with bounded closed-trace cache residency."""
import fx2_ratio_coder_fixture50051_q0_v1 as base
from lib.native_trace_cache_v1 import release_closed_file,memory_snapshot

ID='fx2_ratio_coder_fixture50051_q0_v2'
ORIGINAL_BINARY='results/fx2_ratio_coder_fixture50051_q0_v1/work/cmix'


class TraceCacheGate(base.NativeGate):
    def run(self,name,argv,cap,env=None,accepted=(0,),work=None):
        result=super().run(name,argv,cap,env,accepted,work)
        self.closure()
        if name=='compile':
            base.require(base.sha(self.work/'cmix')==self.inputs[ORIGINAL_BINARY]['sha256'].removeprefix('sha256:'),
                         'retry changed the native executable')
        before=memory_snapshot(self.group);released=[]
        try:
            for arm in base.ARMS:
                for phase in ('encode','decode','repeat'):
                    for suffix in ('ratio','coder'):
                        path=self.work/(arm+'-'+phase+'.'+suffix)
                        if path.exists():released.append(release_closed_file(path))
        except (OSError,ValueError) as error:
            raise base.GateFailure('resource_or_signal_stop','closed trace cache release failed: '+str(error)) from error
        if not hasattr(self,'cache_releases'):self.cache_releases=[]
        self.cache_releases.append(dict(phase=name,before=before,after=memory_snapshot(self.group),files=released))
        self.write('closed-trace-cache.json',dict(events=self.cache_releases,advisory_only=True,guard_unchanged=True))
        return result


def main():
    base.ID=ID
    base.NativeGate=TraceCacheGate
    return base.main()


if __name__=='__main__':raise SystemExit(main())
