/* Original candidate for LeetCode 3157. Contract: https://leetcode.com/problems/find-the-level-of-tree-with-minimum-sum/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Explicit JSON adapter: nonempty root compact BFS values with null children; root level1, ties choose smallest level.
Complexity: O(n) time and space */
"use strict";
function build(a){if(!a.length||a[0]===null)return [];let ns=[[a[0],-1,-1]],p=1;for(let q=0;q<ns.length&&p<a.length;q++)for(let s=1;s<=2;s++){if(p<a.length&&a[p]!==null){ns[q][s]=ns.length;ns.push([a[p],-1,-1]);}p++;}return ns;}
function solve(root){let ns=build(root),level=[0],depth=1,best=Infinity,answer=1;while(level.length){let total=0,next=[];for(const i of level){total+=ns[i][0];for(const c of ns[i].slice(1))if(c>=0)next.push(c);}if(total<best){best=total;answer=depth;}depth++;level=next;}return answer;}
module.exports = solve;
