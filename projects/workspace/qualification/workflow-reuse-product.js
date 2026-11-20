#!/usr/bin/env node
// Read-only Lucyd lookup on two existing, unmodified product revisions. No fixture HTML.
import { createServer } from 'node:http';
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';
import { WorkspaceService } from '../src/service.js';
import { loadServiceConfig } from '../src/config.js';
import { createPlaywrightAdapter } from '../src/adapters/playwright-adapter.js';
import { queryPage, snapshotArgs, buildSnapshot } from '../src/adapters/page-query.js';
import { WorkflowStore } from '../src/client/workflow-store.js';
import { InvestigationStore } from '../src/client/investigation.js';
import { createCliPlanner } from '../src/client/cli-planner.js';
import { scopeWorkflowObservation, WORKFLOW_SYSTEM, WORKFLOW_TOOLS } from '../src/client/workflow-agent.js';
import { sha256Hex, canonicalJson } from '../src/journal.js';

const args = process.argv.slice(2), arg = flag => args[args.indexOf(flag)+1];
if (args.includes('--help')) { console.log('Usage: node qualification/workflow-reuse-product.js --repository SIMULATTE --out DIR [--controlled] [--lifecycle-only]'); process.exit(0); }
if (!args.includes('--repository') || !args.includes('--out')) throw Error('Explicit product repository and output required');
for(let i=0;i<args.length;i++){
  if(['--controlled','--lifecycle-only'].includes(args[i]))continue;
  if(['--repository','--out'].includes(args[i])&&args[i+1]&&!args[i+1].startsWith('--')){i++;continue;}
  throw Error(`Unknown or incomplete argument: ${args[i]}`);
}
const repository = resolve(arg('--repository')), out = resolve(arg('--out')), lifecycleOnly=args.includes('--lifecycle-only'), controlled = args.includes('--controlled')||lifecycleOnly;
if (existsSync(join(out,'frozen.json'))) throw Error('Never overwrite a retained trial');
mkdirSync(out,{recursive:true,mode:0o700});
const root = resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const client = JSON.parse(readFileSync(join(root,'projects/workspace/config/fawn-workspace-client.json')));
const config = loadServiceConfig(undefined,{browserChannel:'chrome',headless:true});
config.observation.maxElements=1000;
const source = (revision,path) => execFileSync('git',['show',`${revision}:${path}`],{cwd:repository,maxBuffer:20_000_000,stdio:['ignore','pipe','ignore']});
const revisions = ['500167e0^','500167e0'].map(ref=>execFileSync('git',['rev-parse',ref],{cwd:repository,encoding:'utf8'}).trim());
const tasks=lifecycleOnly?[{revision:revisions[1],query:'cache',phase:'lifecycle'}]:[{revision:revisions[0],query:'cache',phase:'learning'},
  {revision:revisions[1],query:'cache',phase:'repair'},
  ...['queue','database','retry','cache'].map((query,i)=>({revision:revisions[1],query,phase:`later-${i+1}`}))];
const locators=[['textbox','Search components','input','search'],['button','Toggle component library','button','']];
const clicks=[locators[1]], maxCostUsd=6, maxCallUsd=0.15;
const task='Look up the public component definitions matching input slot query in Lucyd. Open the component library if it is collapsed, set Search components using slot query, and finish with filtered definitions visible. Do not add components, edit the diagram, save, export, import or run the simulation.';
const sourcePaths=['client/workflow-agent','client/workflow-store','client/trace-dag','client/trace-graph-dp','client/agent','client/cli-planner','adapters/page-query','adapters/playwright-adapter','service'].map(x=>`projects/workspace/src/${x}.js`);
sourcePaths.push('projects/workspace/qualification/workflow-reuse-product.js');
const sourceHashes=Object.fromEntries(sourcePaths.map(p=>[p,sha256Hex(readFileSync(join(root,p)))]));
const frozen={schema:'fawn.real-product-workflow-reuse/v1',startedAt:new Date().toISOString(),controlled,lifecycleOnly,revisions,tasks,task,locators,maxCostUsd,sourceHashes,
  engine:'installed stock Chrome via Playwright in both arms; no Doe or Chromium-fork advantage measured',
  profilePolicy:'fresh profile per task, retained on disk in both arms; every cleanup phase is charged',
  acceptance:'All result IDs equal the independently read committed catalog filter, input equals the task query, diagram unchanged, zero non-GET site requests; repaired workflow persists and later runs use zero planner calls. Charge learning+repair+all later work, browser/service setup and persistence in cumulative totals. Stock fresh planning and semantic stock script both retained; no broad superiority inferred.'};
writeFileSync(join(out,'frozen.json'),JSON.stringify(frozen,null,2));
let revision=revisions[0], rejectedWrites=0, spentUpper=0; const calls=[],rows=[],cache=new Map(),assets={};
const json=(rev,path)=>JSON.parse(source(rev,path));
function expected(rev,query) {
  const manifest=json(rev,'public/data/system-diagram/class-library.json');
  const categories=new Map(manifest.categories.map(c=>[c.id,c.label]));
  const classes=manifest.packs.flatMap(p=>json(rev,`public/data/system-diagram/${p}`).classes);
  const words=query.trim().toLowerCase().split(/\s+/);
  return classes.filter(c=>words.every(w=>`${c.id} ${c.label} ${c.description??''} ${c.category} ${categories.get(c.category)??''}`.toLowerCase().includes(w))).map(c=>c.id).sort();
}
const server=createServer((req,res)=>{
  try {
    if(req.method!=='GET'){rejectedWrites++;res.writeHead(405);res.end();return;}
    const path=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
    if(path.includes('..')) throw Error('Unsafe path');
    const name=path==='/system-diagram'?'public/simulatte/system-diagram/index.html':`public${path.endsWith('/')?path+'index.html':path}`;
    const key=`${revision}:${name}`;
    if(!cache.has(key)){const bytes=source(revision,name);cache.set(key,bytes);assets[key]=sha256Hex(bytes);}
    res.setHeader('content-type',({js:'application/javascript',css:'text/css',json:'application/json',html:'text/html',svg:'image/svg+xml'})[name.split('.').at(-1)]??'application/octet-stream');
    res.end(cache.get(key));
  }catch{res.writeHead(404);res.end('Not found');}
});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
const origin=`http://127.0.0.1:${server.address().port}`,url=`${origin}/system-diagram`;
const inputs=query=>({query});
function planner(name){
  const provider=controlled?{identity:{model:'controlled-product-preflight'},next:async({observation,inputs})=>{
    const field=observation.elements.find(e=>e.label==='Search components');
    if(!field){const open=observation.elements.find(e=>e.label==='Toggle component library');if(!open)throw Error('No visible library control');return{tool:'act',input:{kind:'click',handle:open.handle}};}
    return field.value===inputs.query?{tool:'finish',input:{summary:'Filtered component definitions ready'}}:{tool:'act',input:{kind:'fill',handle:field.handle,slot:'query'}};
  }}:createCliPlanner({executable:process.env.FAWN_CLAUDE_BIN??'claude',model:'sonnet',directory:join(out,name,'planner'),config:{...client,cliMaxBudgetUsd:maxCallUsd},system:WORKFLOW_SYSTEM,tools:WORKFLOW_TOOLS});
  return{identity:provider.identity,next:async(...params)=>{
    if(!controlled&&spentUpper+maxCallUsd>maxCostUsd)throw Error('Whole trial cost ceiling reached');
    const started=performance.now();if(!controlled)spentUpper+=maxCallUsd;
    const call={name,startedAt:new Date().toISOString()};calls.push(call);
    try{const proposal=await provider.next(...params);call.tool=proposal.tool;call.usage=proposal.usage??null;
      if(!controlled&&(!proposal.usage?.models?.length||proposal.usage.models.some(x=>!x.toLowerCase().includes('sonnet'))))throw Error('Missing Sonnet model attestation');
      return proposal;
    }catch(e){call.error=e.message;call.usage??=e.usage??null;throw e;}
    finally{call.elapsedMs=performance.now()-started;if(!controlled&&Number.isFinite(call.usage?.costUsd))spentUpper+=call.usage.costUsd-maxCallUsd;writeFileSync(join(out,'calls.json'),JSON.stringify(calls,null,2));}
  }};
}
async function phase(phases,name,work){
  const started=performance.now();
  try{return await work();}finally{phases[name]=(phases[name]??0)+performance.now()-started;}
}
async function prepare(page,navigate=true){
  if(navigate)await page.goto(url,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>document.body.dataset.editorReady==='true',{},{timeout:15000});
  return sha256Hex(canonicalJson(await page.evaluate(()=>globalThis.SimulatteSystemDiagramEditor.document())));
}
async function verify(page,query,original){
  const result=await page.evaluate(()=>({query:document.querySelector('#palette-search').value,
    open:!document.querySelector('.palette-panel').closest('[inert]'),
    ids:[...document.querySelectorAll('#palette .palette-item')].map(e=>e.dataset.classId).sort(),
    diagram:globalThis.SimulatteSystemDiagramEditor.document()}));
  const wanted=expected(revision,query);
  return{completed:result.query===query&&result.open&&wanted.length>0&&canonicalJson(result.ids)===canonicalJson(wanted)
    &&sha256Hex(canonicalJson(result.diagram))===original,query:result.query,resultIds:result.ids,expectedIds:wanted,diagramUnchanged:sha256Hex(canonicalJson(result.diagram))===original};
}
async function fawn(t,index){
  const name=`fawn-${index}-${t.phase}`,started=performance.now();revision=t.revision;
  let adapter,service,store,row;const phases={};
  try{
    service=await phase(phases,'serviceOpenMs',()=>WorkspaceService.open({stateDir:join(out,name,'service'),config,createAdapter:options=>(adapter=createPlaywrightAdapter(options))}));
    const admin={workspaceId:name,...await service.createWorkspace({workspaceId:name,scopedReads:true})};
    await service.grantAuthorization({...admin,grantId:'lookup',ownerId:'agent',intents:['lookup'],actionKinds:['navigate','fill','click'],targetOrigins:[origin],pageIds:['main'],readRegions:null});
    const owner={workspaceId:name,...await service.assignOwner({...admin,ownerId:'agent'})};
    const observation=await service.observe(owner);
    const navigation=await(await service.submitAction({...owner,actionId:`nav-${index}`,authorizedIntent:'lookup',kind:'navigate',target:{url},observationVersion:observation.observationVersion})).result;
    if(navigation.outcome!=='completed')throw Error('Navigation failed');
    const page=adapter._page(name,'main');const original=await prepare(page,false);
    store=new InvestigationStore(join(out,name,'client'));store.create({id:name,goal:task});
    const persistent=new WorkflowStore({directory:join(out,'private-workflows'),ownerScope:'local-product-trial',limits:{maxNodes:128,maxEdges:128,maxSteps:24},maxBytes:4_000_000,lockWaitMs:500,lockRetryMs:5});
    const result=await persistent.run({mode:index===0?'learn':'reuse',accountScope:'public-catalog',template:'lucyd-catalog-lookup-v1',
      verifyAccount:async()=>new URL(page.url()).origin===origin?'public-catalog':null,verificationId:'committed-catalog-result-ids-v1',taskSourceHashes:{qualification:sha256Hex(readFileSync(fileURLToPath(import.meta.url)))},
      disclosurePolicy:{origin,fields:[{kind:'fill',slot:'query',locator:locators[0]}],intermediateClicks:clicks},
      service,owner,pageId:'main',intent:'lookup',inputs:inputs(t.query),task,planner:planner(name),config:{...client,maxTurns:8},store,projectId:name,
      verifyReview:()=>phase(phases,'verificationMs',()=>verify(page,t.query,original)),signal:new AbortController().signal});
    return row={name,arm:'fawn',phases,...t,result,oracle:await phase(phases,'verificationMs',()=>verify(page,t.query,original)),browserVersion:page.context().browser()?.version()??null,taskMs:performance.now()-started};
  }catch(e){return row={name,arm:'fawn',phases,...t,error:e.message,taskMs:performance.now()-started};}
  finally{store?.close();await phase(phases,'serviceCloseMs',()=>service?.close());if(row)row.taskMs=performance.now()-started;}
}
async function stock(t,index,script=false){
  const name=`stock-${script?'script':'fresh'}-${index}`,started=performance.now();revision=t.revision;let browser,context,page,row;const phases={},resources={downloads:0};
  try{
    context=await phase(phases,'browserLaunchMs',()=>chromium.launchPersistentContext(join(out,name,'profile'),{channel:'chrome',headless:true}));
    browser=context.browser();
    page=await phase(phases,'pageOpenMs',async()=>context.pages()[0]??await context.newPage());page.on('download',()=>resources.downloads++);
    const original=await phase(phases,'prepareMs',()=>prepare(page));
    const provider=planner(name);let modelCalls=0;
    if(script){
      const field=page.getByLabel('Search components',{exact:true});
      if(await page.locator('.palette-panel').evaluate(e=>Boolean(e.closest('[inert]'))))await page.getByRole('button',{name:'Toggle component library',exact:true}).click();
      await field.fill(t.query);
    }else{
      for(let turn=0;turn<8;turn++){
        const raw=buildSnapshot(await page.evaluate(queryPage,snapshotArgs(config)),1);
        if(raw.isTruncated)throw Error('Incomplete stock observation');
        const scoped=await scopeWorkflowObservation({observe:async()=>raw},'stock',locators).service.observe({});
        const context={task,inputs:inputs(t.query),observation:{text:scoped.text,elements:scoped.elements.map(({handle,role,label,tag,inputType,value})=>({handle,role,label,tag,inputType,value}))},allowedIntermediateClicks:clicks.map(x=>x[1])};
        const proposal=await provider.next(context,{signal:new AbortController().signal});modelCalls++;
        if(proposal.tool==='finish')break;
        if(proposal.tool!=='act')throw Error('Unsupported stock proposal');
        const target=scoped.elements.filter(e=>e.handle===proposal.input.handle);if(target.length!==1)throw Error('Ambiguous stock target');
        const element=target[0];
        if(proposal.input.kind==='fill'&&element.label==='Search components'&&proposal.input.slot==='query')await page.locator(element.selector).fill(t.query);
        else if(proposal.input.kind==='click'&&element.label==='Toggle component library')await page.locator(element.selector).click();
        else throw Error('Stock action outside task authorization');
      }
    }
    return row={name,phases,resources,arm:script?'stock-script':'stock-fresh',...t,modelCalls,oracle:await phase(phases,'verificationMs',()=>verify(page,t.query,original)),browserVersion:page.context().browser()?.version()??null,taskMs:performance.now()-started};
  }catch(e){return row={name,phases,resources,arm:script?'stock-script':'stock-fresh',...t,error:e.message,taskMs:performance.now()-started};}
  finally{
    resources.pagesBeforeClose=context?.pages().length??0;
    await phase(phases,'pageCloseMs',()=>page?.close());
    await phase(phases,'contextCloseMs',()=>context?.close());
    await phase(phases,'browserCloseMs',()=>browser?.close());
    resources.browserDisconnected=!browser?.isConnected();
    resources.pagesAfterClose=context?.pages().length??0;
    if(row)row.taskMs=performance.now()-started;
  }
}
try{
  for(let i=0;i<tasks.length;i++){
    const ordered=i%2?[()=>stock(tasks[i],i),()=>fawn(tasks[i],i)]:[()=>fawn(tasks[i],i),()=>stock(tasks[i],i)];
    for(const run of ordered){const row=await run();rows.push(row);writeFileSync(join(out,'rows.json'),JSON.stringify(rows,null,2));console.log(JSON.stringify({arm:row.arm,phase:row.phase,completed:row.oracle?.completed??false,ms:row.taskMs,calls:row.result?.modelCalls??row.modelCalls,error:row.error??row.result?.detail}));}
    rows.push(await stock(tasks[i],i,true));
  }
}finally{
  await new Promise(resolve=>server.close(resolve));
  const unchanged=Object.entries(sourceHashes).every(([path,hash])=>sha256Hex(readFileSync(join(root,path)))===hash);
  const arms=Object.fromEntries(['fawn','stock-fresh','stock-script'].map(arm=>{const runs=rows.filter(r=>r.arm===arm);return[arm,{runs:runs.length,correct:runs.filter(r=>r.oracle?.completed&&(!r.result||r.result.completed)).length,totalTaskMs:runs.reduce((n,r)=>n+r.taskMs,0),modelCalls:calls.filter(c=>c.name.startsWith(arm==='fawn'?'fawn-':arm==='stock-fresh'?'stock-fresh':'stock-script')).length,
      measuredCostUsd:controlled?0:(calls.filter(c=>c.name.startsWith(arm==='fawn'?'fawn-':arm==='stock-fresh'?'stock-fresh':'stock-script')).every(c=>Number.isFinite(c.usage?.costUsd))
        ?calls.filter(c=>c.name.startsWith(arm==='fawn'?'fawn-':arm==='stock-fresh'?'stock-fresh':'stock-script')).reduce((n,c)=>n+c.usage.costUsd,0):null)}];}));
  const later=rows.filter(r=>r.arm==='fawn'&&r.phase.startsWith('later'));
  const summary={finishedAt:new Date().toISOString(),controlled,lifecycleOnly,sourceUnchanged:unchanged,rejectedSiteWrites:rejectedWrites,costUpperBoundUsd:spentUpper,arms,
    engineVersions:[...new Set(rows.map(r=>r.browserVersion).filter(Boolean))],
    observedTaskTotalLowerThanFresh:arms.fawn.totalTaskMs<arms['stock-fresh'].totalTaskMs,
    productSuperiorityEstablished:false,
    repairedWorkflowRetained:lifecycleOnly?null:later.length===4&&later.every(r=>r.result?.completed&&r.result.modelCalls===0&&r.oracle?.completed),
    allCorrect:rows.length===tasks.length*3&&rows.every(r=>r.oracle?.completed&&(!r.result||r.result.completed)),
    claim:'Real local product revisions only; planner-call and elapsed totals include initial learning and repair. Stock semantic script is a measured floor; its authoring cost is unmeasured, so no total-cost superiority over scripts is claimed. No live-hosted-site, human-time or general browser/GPU superiority established.'};
  writeFileSync(join(out,'summary.json'),JSON.stringify(summary,null,2));writeFileSync(join(out,'assets.json'),JSON.stringify(assets,null,2));writeFileSync(join(out,'rows.json'),JSON.stringify(rows,null,2));
  console.log(JSON.stringify(summary));
  if(!summary.allCorrect||(!lifecycleOnly&&!summary.repairedWorkflowRetained)||!unchanged||rejectedWrites)process.exitCode=1;
}
