const solve=a=>{let b=0;let c=a.length-1;let d=0;let e=0;let f=0;while(b<c){if(a[b]<=a[c]){d=Math.max(d,a[b]);f+=d-a[b];b++;}else{e=Math.max(e,a[c]);f+=e-a[c];c--;}}return f;};
