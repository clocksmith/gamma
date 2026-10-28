"use strict";
function solve(s) {
const counts=new Map(),first=new Map();for(let i=0;i<s.length;i++)if('aeiou'.includes(s[i])){counts.set(s[i],(counts.get(s[i])||0)+1);if(!first.has(s[i]))first.set(s[i],i);}const vowels=[...counts.keys()].sort((a,b)=>counts.get(b)-counts.get(a)||first.get(a)-first.get(b)).map(c=>c.repeat(counts.get(c))).join('');let index=0;return [...s].map(c=>'aeiou'.includes(c)?vowels[index++]:c).join('');
}
function sortVowels(s) { return solve(s); }
module.exports=solve;
module.exports.sortVowels=sortVowels;
