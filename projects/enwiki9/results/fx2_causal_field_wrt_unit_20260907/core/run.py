import hashlib,json,os,pathlib,resource,subprocess,sys,time
root=pathlib.Path('/home/x/deco/gamma/projects/enwiki9')
base=pathlib.Path(__file__).parent
out=base/sys.argv[1]
out.mkdir(exist_ok=False)
cmd=[sys.executable,'-m','unittest','discover','-s','tests','-p','test_fx2_causal_field_replay_v1.py','-v']
sources=['tools/fx2_causal_field_replay_v1.py','tests/test_fx2_causal_field_replay_v1.py','tools/causal_field_parent_coder_v1.py','tools/causal_field_wrt_adapter_v1.py']
refs=lambda:[{'path':p,'bytes':len(b:=(root/p).read_bytes()),'sha256':hashlib.sha256(b).hexdigest()} for p in sources]
before=refs()
def limits():
 os.sched_setaffinity(0,{2})
 resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
 resource.setrlimit(resource.RLIMIT_CPU,(60,60))
 resource.setrlimit(resource.RLIMIT_FSIZE,(33554432,33554432))
start=time.monotonic();usage=resource.getrusage(resource.RUSAGE_CHILDREN)
with (out/'regression.log').open('xb') as log:
 try:
  result=subprocess.run(cmd,cwd=root,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits,timeout=90,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  code=result.returncode
 except subprocess.TimeoutExpired:code=124
after=resource.getrusage(resource.RUSAGE_CHILDREN)
receipt={'command':cmd,'cwd':str(root),'sources_before':before,'sources_after':refs(),'returncode':code,'elapsed_seconds':time.monotonic()-start,'user_cpu_seconds':after.ru_utime-usage.ru_utime,'system_cpu_seconds':after.ru_stime-usage.ru_stime,'peak_rss_kib':after.ru_maxrss,'cpus':[2],'memory_bytes':536870912,'cpu_seconds':60,'wall_seconds':90,'scratch_bytes':33554432,'corpus_bytes':0,'objective_credit_bytes':0}
(out/'execution.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
raise SystemExit(code)
