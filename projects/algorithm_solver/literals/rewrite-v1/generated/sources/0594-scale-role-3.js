function solve(a){const b=h(a);let r=0;for(const x of a){const a=b[x+1]||0;if(a>0){const c=b[x]+a;if(c>r){r=c;}}}return r;}function h(a){const m={};for(const x of a){m[x]=(m[x]||0)+1;}return m;}
