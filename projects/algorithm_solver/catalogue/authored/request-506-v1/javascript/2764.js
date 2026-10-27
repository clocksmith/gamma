/* Original candidate for LeetCode 2764. Contract: https://leetcode.com/problems/is-array-a-preorder-of-some-binary-tree/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time and space; input describes a valid binary tree as required */
"use strict";
function solve(nodes){let st=[];for(let i=0;i<nodes.length;i++){let[node,parent]=nodes[i];if(i===0){if(parent!==-1)return false;}else{while(st.length&&st[st.length-1]!==parent)st.pop();if(!st.length)return false;}st.push(node);}return true;}
module.exports = solve;
