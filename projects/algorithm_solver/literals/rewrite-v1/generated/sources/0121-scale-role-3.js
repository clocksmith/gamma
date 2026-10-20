function solve(a){if(a.length===0){return 0;}let b=a[0];let r=0;for(const x of a){const a=x-b;if(a>r){r=a;}if(x<b){b=x;}}return r;}
