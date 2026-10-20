function solve(a){let b=0;for(const f of a){b+=f;}if(b%3!==0){return false;}const c=b/3;let d=0;let e=0;for(const g of a){e+=g;if(e===c){d+=1;e=0;}}return d>=3;}
