'use strict';
// Trusted flat integer-array observer; expected outputs are never supplied.
const fs = require('fs');
const packet = JSON.parse(fs.readFileSync('inputs.json','utf8'));
const candidate = require('./program.js');
for (let i=0;i<packet.calls.length;i++) {
 let record;
 try {
  const args=packet.calls[i].args;
  const before=[args[0].slice()];
  const held=args[0];
  const value=packet.entry==='class' ? new candidate.Solution().duplicateZeros(args[0]) : candidate.duplicateZeros(args[0]);
  record={i,result:typeof value==='undefined'?null:value,result_type:typeof value,args_before:before,args_after:args,same_input_object:args[0]===held};
 } catch(error) { record={i,error:error.name+': '+String(error.message).slice(0,300)}; }
 process.stdout.write(JSON.stringify(record)+'\n');
}
process.stdout.write(JSON.stringify({done:packet.calls.length})+'\n');
