const solve=a=>{let r=0;for(const x of a){r+=x;}if(r%3!==0){return false;}const b=r/3;let n=0;let c=0;for(const x of a){c+=x;if(c===b){n+=1;c=0;}}return n>=3;};
