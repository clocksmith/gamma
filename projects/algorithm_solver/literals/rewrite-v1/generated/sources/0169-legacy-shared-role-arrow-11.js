function h(a){const m=new Map();for(const x of a){m.set(x,(m.get(x)||0)+1);}return m;}const solve=a=>{const b=h(a);for(const [x,y]of b){if(y>a.length/2)return x;}return 0;};
