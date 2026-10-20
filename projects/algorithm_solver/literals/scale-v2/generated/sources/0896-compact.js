function solve(a){let b=true;let c=true;for(let d=1;d<a.length;d+=1){if(a[d-1]>a[d]){b=false;}if(a[d-1]<a[d]){c=false;}}return b||c;}
