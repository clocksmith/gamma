"use strict";
// Diagnostic CPU attribution entry for measure_observer_cost.py --phases.
// Published in the sandbox as harness.cjs. The observer under test is
// observer.cjs and its graph helper is native_graphs.cjs. Programs are
// synthetic no-ops. This is not an execution helper and is never dispatched
// by a controller.
const T={},cpu=()=>{const u=process.cpuUsage();return (u.user+u.system)/1000;};
function wrap(owner,name,label){const f=owner[name];owner[name]=function(...a){const t=cpu();try{return f.apply(this,a);}finally{T[label]=(T[label]||0)+cpu()-t;}};}
const startup=cpu(),NG=require('./native_graphs.cjs');
wrap(NG,'build','build');wrap(NG.Graph.prototype,'snapshot','snapshot');wrap(NG.Graph.prototype,'linked','linked');
wrap(JSON,'parse','json_parse');wrap(JSON,'stringify','json_stringify');
const {observe}=require('./observer.cjs'),packet=JSON.parse(require('fs').readFileSync('inputs.json','utf8')),ns=require('./program.cjs');let observeMs=0;
for(let i=0;i<packet.calls.length;i++){const a=cpu();let record;try{record={i,...observe(ns,packet.problem_id,packet.calls[i])};}catch(e){record={i,error:String(e)};}observeMs+=cpu()-a;JSON.stringify(record);}
process.stderr.write('PHASES '+JSON.stringify({startup:Math.round(startup),total:Math.round(cpu()),observe:Math.round(observeMs),...Object.fromEntries(Object.entries(T).map(([k,v])=>[k,Math.round(v)]))})+'\n');
