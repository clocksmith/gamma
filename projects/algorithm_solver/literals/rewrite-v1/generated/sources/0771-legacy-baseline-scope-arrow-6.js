const solve=(a,b)=>{const c=new Set(a);let d=0;for(const a of b){if(c.has(a))d++;}return d;};
