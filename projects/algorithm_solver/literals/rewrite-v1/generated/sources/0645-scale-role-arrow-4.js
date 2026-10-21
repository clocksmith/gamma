const solve=a=>{const b=a.length;const c=b*(b+1)/2;let r=0;let n=0;const m={};for(const x of a){r+=x;if(!m[x]){m[x]=true;n+=x;}}return[r-n,c-n];};
