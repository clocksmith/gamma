var a=function(a){let r=0;for(let i=1;i<a.length;i++){r+=Math.max(0,a[i]-a[i-1]);}return r;};function solve(b){return a(b);}
