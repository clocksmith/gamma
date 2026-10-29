"use strict";
// Fixed native-class observer for development checks. No solve fallback.
const fs=require('fs'),path=require('path');
const root=__dirname;
function observe(packet){const {id,args}=packet;const names={1622:'Fancy',1656:'OrderedStream'};if(!names[id])throw Error('unknown native problem');const { [names[id]]: Native }=require(path.join(root,'javascript',id+'.js'));if(typeof Native!=='function')throw Error('named native class required');const before=JSON.stringify(args),[operations,rows]=args,receiver=new Native(...rows[0]),outputs=[null],seen=new Set();
 if(Object.getPrototypeOf(receiver)!==Native.prototype)throw Error('original receiver required');
 for(let i=1;i<operations.length;i++){const operation=operations[i],method=Native.prototype[operation];if(typeof method!=='function')throw Error('original prototype method required');const value=method.apply(receiver,rows[i]);
  if(id===1622&&operation!=='getIndex'){if(value!==undefined)throw Error('void method returned value');outputs.push(null);}
  else{if(id===1622&&(!Number.isInteger(value)))throw Error('query must return integer');if(id===1656){if(!Array.isArray(value)||value.some(v=>typeof v!=='string'))throw Error('insert must return string list');if(seen.has(value))throw Error('returned chunk alias');seen.add(value);}outputs.push(value);}
 }
 if(JSON.stringify(args)!==before)throw Error('input mutation');return outputs;
}
const input=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(input.map(packet=>{try{return {result:observe(packet)};}catch(e){return {error:e.stack};}})));
