function solve(s,t){let zeros=0;for(const c of t)if(c==='0')zeros++;const remaining=[zeros,t.length-zeros],output=[];for(const c of s){const bit=Number(c),desired=1-bit,chosen=remaining[desired]?desired:bit;remaining[chosen]--;output.push(String(bit^chosen));}return output.join('');}

var maximumXor = solve;
module.exports = solve;
