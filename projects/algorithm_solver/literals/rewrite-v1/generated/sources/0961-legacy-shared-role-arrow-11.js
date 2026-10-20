function h(a){const m=new Map();for(const x of a){m.set(x,(m.get(x)||0)+1);}return m;}const solve=a=>{const b=h(a);for(const x of a){if(b.get(x)>1)return x;}return null;};
