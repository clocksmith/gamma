const solve=a=>{const b=[];let c=0;for(const d of a){c=((c*2|d)%5+5)%5;b.push(c===0);}return b;};
