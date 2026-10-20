function solve(a){let b=0;for(const c of a){b+=c;}if(b%3!==0){return false;}const c=b/3;let d=0;let e=0;for(const b of a){e+=b;if(e===c){d+=1;e=0;}}return d>=3;}
