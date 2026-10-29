"use strict";
const fs=require('fs'),path=require('path');
const root=__dirname;
function collect(x,s,unique=false){if(x===null||typeof x!=='object')return;if(s.has(x)){if(unique)throw Error('mutable result alias');return;}s.add(x);for(const v of Object.values(x))collect(v,s,unique);}
function invoke(c,official){const mod=require(path.join(root,'javascript',c.id+'.js')),args=JSON.parse(JSON.stringify(c.args)),before=JSON.stringify(args),inputs=new Set();collect(args,inputs);const result=(official?mod[c.name]:mod)(...args);if(JSON.stringify(args)!==before)throw Error('argument mutation');const out=new Set();collect(result,out,true);for(const x of out)if(inputs.has(x))throw Error('input/result alias');return result;}
const cases=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(cases.map(c=>{try{return {result:invoke(c,false),wrapper:invoke(c,true)};}catch(error){return {error:error.stack};}})));
