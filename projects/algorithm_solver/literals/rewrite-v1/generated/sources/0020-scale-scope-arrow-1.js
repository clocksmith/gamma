const solve=a=>{const b=new Map([['(',')'],['[',']'],['{','}']]);const c=[];for(const d of a){if(b.has(d)){c.push(b.get(d));}else if(c.pop()!==d){return false;}}return c.length===0;};
