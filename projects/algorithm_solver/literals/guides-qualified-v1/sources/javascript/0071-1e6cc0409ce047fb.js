function solve(a){const r=[];for(const x of a.split('/')){if(!x||x==='.'){continue;}if(x==='..'){r.pop();}else{r.push(x);}}return'/'+r.join('/');}
