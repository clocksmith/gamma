function solve(nums){let maximum=0;for(const x of nums)maximum=Math.max(maximum,x);const palindromes=[];for(let x=0;x<=2*maximum+1;x++){const text=x.toString(2);if(text===text.split('').reverse().join(''))palindromes.push(x);}return nums.map(x=>{let lo=0,hi=palindromes.length;while(lo<hi){const mid=Math.floor((lo+hi)/2);if(palindromes[mid]<x)lo=mid+1;else hi=mid;}let distance=x-palindromes[lo-1];if(lo<palindromes.length)distance=Math.min(distance,palindromes[lo]-x);return distance;});}

var minOperations = solve;
module.exports = solve;
