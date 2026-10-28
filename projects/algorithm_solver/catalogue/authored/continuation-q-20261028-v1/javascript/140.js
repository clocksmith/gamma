"use strict";
function solve(s, wordDict) {
const dictionary=new Set(wordDict),suffixes=Array.from({length:s.length+1},()=>[]);suffixes[s.length]=[''];for(let start=s.length-1;start>=0;start--)for(let end=start+1;end<=Math.min(s.length,start+10);end++){const word=s.slice(start,end);if(dictionary.has(word))for(const tail of suffixes[end])suffixes[start].push(word+(tail?' '+tail:''));}return suffixes[0];
}
function wordBreak(s, wordDict) { return solve(s, wordDict); }
class Solution {wordBreak(s, wordDict) { return solve(s, wordDict); }}
module.exports=solve;
module.exports.wordBreak=wordBreak;
module.exports.Solution=Solution;
