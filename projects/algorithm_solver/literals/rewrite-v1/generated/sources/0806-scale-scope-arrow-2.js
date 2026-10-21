const solve=(a,b)=>{let c=1;let d=0;for(const e of b){const b=e.charCodeAt(0)-97;const f=a[b];if(d+f<=100){d+=f;}else{c+=1;d=f;}}return[c,d];};
