const solve=a=>{const r=[];let n=0;for(const x of a){n=((n*2|x)%5+5)%5;r.push(n===0);}return r;};
