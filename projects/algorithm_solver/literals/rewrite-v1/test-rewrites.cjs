"use strict";
const assert=require('node:assert/strict'),vm=require('node:vm');
const {rename,graph}=require('./generate.cjs');
const evaluate=(s,args)=>{const context={args};vm.createContext(context);return JSON.stringify(vm.runInContext(s+'\nsolve(...args)',context));};
const cases=[
 ['function solve(values){let result=0;for(const value of values){result+=value;}return result;}',[[1,2,3]]],
 ['function solve(a){let x=1;function f(y){let z=2;return x+y+z;}return f(a);}',[4]],
 ['function solve(a){let x=1;{let y=2;{let z=3;x+=y+z;}}return x+a;}',[4]],
 ['function solve(a){let x=a;{let x=2;a+=x;}return x+a;}',[3]],
 ['function solve(a){const key=a;const object={key};return object.key;}',[7]],
 ['class Holder{constructor(value){this.value=value;}get(){return this.value;}}function solve(input){return new Holder(input).get();}',[9]],
 ['function solve(n){function rec(k){return k===0?1:k*rec(k-1);}return rec(n);}',[5]],
 ['function solve(a){let x=0;for(let i=0;i<a;i++)x+=i;for(let j=0;j<a;j++)x+=j;return x;}',[5]],
 ['function helper(values){let result=0;for(const value of values)result+=value;return result;}function solve(values){return helper(values)+helper([1]);}',[[2,3]]],
 ['function solve(values){const [left,right]=values;return {left,right};}',[[3,4]]],
 ['function solve(input){const value=input;return function(other){return value+other;}(3);}',[4]],
 ['function solve(input){try{throw input;}catch(problem){return problem+1;}}',[7]]
];
let checks=0;
for(const [source,args]of cases)for(const mode of ['scope','role']){const out=rename(source,mode);assert.deepEqual(graph(source),graph(out));assert.equal(evaluate(out,args),evaluate(source,args));assert.equal(rename(out,mode),out);checks++;}
assert.throws(()=>rename('function solve(x){return eval(x);}'),/reflective/);checks++;
const one=rename('function solve(x){return helper(x);}function helper(values){let out=0;for(const v of values)out+=v;return out;}');
const two=rename('function solve(x){const temp=3;return helper(x)+temp;}function helper(data){let total=0;for(const item of data)total+=item;return total;}');
assert.equal(one.slice(one.indexOf('function h')),two.slice(two.indexOf('function h')));checks++;
console.log(JSON.stringify({passed:checks,cases:cases.length,modes:2}));
