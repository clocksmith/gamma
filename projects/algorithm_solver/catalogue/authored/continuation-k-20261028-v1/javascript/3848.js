function solve(n){const facts=[1];for(let i=1;i<=9;i++)facts.push(facts[i-1]*i);const text=String(n);let total=0;for(const c of text)total+=facts[Number(c)];return String(total).split('').sort().join('')===text.split('').sort().join('');}

var isDigitorialPermutation = solve;
module.exports = solve;
