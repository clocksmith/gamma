const solve=(a,b)=>{const s=new Set(a);let r=0;for(const x of b){if(s.has(x))r++;}return r;};
