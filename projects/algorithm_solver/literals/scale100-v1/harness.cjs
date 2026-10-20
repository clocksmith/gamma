"use strict";
const fs=require('fs'),vm=require('vm');
function aliasEdges(args,result){
 const seen=new WeakMap(),edges=[];
 function visit(value,at){
  if(value===null||typeof value!=='object')return;
  if(seen.has(value)){edges.push([at,seen.get(value)]);return;}
  seen.set(value,at);
  for(const [key,child]of Object.entries(value))visit(child,at+'.'+key);
 }
 visit(args,'args');visit(result,'result');return edges;
}
function main(){
 const source=fs.readFileSync('program.js','utf8'),packet=JSON.parse(fs.readFileSync('inputs.json'));
 vm.runInThisContext(source,{filename:'program.js',timeout:1000});
 const target=vm.runInThisContext(packet.entry);
 for(let i=0;i<packet.calls.length;i++){
  const args=packet.calls[i].args,before=JSON.parse(JSON.stringify(args));let record;
  try{
   const result=target(...args);
   record={i,result,args_before:before,args_after:args,alias_edges:aliasEdges(args,result)};
  }catch(e){record={i,error:String(e),args_before:before,args_after:args};}
  process.stdout.write(JSON.stringify(record)+'\n');
 }
 process.stdout.write(JSON.stringify({done:packet.calls.length})+'\n');
}
if(require.main===module)main();
module.exports={aliasEdges};
