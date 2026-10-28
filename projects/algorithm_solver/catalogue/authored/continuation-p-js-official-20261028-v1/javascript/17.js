
var letterCombinations = function(digits) {
const mapping=['abc','def','ghi','jkl','mno','pqrs','tuv','wxyz'];let result=[''];for(const digit of digits){const following=[];for(const prefix of result)for(const c of mapping[Number(digit)-2])following.push(prefix+c);result=following;}return result;
};
module.exports = {letterCombinations};
