const solve=a=>{const b=new Map();for(const c of a){if(c>='a'&&c<='z'){b.set(c,(b.get(c)||0)+1);}}for(let c=0;c<a.length;c++){if(b.get(a[c])===1)return c;}return-1;};
