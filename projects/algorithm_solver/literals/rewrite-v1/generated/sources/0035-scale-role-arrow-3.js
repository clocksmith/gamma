const solve=(a,b)=>{let r=0;let c=a.length;while(r<c){const d=r+Math.floor((c-r)/2);if(a[d]<b){r=d+1;}else{c=d;}}return r;};
