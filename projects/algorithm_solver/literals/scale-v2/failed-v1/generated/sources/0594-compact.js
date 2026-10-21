function solve(b){const c=a(b);let d=0;for(const e of b){const f=c[e+1]||0;if(f>0){const g=c[e]+f;if(g>d){d=g;}}}return d;}function a(h){const i={};for(const j of h){i[j]=(i[j]||0)+1;}return i;}
