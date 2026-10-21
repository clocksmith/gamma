function h(a){const b=new Map();for(const c of a){b.set(c,(b.get(c)||0)+1);}return b;}const solve=a=>{const b=h(a);for(const c of a){if(b.get(c)>1)return c;}return null;};
