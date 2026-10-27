"""Independent threshold-two graph simulation, no protected cases."""
from array import array
from pathlib import Path
import importlib.util,subprocess,json,time,math
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
spec=importlib.util.spec_from_file_location('triangle',ROOT/'python'/'2647.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
sizes=list(range(1,41))+[99,100,101,102,255,256,257,258,999,1000];start=time.monotonic()
def check(n,seeds):
    assert len(seeds)==(n*(n+3)+3)//4
    red=bytearray(n*n);neighbors=bytearray(n*n);q=array('I')
    for r,c in seeds:
        assert 1<=r<=n and 1<=c<2*r
        i=(r-1)**2+c-1;assert not red[i];red[i]=1;q.append(i)
    head=0
    while head<len(q):
        i=q[head];head+=1;r=math.isqrt(i)+1;c=i-(r-1)**2+1
        adjacent=[]
        if c>1:adjacent.append(i-1)
        if c<2*r-1:adjacent.append(i+1)
        if c%2 and r<n:adjacent.append(r*r+c)
        elif not c%2:adjacent.append((r-2)**2+c-2)
        for j in adjacent:
            if not red[j]:
                neighbors[j]+=1
                if neighbors[j]>=2:red[j]=1;q.append(j)
    assert len(q)==n*n,(n,len(q))
for n in sizes:check(n,mod.solve(n))
js="const s=require(process.argv[1]);const ns=JSON.parse(require('fs').readFileSync(0,'utf8'));for(const n of ns){const seeds=s(n),red=new Uint8Array(n*n),cnt=new Uint8Array(n*n),q=new Uint32Array(n*n);let end=0;if(seeds.length!==Math.ceil(n*(n+3)/4))throw Error('count');for(const[r,c]of seeds){if(r<1||r>n||c<1||c>=2*r)throw Error('bounds');const i=(r-1)**2+c-1;if(red[i])throw Error('duplicate');red[i]=1;q[end++]=i;}for(let h=0;h<end;h++){let i=q[h],r=Math.floor(Math.sqrt(i))+1,c=i-(r-1)**2+1,a=[];if(c>1)a.push(i-1);if(c<2*r-1)a.push(i+1);if(c%2&&r<n)a.push(r*r+c);else if(c%2===0)a.push((r-2)**2+c-2);for(const j of a)if(!red[j]){cnt[j]++;if(cnt[j]>=2){red[j]=1;q[end++]=j;}}}if(end!==n*n)throw Error('not filled '+n);}console.log(JSON.stringify({passed:ns.length}));"
r=subprocess.run(['node','--max-old-space-size=256','-e',js,str(ROOT/'javascript'/'2647.js')],input=json.dumps(sizes),text=True,capture_output=True,timeout=60);assert r.returncode==0,r.stderr
report={'id':2647,'sizes':sizes,'python_passed':len(sizes),'javascript':json.loads(r.stdout),'elapsed_seconds':round(time.monotonic()-start,3),'scope':'Independent development simulation plus seed-count lower-bound check; not admission or confirmation.'}
(HERE/'triangle-test-results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
