const solve=a=>{let r=0;let n=0;let b='';const c=[];for(const x of a){if(r>0&&x!==b){if(r-n>=3){c.push([n,r-1]);}n=r;}b=x;r+=1;}if(r-n>=3){c.push([n,r-1]);}return c;};
