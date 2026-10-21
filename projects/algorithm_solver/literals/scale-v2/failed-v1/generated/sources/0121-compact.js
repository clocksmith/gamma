function solve(a){if(a.length===0){return 0;}let b=a[0];let c=0;for(const d of a){const e=d-b;if(e>c){c=e;}if(d<b){b=d;}}return c;}
