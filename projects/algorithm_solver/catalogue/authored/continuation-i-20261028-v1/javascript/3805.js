function solve(words){const counts=new Map();let answer=0;for(const word of words){const first=word.charCodeAt(0);let key='';for(const c of word)key+=String.fromCharCode(97+(c.charCodeAt(0)-first+26)%26);answer+=counts.get(key)||0;counts.set(key,(counts.get(key)||0)+1);}return answer;}

var countPairs = solve;
module.exports = solve;
