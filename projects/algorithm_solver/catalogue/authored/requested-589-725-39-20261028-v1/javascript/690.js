"use strict";
function solve(employees,id){const lookup=new Map(employees.map(e=>[e.id,e])),seen=new Set(),stack=[id];let total=0;while(stack.length){const key=stack.pop();if(seen.has(key))continue;seen.add(key);const e=lookup.get(key);total+=e.importance;for(const sub of e.subordinates)stack.push(sub);}return total;}

function getImportance(employees, id){return solve(employees, id);}
module.exports=solve;
module.exports.getImportance=getImportance;
