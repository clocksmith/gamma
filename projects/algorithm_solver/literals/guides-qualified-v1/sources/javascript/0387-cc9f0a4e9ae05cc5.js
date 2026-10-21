function solve(a){const m=new Map();for(const x of a){if(x>='a'&&x<='z'){m.set(x,(m.get(x)||0)+1);}}for(let i=0;i<a.length;i++){if(m.get(a[i])===1)return i;}return-1;}
