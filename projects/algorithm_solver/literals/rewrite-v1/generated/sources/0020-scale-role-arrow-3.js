const solve=a=>{const m=new Map([['(',')'],['[',']'],['{','}']]);const r=[];for(const x of a){if(m.has(x)){r.push(m.get(x));}else if(r.pop()!==x){return false;}}return r.length===0;};
