function solve(a){let b=0;let c=0;for(const d of a){if(d==='A'){b+=1;if(b>=2){return false;}}if(d==='L'){c+=1;if(c>=3){return false;}}else{c=0;}}return true;}
