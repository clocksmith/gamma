function solve(s,k){while(true){let merged=false;for(let l=0;l<s.length;l++){for(let r=l+1;r<Math.min(s.length,l+k+1);r++)if(s[l]===s[r]){s=s.slice(0,r)+s.slice(r+1);merged=true;break;}if(merged)break;}if(!merged)return s;}}

var mergeCharacters = solve;
module.exports = solve;
