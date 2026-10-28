"use strict";
function solve(chunks, queries) {
const words=chunks.join('').match(/[a-z]+(?:-[a-z]+)*/g)||[],counts=new Map();for(const word of words)counts.set(word,(counts.get(word)||0)+1);return queries.map(word=>counts.get(word)||0);
}
function countWordOccurrences(chunks, queries) { return solve(chunks, queries); }
module.exports=solve;
module.exports.countWordOccurrences=countWordOccurrences;
