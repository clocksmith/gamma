/* Original candidate for LeetCode 1993. Contract: https://leetcode.com/problems/operations-on-tree/
Development tests only; not admitted or independently qualified.
Batch adapter solve(operations, arguments) follows official class-call arrays, constructor result null.
Complexity: O(n) per upgrade, O(1) lock/unlock, O(n+q) space */
"use strict";
function solve(operations,args){const parent=args[0][0],children=parent.map(()=>[]),locked=parent.map(()=>0),out=[null];for(let i=1;i<parent.length;i++)children[parent[i]].push(i);for(let i=1;i<operations.length;i++){let [node,user]=args[i],op=operations[i],ok;if(op==='lock'){ok=!locked[node];if(ok)locked[node]=user;}else if(op==='unlock'){ok=locked[node]===user;if(ok)locked[node]=0;}else{ok=true;for(let p=node;p!==-1;p=parent[p])if(locked[p]){ok=false;break;}let descendants=[],stack=[...children[node]];while(stack.length){const v=stack.pop();descendants.push(v);for(const c of children[v])stack.push(c);}ok=ok&&descendants.some(v=>locked[v]!==0);if(ok){for(const v of descendants)locked[v]=0;locked[node]=user;}}out.push(!!ok);}return out;}
module.exports = solve;
