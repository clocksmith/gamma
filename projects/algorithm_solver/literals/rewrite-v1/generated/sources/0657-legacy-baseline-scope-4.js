function solve(a){const b=new Map();for(const c of a)b.set(c,(b.get(c)||0)+1);return(b.get('U')||0)===(b.get('D')||0)&&(b.get('L')||0)===(b.get('R')||0);}
