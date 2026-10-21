const solve=a=>{let r=0;let b=Array.from(a).length;const c=[];for(const x of a){if(x==='I'){c.push(r);r+=1;}else{c.push(b);b-=1;}}c.push(r);return c;};
