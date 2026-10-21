const solve=a=>{let b=0;let c=Array.from(a).length;const d=[];for(const e of a){if(e==='I'){d.push(b);b+=1;}else{d.push(c);c-=1;}}d.push(b);return d;};
