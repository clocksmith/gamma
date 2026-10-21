function solve(a){let r=0;let n=0;for(const x of a){if(x==='U'){n+=1;}else if(x==='D'){n-=1;}else if(x==='L'){r-=1;}else if(x==='R'){r+=1;}}return r===0&&n===0;}
