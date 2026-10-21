function solve(a){let r=0;let n=0;let b='';let c=0;for(const x of a){if(x===b){n+=1;}else{r=n;n=1;b=x;}if(n<=r){c+=1;}}return c;}
