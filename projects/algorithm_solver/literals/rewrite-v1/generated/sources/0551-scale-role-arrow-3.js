const solve=a=>{let r=0;let n=0;for(const x of a){if(x==='A'){r+=1;if(r>=2){return false;}}if(x==='L'){n+=1;if(n>=3){return false;}}else{n=0;}}return true;};
