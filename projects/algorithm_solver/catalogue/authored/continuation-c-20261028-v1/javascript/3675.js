function solve(s){let answer=0;for(const c of s)answer=Math.max(answer,(123-c.charCodeAt(0))%26);return answer;}

var minOperations = solve;
module.exports = solve;
