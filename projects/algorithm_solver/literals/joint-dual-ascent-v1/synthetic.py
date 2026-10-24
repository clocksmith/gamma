"""One hard-bounded invented-only proof and full-iteration measurement job."""
import json
import os
from pathlib import Path
import resource
import signal
import time
import unittest
import prototype as p
import test_prototype


class Deadline(BaseException):pass


def main():
    started=time.monotonic()
    def expired(*_):raise Deadline('Whole synthetic proof/measurement 60-second cap')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,60)
    os.sched_setaffinity(0,{4});resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2)
    output=Path(__file__).with_name('synthetic-complexity.json')
    try:
        tests=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(test_prototype))
        assert tests.wasSuccessful()
        # 300 invented 60..80-character strings; no file/corpus loader exists.
        alphabet='abcdefghijklmno'
        texts={str(i):''.join(alphabet[(i*7+j*11+j*j)%len(alphabet)] for j in range(60+i%21)) for i in range(300)}
        # Exact bans are global: all complete invented sources plus a shared
        # invented body-like literal, including occurrences in other programs.
        banned=set(texts.values())|{'fghijkl'}
        clock=time.monotonic();index=p.dual.Index(texts,banned);pool_seconds=time.monotonic()-clock
        q=p.zeros(texts);D=1000000;rows=[];best=None
        for iteration in range(2):
            clock=time.monotonic();got=p.oracle(index,q,256,D)
            assert got['joint_family_feasible']
            update_start=time.monotonic();new=p.update(q,got['gradient'],D);update_seconds=time.monotonic()-update_start
            if best is None or got['numerator']>best[0]:best=(got['numerator'],iteration)
            rows.append({'iteration':iteration,'numerator':got['numerator'],'selected_a':got['selected_a'],
                         'all_32_assignment_cases':len(got['assignments']),'phase_seconds':got['phase_seconds'],
                         'oracle_seconds':got['seconds'],'projected_update_seconds':update_seconds,
                         'full_iteration_seconds':time.monotonic()-clock,'endpoint_peak_bytes':got['endpoint_peak_bytes'],
                         'gradient_squared_norm':p.dot(got['gradient'],got['gradient']),
                         'q_nonzero_coordinates':sum(v!=0 for values in q.values() for row in values for v in row)})
            q=new
        result={'complete':True,'invented_only':True,'private_inputs_read':False,'tests_run':tests.testsRun,
                'programs':len(texts),'source_characters':sum(map(len,texts.values())),
                'maximum_source_characters':max(map(len,texts.values())),'full_pool_entries':index.distinct_allowed_entries,
                'length_pieces':len(index.pieces),'exact_global_bans':len(banned),'pool_build_seconds':pool_seconds,
                'denominator':D,'synthetic_update_step':D,'production_step_selected':False,
                'iterations':rows,'retained_best_numerator':best[0],'retained_best_iteration':best[1],
                'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'total_seconds':time.monotonic()-started,
                'limits':{'seconds':60,'core':4,'address_space_bytes':8*1024**3,'per_program_endpoint_bytes':p.ENDPOINT_BYTES}}
        assert result['total_seconds']<60
        output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
        print(json.dumps(result,sort_keys=True),flush=True)
    except BaseException as error:
        output.write_text(json.dumps({'complete':False,'invented_only':True,'exception':type(error).__name__,'seconds':time.monotonic()-started})+'\n')
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


if __name__=='__main__':main()
