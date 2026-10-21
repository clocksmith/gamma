function solve(a){const m=new Map();for(const x of a)m.set(x,(m.get(x)||0)+1);return(m.get('U')||0)===(m.get('D')||0)&&(m.get('L')||0)===(m.get('R')||0);}
