#!/usr/bin/env python3
"""Package a self-contained fx2 candidate from a GEPA page-order key."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import textwrap
import zlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROGRAMS = ROOT / "programs"
DEFAULT_TEMPLATE = PROGRAMS / "fx2_geometry_title_sort_dictcmix_xz_zlibpy_min_v1"
SUPPORTED_FIELDS = {
    "kind",
    "template",
    "topic",
    "category",
    "redirect",
    "first_link",
    "params",
    "title",
    "title_prefix",
    "title_suffix",
    "rev_title",
    "namespace",
    "shape",
    "size",
    "lines",
    "mh2",
    "mh3",
    "mh4",
}


def raw_deflate(data: bytes) -> bytes:
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    return comp.compress(data) + comp.flush()


def payload_source(fields: tuple[str, ...]) -> str:
    field_expr = repr(fields)
    return textwrap.dedent(
        """
        import hashlib,lzma,os,re,subprocess as s
        P=__file__[:-10];T="/tmp/g"+str(os.getpid());B=T+"b";D=T+"d";I=T+"i";U=T+"o";O=b"  <page>\\n";C=b"  </page>\\n";N=s.DEVNULL;R=s.run;A=os.path.exists;S=sorted;G=range;L=len;J=b"".join;Q=open;F=FIELD_EXPR
        def b():
         if not A(B):Q(B,"wb").write(lzma.open(P+"c").read());os.chmod(B,493)
         return B
        def d():
         if not A(D):R([b(),"-d",P+"d",D],stdout=N,stderr=N)
         return D
        def r(a,z):
         Q(I,"wb").write(z);R([b(),a,d(),I,U],stdout=N,stderr=N);return Q(U,"rb").read()
        def f(p,x):
         m=re.search(x,p,18);return m.group(1)if m else b""
        def n(v,l=180):return re.sub(rb"[^a-z0-9]+",b" ",v.lower()).strip()[:l]
        def u(a,l=8,m=80):
         o=[];e=set()
         for v in a:
          x=n(v,m)
          if x and x not in e:o.append(x);e.add(x)
          if L(o)>=l:break
         return tuple(o)
        def w(v,l=160):
         o=[];e=set()
         for m in re.finditer(rb"[a-z][a-z0-9]{{2,24}}",v.lower()):
          x=m.group(0)
          if x not in e:o.append(x);e.add(x)
          if L(o)>=l:break
         return tuple(o)
        def g(v):
         o=0
         while v>15 and o<31:v>>=1;o+=1
         return o
        def mh(t,b=8):
         if not t:return(0,)*b
         o=[]
         for i in G(b):
          z=(1<<64)-1;seed=bytes([i])
          for x in t:
           h=int.from_bytes(hashlib.blake2s(seed+x,digest_size=8).digest(),"little")
           if h<z:z=h
          o.append(z>>40)
         return tuple(o)
        def sh(p):
         o=bytearray()
         for x in p.splitlines()[:160]:
          y=x.strip()
          if not y:o.extend(b"_;")
          elif y.startswith(b"<"):
           m=re.match(rb"</?([a-zA-Z0-9:_-]+)",y);o.extend((m.group(1).lower()[:8]if m else b"<")+b";")
          elif y.startswith(b"{{"):o.extend(b"T"+n(f(y,rb"\\{{\\{{\\s*([^|}}\\n]{{1,64}})"),32)+b";")
          elif y.startswith(b"|"):o.extend(b"P;")
          elif y.startswith(b"=="):o.extend(b"H;")
          elif y.startswith((b"*",b"#",b":",b";")):o.extend(y[:1]+b";")
          else:o.extend(b"W;")
         return hashlib.blake2s(bytes(o),digest_size=8).digest()
        def tp(t):
         x=w(t,16);return b" ".join(x[:3]),b" ".join(x[-3:]),b" ".join(reversed(x)),x[0]if L(x)>1 and b":"in t[:64]else b""
        def sp(z,u=0):
         a=z.find(O);p=[];i=a
         if a<0:return
         while 1:
          j=z.find(O,i);k=z.find(C,j)
          if j<0 or k<0:break
          k+=L(C);p+=z[j:k],;i=k
         v=[int(f(x,rb"<id>(\\d+)</id>")or 1<<99)for x in p]
         if L(p)>1 and L(v)==L(set(v))and(u or v==S(v)):return z[:a],p,z[i:],v
        def key(p,pid):
         rt=f(p,rb"<title>(.*?)</title>");ti=n(rt,220);tx=f(p,rb"<text[^>]*>(.*?)</text>")or p
         ca=u(re.findall(rb"\\[\\[Category:([^\\]|\\n]{{1,120})",p,2));tm=u(re.findall(rb"\\{{\\{{\\s*([a-z0-9 _-]{{1,80}})(?:[|}}\\n])",p,2));pa=u(re.findall(rb"\\|\\s*([a-z0-9 _-]{{1,50}})\\s*=",p,2),10,50)
         rd=n(f(p,rb"#redirect\\s*\\[\\[([^\\]|\\n]{{1,140})"),140);fl=n(f(p,rb"\\[\\[([^\\]|\\n]{{1,120})(?:\\|[^\\]\\n]*)?\\]\\]"),120)
         pr,su,rv,ns=tp(rt);to=w(tx,160);ib=any(b"infobox"in x for x in tm);tax=any(b"taxobox"in x or b"speciesbox"in x for x in tm)
         ki=b"redirect"if rd else b"category"if ti.startswith(b"category ")else b"list"if ti.startswith(b"list of")else b"disambig"if b"disambiguation"in ti else b"taxon"if tax else b"infobox"if ib else b"category_tagged"if ca else b"plain"
         cat=b" ".join(ca[:4]);tmp=b" ".join(tm[:4]);top=cat or tmp or fl or pr or ti;mm=mh(to,8)
         V={"kind":ki,"template":tmp,"topic":top,"category":cat,"redirect":rd,"first_link":fl,"params":b" ".join(pa[:6]),"title":ti,"title_prefix":pr,"title_suffix":su,"rev_title":rv,"namespace":ns,"shape":sh(p),"size":g(L(p)),"lines":g(p.count(b"\\n")),"mh2":mm[:2],"mh3":mm[:3],"mh4":mm[:4]}
         return tuple(V[x]for x in F)+(pid,)
        def o(z):
         x=sp(z)
         if not x:return
         h,p,t,v=x;q=S(G(L(p)),key=lambda i:key(p[i],v[i]))
         if q!=S(G(L(p))):return h+J(p[i]for i in q)+t
        def e(z):
         x=sp(z,1)
         if not x:return z
         h,p,t,v=x;return h+J(p[i]for i in S(G(L(p)),key=lambda i:v[i]))+t
        def compress(z):
         y=o(z);return b"G"+r("-c",y)if y else b"R"+r("-c",z)
        def decompress(z):
         y=r("-d",z[1:]);return e(y)if z[:1]==b"G"else y
        """
    ).replace("FIELD_EXPR", field_expr).strip() + "\n"


def load_screen_hit(screen_json: pathlib.Path | None, fields: tuple[str, ...]) -> dict | None:
    if not screen_json:
        return None
    data = json.loads(screen_json.read_text())
    wanted = list(fields)
    for section in (
        "top_by_objective",
        "top_by_smooth",
        "top_by_boundary",
        "frontier",
        "top_by_score",
        "diverse_top",
        "top",
        "rows",
    ):
        for row in data.get(section, []):
            row_fields = row.get("fields") or row.get("parts")
            if row_fields == wanted:
                return row
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True)
    parser.add_argument("--fields", required=True, help="comma-separated GEPA feature key")
    parser.add_argument("--template", type=pathlib.Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--screen-json", type=pathlib.Path)
    args = parser.parse_args()

    fields = tuple(field.strip() for field in args.fields.split(",") if field.strip())
    bad = [field for field in fields if field not in SUPPORTED_FIELDS]
    if bad:
        raise SystemExit(f"unsupported fields: {bad}")
    if len(fields) < 2:
        raise SystemExit("need at least two fields")
    if not (args.template / "program.py").exists():
        raise SystemExit(f"missing template candidate: {args.template}")

    out_dir = PROGRAMS / args.id
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("program.py", "c", "d"):
        shutil.copy2(args.template / name, out_dir / name)
    source = payload_source(fields)
    (out_dir / "p").write_bytes(raw_deflate(source.encode()))

    screen_hit = load_screen_hit(args.screen_json, fields)
    meta = {
        "id": args.id,
        "family": "fx2-gepa-order",
        "status": "candidate",
        "parent": args.template.name,
        "description": "Self-contained fx2 candidate using a GEPA-derived reversible page-order key.",
        "hypothesis": "Template/topic/minhash/shape page adjacency can lower archive bytes without storing an order table.",
        "deps": [],
        "order_fields": list(fields),
        "screen_evidence": {
            "basis": "No-compression GEPA adjacency screen; not a Hutter score.",
            "source": str(args.screen_json) if args.screen_json else None,
            "hit": screen_hit,
        },
        "pgsg": {
            "nodes": [
                {
                    "id": "page_order",
                    "type": "transform",
                    "payload": {"discrete": {"mode": "gepa_hybrid", "fields": list(fields)}},
                },
                {
                    "id": "backend",
                    "type": "codec",
                    "payload": {"discrete": {"codec": "fx2-cmix", "container": "xz+raw-deflate-wrapper"}},
                },
            ],
            "edges": [{"from": "page_order", "to": "backend", "stream": "reordered_raw_xml"}],
        },
        "measured": {},
        "verdict": "Unmeasured GEPA-order candidate.",
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps({"id": args.id, "dir": str(out_dir), "payload_size": (out_dir / "p").stat().st_size}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
