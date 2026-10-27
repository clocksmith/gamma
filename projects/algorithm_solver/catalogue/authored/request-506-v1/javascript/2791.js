/* Original candidate for LeetCode 2791. Contract: https://leetcode.com/problems/count-paths-that-can-form-a-palindrome-in-a-tree/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(26n) time, O(n) space; masks use 26 bits, counts fit JS Number */
"use strict";
function solve(parent,s){let children=parent.map(()=>[]);for(let i=1;i<parent.length;i++)children[parent[i]].push(i);let stack=[[0,0]],counts=new Map(),ans=0;while(stack.length){let [u,mask]=stack.pop();ans+=counts.get(mask)||0;for(let b=0;b<26;b++)ans+=counts.get(mask^(1<<b))||0;counts.set(mask,(counts.get(mask)||0)+1);for(const v of children[u])stack.push([v,mask^(1<<(s.charCodeAt(v)-97))]);}return ans;}
module.exports = solve;
