const solve=a=>{const m=new Map();let r=0;let n=0;let b=0;for(const x of a){const a=m.get(x);if(a!==undefined&&a>=r){r=a+1;}m.set(x,n);b=Math.max(b,n-r+1);n++;}return b;};
