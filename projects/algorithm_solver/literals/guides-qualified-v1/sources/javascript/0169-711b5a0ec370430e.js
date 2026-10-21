function solve(a){let r=0;let n=0;for(const x of a){if(n===0){r=x;}if(x===r){n+=1;}else{n-=1;}}return r;}
