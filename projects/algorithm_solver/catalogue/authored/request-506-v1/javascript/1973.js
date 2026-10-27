/* Original candidate for LeetCode 1973. Contract: https://leetcode.com/problems/count-nodes-equal-to-sum-of-descendants/
Definition additionally checked against public doocs/leetcode documentation (CC-BY-SA-4.0); original implementation.
Development tests only; not admitted or independently qualified.
Explicit JSON adapter: root is compact BFS level-order values with null children; output count, native pointer identity is not observable.
Complexity: O(n) time and space */
"use strict";
function build(a){if(!a.length||a[0]===null)return [];let ns=[[a[0],-1,-1]],p=1;for(let q=0;q<ns.length&&p<a.length;q++)for(let s=1;s<=2;s++){if(p<a.length&&a[p]!==null){ns[q][s]=ns.length;ns.push([a[p],-1,-1]);}p++;}return ns;}
function solve(root){let ns=build(root),sum=Array(ns.length).fill(0),ans=0;for(let i=ns.length-1;i>=0;i--){let[v,l,r]=ns[i],s=(l>=0?sum[l]:0)+(r>=0?sum[r]:0);if(s===v)ans++;sum[i]=s+v;}return ans;}
module.exports = solve;
