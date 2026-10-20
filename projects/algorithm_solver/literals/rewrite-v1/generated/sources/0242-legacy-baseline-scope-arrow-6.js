const solve=(a,b)=>{const c=new Map();for(const b of a){c.set(b,(c.get(b)||0)+1);}for(const a of b){c.set(a,(c.get(a)||0)-1);}return[...c.values()].every(a=>a===0);};
