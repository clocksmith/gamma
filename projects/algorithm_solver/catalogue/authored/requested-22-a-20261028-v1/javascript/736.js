"use strict";
function solve(expression) {
const tokens=expression.replace(/\(/g,'( ').replace(/\)/g,' )').split(' ').filter(t=>t.length),bindings=new Map(),frames=[],alpha=c=>c>='a'&&c<='z';let result=null,position=0;while(position<tokens.length){const token=tokens[position++];if(token==='('){frames.push({op:tokens[position++],values:[],name:null,bound:[],body:null});continue;}let value,frame=frames.length?frames[frames.length-1]:null;if(token===')'){frame=frames.pop();if(frame.op==='add')value=frame.values[0]+frame.values[1];else if(frame.op==='mult')value=frame.values[0]*frame.values[1];else{value=frame.body;for(const name of frame.bound)bindings.get(name).pop();}}else if(frame!==null&&frame.op==='let'&&frame.name===null&&alpha(token[0])&&tokens[position]!==')'){frame.name=token;continue;}else if(alpha(token[0])){const stack=bindings.get(token);value=stack[stack.length-1];}else value=Number(token);if(!frames.length){result=value;continue;}const parent=frames[frames.length-1];if(parent.op!=='let')parent.values.push(value);else if(parent.name!==null){if(!bindings.has(parent.name))bindings.set(parent.name,[]);bindings.get(parent.name).push(value);parent.bound.push(parent.name);parent.name=null;}else parent.body=value;}return result;
}
function evaluate(expression) { return solve(expression); }
module.exports=solve;
module.exports.evaluate=evaluate;
