function solve(words,k){const counts=new Map();for(const word of words)if(word.length>=k){const key=word.slice(0,k);counts.set(key,(counts.get(key)||0)+1);}let answer=0;for(const count of counts.values())if(count>=2)answer++;return answer;}

var prefixConnected = solve;
module.exports = solve;
