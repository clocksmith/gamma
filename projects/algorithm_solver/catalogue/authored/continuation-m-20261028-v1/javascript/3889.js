function solve(s){const counts=new Map();for(const c of s)counts.set(c,(counts.get(c)||0)+1);let answer=0;for(const alphabet of ['abcdefghijklmnopqrstuvwxyz','0123456789'])for(let i=0;i<alphabet.length/2;i++)answer+=Math.abs((counts.get(alphabet[i])||0)-(counts.get(alphabet[alphabet.length-1-i])||0));return answer;}

var mirrorFrequency = solve;
module.exports = solve;

