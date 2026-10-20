function solve(a){let b=0;let c=a.length-1;let d=0;while(b<c){const e=Math.min(a[b],a[c])*(c-b);d=Math.max(d,e);if(a[b]<=a[c]){b++;}else{c--;}}return d;}
