function solve(a){const b=a.length;const c=b*(b+1)/2;let d=0;let e=0;const f={};for(const g of a){d+=g;if(!f[g]){f[g]=true;e+=g;}}return[d-e,c-e];}
