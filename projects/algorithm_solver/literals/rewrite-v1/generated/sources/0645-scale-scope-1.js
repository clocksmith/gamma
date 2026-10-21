function solve(a){const b=a.length;const c=b*(b+1)/2;let d=0;let e=0;const f={};for(const b of a){d+=b;if(!f[b]){f[b]=true;e+=b;}}return[d-e,c-e];}
