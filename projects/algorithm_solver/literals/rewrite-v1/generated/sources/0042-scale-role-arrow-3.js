const solve=a=>{let r=0;let b=a.length-1;let n=0;let c=0;let d=0;while(r<b){if(a[r]<=a[b]){n=Math.max(n,a[r]);d+=n-a[r];r++;}else{c=Math.max(c,a[b]);d+=c-a[b];b--;}}return d;};
