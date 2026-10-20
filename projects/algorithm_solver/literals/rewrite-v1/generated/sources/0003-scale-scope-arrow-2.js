const solve=a=>{const b=new Map();let c=0;let d=0;let e=0;for(const f of a){const a=b.get(f);if(a!==undefined&&a>=c){c=a+1;}b.set(f,d);e=Math.max(e,d-c+1);d++;}return e;};
