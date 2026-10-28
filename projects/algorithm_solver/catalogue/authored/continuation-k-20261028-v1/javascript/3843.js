function solve(nums){const counts=new Map(),frequencies=new Map();for(const x of nums)counts.set(x,(counts.get(x)||0)+1);for(const count of counts.values())frequencies.set(count,(frequencies.get(count)||0)+1);for(const x of nums)if(frequencies.get(counts.get(x))===1)return x;return -1;}

var firstUniqueFreq = solve;
module.exports = solve;
