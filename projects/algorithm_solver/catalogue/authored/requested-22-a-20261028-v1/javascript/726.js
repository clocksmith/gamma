"use strict";
function solve(formula) {
const counts=new Map(),multipliers=[1];let pending=1,i=formula.length-1;const digit=c=>c>='0'&&c<='9',lower=c=>c>='a'&&c<='z';while(i>=0){const c=formula[i];if(digit(c)){let j=i;while(digit(formula[j-1]))j--;pending=Number(formula.slice(j,i+1));i=j-1;}else if(c===')'){multipliers.push(multipliers[multipliers.length-1]*pending);pending=1;i--;}else if(c==='('){multipliers.pop();i--;}else{let j=i;while(lower(formula[j]))j--;const name=formula.slice(j,i+1);counts.set(name,(counts.get(name)||0)+pending*multipliers[multipliers.length-1]);pending=1;i=j-1;}}return [...counts.keys()].sort().map(name=>name+(counts.get(name)>1?String(counts.get(name)):'')).join('');
}
function countOfAtoms(formula) { return solve(formula); }
module.exports=solve;
module.exports.countOfAtoms=countOfAtoms;
