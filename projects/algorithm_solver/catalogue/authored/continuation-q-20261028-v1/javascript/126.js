"use strict";
function solve(beginWord, endWord, wordList) {
const words=new Set(wordList);if(!words.has(endWord))return [];const distance=new Map([[beginWord,0]]),parents=new Map(),queue=[beginWord];let shortest=Infinity;for(let head=0;head<queue.length;head++){const current=queue[head],depth=distance.get(current);if(depth>=shortest)continue;for(let i=0;i<current.length;i++)for(let code=97;code<=122;code++){const char=String.fromCharCode(code);if(char===current[i])continue;const following=current.slice(0,i)+char+current.slice(i+1);if(!words.has(following))continue;if(!distance.has(following)){distance.set(following,depth+1);parents.set(following,[]);queue.push(following);}if(distance.get(following)===depth+1){parents.get(following).push(current);if(following===endWord)shortest=depth+1;}}}if(!distance.has(endWord))return [];const answer=[],pending=[[endWord,[endWord]]];while(pending.length){const [word,path]=pending.pop();if(word===beginWord)answer.push(path.slice().reverse());else for(const parent of parents.get(word))pending.push([parent,path.concat(parent)]);}return answer;
}
function findLadders(beginWord, endWord, wordList) { return solve(beginWord, endWord, wordList); }
class Solution {findLadders(beginWord, endWord, wordList) { return solve(beginWord, endWord, wordList); }}
module.exports=solve;
module.exports.findLadders=findLadders;
module.exports.Solution=Solution;
