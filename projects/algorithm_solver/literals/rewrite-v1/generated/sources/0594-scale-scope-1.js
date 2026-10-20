function solve(a){const b=h(a);let c=0;for(const d of a){const a=b[d+1]||0;if(a>0){const e=b[d]+a;if(e>c){c=e;}}}return c;}function h(a){const b={};for(const c of a){b[c]=(b[c]||0)+1;}return b;}
