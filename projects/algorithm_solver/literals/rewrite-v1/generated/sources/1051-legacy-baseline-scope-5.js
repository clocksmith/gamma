function solve(a){const b=[...a].sort((a,b)=>a-b);return a.reduce((a,c,d)=>a+(c!==b[d]),0);}
