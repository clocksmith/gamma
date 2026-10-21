const solve=a=>{const s=new Set();for(const x of a){if(s.has(x))return x;s.add(x);}return null;};
