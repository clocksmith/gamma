function solve(a,b){let c=1;let d=0;for(const e of b){const f=e.charCodeAt(0)-97;const g=a[f];if(d+g<=100){d+=g;}else{c+=1;d=g;}}return[c,d];}
