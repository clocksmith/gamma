// Audit copy of ../independent-holdout/frozen/run.mjs. Switches (environment): DIAG_GAMMA, DIAG_PIN,
// DIAG_ARMS, DIAG_FIXED_POLICY=1, DIAG_EVAL_ACCOUNT, DIAG_OUT. See README.md. Diagnostic only.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {appendFileSync,mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
const [base] = process.argv.slice(2);
const root=resolve(base,process.env.DIAG_GAMMA||'gamma'), frozen=resolve(base,'frozen'), out=resolve(base,process.env.DIAG_OUT||'receipt');
const FIXED=process.env.DIAG_FIXED_POLICY==='1', ARMS=(process.env.DIAG_ARMS||'exact,suffix').split(',');
const pin=process.env.DIAG_PIN||'5b79bceccf6cc0efbba6a35823d02bb8c77f0233';
const git=(...args)=>execFileSync('git',['-C',root,...args],{encoding:'utf8'}).trim();
assert.equal(git('rev-parse','HEAD'),pin);
assert.equal(git('status','--porcelain'),'');
execFileSync('sha256sum',['-c','input-sha256.txt'],{cwd:frozen});
assert.equal(process.env.GAMMATRON_FIXTURE_ONLY,'1');
mkdirSync(out);
const W=resolve(root,'projects/workspace/src');
const imp=p=>import(pathToFileURL(resolve(W,p)).href);
const {TraceDag}=await imp('client/trace-dag.js');
const {runWorkflow}=await imp('client/workflow-agent.js');
const {InvestigationStore}=await imp('client/investigation.js');
const SuffixIndex=ARMS.includes('index')?(await imp('client/suffix-eligibility.js')).SuffixIndex:null;
const sha=x=>createHash('sha256').update(x).digest('hex');
const canon=x=>JSON.stringify(x);
const fixture=JSON.parse(readFileSync(resolve(frozen,'fixtures.json')));
const store=new InvestigationStore(resolve(out,'investigations'));
const limits={maxNodes:64,maxEdges:64,maxSteps:22};
const rows=[];
const slotRolesFor=(w)=>({query:w.queryRole,f1:w.fields[0][0],f2:w.fields[1][0]});
const label=(role,name,tag='input',inputType='text')=>[role,name,tag,inputType];
const button=name=>label('button',name,'button','');
function harness(w,id,inputs,log) {
  const alt=id==='alternate', layout=id==='layout';
  const wrong=id==='wrong-tenant', hidden=id==='hidden-lock', skipped=id==='skipped-approval', duplicate=id==='duplicate-target';
  const origin='https://'+w.id+'.fixture.test', tenant=wrong?w.wrongTenant:w.tenant;
  const negative=wrong||hidden||skipped||duplicate;
  let page=hidden?'approval':skipped||duplicate?'edit':'entry', version=0, approved=duplicate, effects=0;
  const values={query:page==='entry'?'':inputs.query,f1:'',f2:''};
  const q=label('textbox',alt?w.alternate[1]:w.queryLabel), open=button('Open '+w.record);
  const approve=button('Record '+w.approver+' approval'), review=button('Open review');
  const std=w.fields.map(([role,l])=>label('textbox',l));
  const edits=w.fields.map(([role,l])=>label('textbox',layout&&role===w.layout[1]?w.layout[2]:l));
  const decor=label('link',w.layout[0],'a','');
  const allowed=FIXED?[label('textbox',w.alternate[1]),label('textbox',w.queryLabel),open,approve,review,...std,...w.fields.map(([role,l])=>label('textbox',role===w.layout[1]?w.layout[2]:l)),decor]
    :[q,label('textbox',w.queryLabel),open,approve,review,...std,...edits,decor];
  function element(loc,handle, value='', formKey='#form') {
    const [role,label,tag,inputType]=loc;
    return {role,label,tag,inputType,handle,selector:'#'+handle,digest:sha(canon([loc,handle,value])),value,text:label,formKey,isDefaultValue:value==='',attributes:[],actionability:{visible:true,inert:false,disabled:false}};
  }
  function controls() {
    if(page==='entry') return [element(q,'query',values.query),element(open,'open')];
    if(page==='approval') return [element(approve,'approve')];
    if(page==='edit') {
      const fields=[element(edits[0],'f1',values.f1),element(edits[1],'f2',values.f2)];
      if(duplicate) fields.unshift(element(edits[0],'duplicate',values.f1));
      if(layout) fields.reverse().splice(1,0,element(decor,'background','',null));
      return [...fields,element(review,'review')];
    }
    return [];
  }
  const pathname=()=>({entry:alt?w.alternate[0]:w.entry,approval:w.approval,edit:w.edit,review:w.review})[page];
  const observation=()=>({url:origin+pathname(),text:page==='approval'?w.approvalStatus+': '+w.approvalRef:page,observationVersion:version,isTruncated:false,elements:controls()});
  const visibleInitial=sha(canon(observation()));
  const established=new Set(); const actions=[]; const guard=[];
  const assertContext=async()=>{if(tenant!==w.tenant){guard.push('tenant_mismatch');log({event:'guard',why:'tenant_mismatch'});throw Error('tenant_mismatch');}};
  async function authorizeStep(a) {
    let why=null;
    if(hidden) why='prerequisite_locked';
    else if(page==='edit'&&!approved) why='approval_missing';
    else if(page==='edit'&&controls().filter(e=>e.label===edits[0][1]).length!==1) why='ambiguous_target';
    guard.push(why||'allowed');
    log({event:'guard',why:why||'allowed',page,kind:a.kind});
    if(why) throw Error(why);
    established.add(canon([version,a.kind]));
  }
  const service={
    outstanding:async()=>[],
    observe:async()=>observation(),
    submitAction:async cmd=>{
      assert.ok(established.delete(canon([version,cmd.kind])),'Effect must pass same prerequisite check');
      assert.equal(cmd.observationVersion,version,'Fresh version at dispatch');
      const e=controls().filter(y=>y.handle===cmd.target.handle&&y.digest===cmd.target.digest);
      assert.equal(e.length,1);
      const h=e[0].handle;
      // Dedicated loopback-free fixture: no final submit action exists.
      assert.ok(['query','open','approve','f1','f2','review'].includes(h));
      log({event:'effect-intent',actionId:cmd.actionId,page,handle:h,kind:cmd.kind,version});
      actions.push({page,handle:h,kind:cmd.kind});
      effects++;
      if(h==='query'||h==='f1'||h==='f2') values[h]=cmd.params.value;
      else if(h==='open') page='approval';
      else if(h==='approve'){approved=true;page='edit';}
      else if(h==='review') page='review';
      ++version;
      log({event:'effect-outcome',actionId:cmd.actionId,outcome:'completed',version});
      return {result:Promise.resolve({outcome:'completed',isUncertain:false,postObservationVersion:version})};
    }
  };
  const actual=()=>({tenant_id:tenant,[w.queryRole]:values.query,approval:approved?w.approvalRef:null,
    [w.fields[0][0]]:values.f1,[w.fields[1][0]]:values.f2,status:page==='review'?'Ready for review':'Not at review'});
  const expected=id==='teach'?{...w.expected,[w.queryRole]:inputs.query,[w.fields[0][0]]:inputs.f1,[w.fields[1][0]]:inputs.f2}:w.expected;
  const verifyReview=async()=>{const observed=actual();return {completed:!negative&&Object.keys(expected).every(k=>expected[k]===observed[k]),actual:observed};};
  const planner={identity:{model:'deterministic-snapshot-stub'},next:async({observation,inputs})=>{
    log({event:'scripted-decision',page});
    const elm=observation.elements; const has=h=>elm.find(x=>x.handle===h);
    const act=(kind,handle,slot)=>({tool:'act',input:{kind,handle,...(slot?{slot}:{})}});
    if(has('query')&&has('query').value!==inputs.query)return act('fill','query','query');
    if(has('open'))return act('click','open');
    if(has('approve'))return act('click','approve');
    if(has('f1')&&has('f1').value!==inputs.f1)return act('fill','f1','f1');
    if(has('f2')&&has('f2').value!==inputs.f2)return act('fill','f2','f2');
    if(has('review'))return act('click','review');
    if(page==='review')return {tool:'finish',input:{summary:'Review ready for independent verification'}};
    return {tool:'ask_human',input:{reason:'No safe unique target'}};
  }};
  return {service,planner,verifyReview,assertContext,authorizeStep,negative,actual,expected,
    actions,guard,visibleInitial,allowed,clicks:[open,approve,review],getEffects:()=>effects};
}
async function run(w,id,armName,dag,index=null) {
  const suffix=armName==='suffix'||armName==='teach';
  const inputs=id==='teach'?{query:'Training-Q8',f1:'Teaching value one',f2:'Teaching value two'}
    :{query:w.query,f1:w.fields[0][2],f2:w.fields[1][2]};
  const arm=id==='teach'?'shared-teach':armName;
  const projectId=[w.id,id,arm].join('-');
  const journal=resolve(out,projectId+'.jsonl');
  const log=row=>appendFileSync(journal,canon(row)+'\n');
  const env=harness(w,id,inputs,log);
  store.create({id:projectId,goal:'Prepare a verified local review'});
  const result=await runWorkflow({
    dag,mode:id==='teach'?'learn':'reuse',goal:w.id+'-review',accountScope:id==='teach'?w.tenant:(process.env.DIAG_EVAL_ACCOUNT||w.tenant),service:env.service,
    owner:{},pageId:'main',intent:w.id+':review',template:w.id+'-template',inputs,
    intermediateClicks:env.clicks,observationLocators:env.allowed,slotRoles:slotRolesFor(w),
    learnRepairs:false,reconvergeMidRepair:true,suffixEligibility:suffix,suffixIndex:(id==='teach'||armName==='index')?index:null,assertContext:env.assertContext,
    authorizeStep:env.authorizeStep,task:'Prepare a verified local review',planner:env.planner,
    config:{maxTurns:22,maxInputBytes:50000},store,projectId,verifyReview:env.verifyReview,
    signal:AbortSignal.timeout(2000),
  });
  log({event:'run-terminal',completed:result.completed,detail:result.detail});
  const actual=env.actual(), exactOracle=Object.keys(env.expected).every(k=>actual[k]===env.expected[k]);
  const row={workflow:w.id,case:id,arm,negative:env.negative,completed:result.completed,exactOracle,
    scriptedPlannerDecisions:result.modelCalls,realModelCalls:0,cacheSteps:result.cacheSteps,
    certifiedSuffixRejoins:result.certifiedSuffixRejoins.map(x=>({node:x.rejoinedNodeId})),
    certified:armName==='index'?(result.suffix?.certified??0):result.certifiedSuffixRejoins.length,indexRefusals:result.suffix?.refusals??null,
    prefixCacheSteps:result.prefixCacheSteps,reconvergedCacheSteps:result.reconvergedCacheSteps,fallbackReason:result.fallbackReason,
    effects:env.getEffects(),actions:env.actions,guard:env.guard,visibleInitial:env.visibleInitial,
    detail:result.detail,actual,journalSha256:sha(readFileSync(journal))};
  appendFileSync(resolve(out,'rows.jsonl'),canon(row)+'\n');
  return row;
}
const sourceDigests=Object.fromEntries(['client/trace-dag.js','client/suffix-eligibility.js','client/workflow-agent.js','client/investigation.js']
  .map(p=>[p,sha(readFileSync(resolve(W,p)))]));
for(const w of fixture.workflows) {
  const dag=new TraceDag(limits);
  const taughtIndex=SuffixIndex?new SuffixIndex():null;
  const taught=await run(w,'teach','teach',dag,taughtIndex);
  if(!taught.completed||!taught.exactOracle) {
    rows.push({workflow:w.id,teachingFailed:true,detail:taught.detail});
    continue;
  }
  const trained=dag.export(), graph=sha(canon(trained));
  const ids=fixture.cases;
  for(const [i,id] of ids.entries()) {
    for(const armName of (i%2?[...ARMS].reverse():ARMS)) {
      const replay=TraceDag.restore(trained,limits);
      const row=await run(w,id,armName,replay,taughtIndex?SuffixIndex.restore(taughtIndex.export()).freeze():null);
      rows.push({...row,trainedGraph:graph,graphUnchanged:sha(canon(replay.export()))===graph});
    }
  }
}
const good=rows.filter(x=>x.negative===false), bad=rows.filter(x=>x.negative===true);
const stats=Object.fromEntries(ARMS.map(arm=>{
  const safe=good.filter(x=>x.arm===arm), unsafe=bad.filter(x=>x.arm===arm);
  return [arm,{completed:safe.filter(x=>x.completed&&x.exactOracle).length,safeCases:safe.length,
    scriptedDecisions:safe.reduce((a,b)=>a+b.scriptedPlannerDecisions,0),
    cacheSteps:safe.reduce((a,b)=>a+b.cacheSteps,0),certifiedRejoins:safe.reduce((a,b)=>a+b.certified,0),certifiedOnNegatives:unsafe.reduce((a,b)=>a+b.certified,0),
    byCase:Object.fromEntries(fixture.cases.map(c=>[c,rows.filter(x=>x.arm===arm&&x.case===c).map(x=>[x.scriptedPlannerDecisions,x.cacheSteps,x.certified,x.effects])])),
    safeStops:unsafe.filter(x=>x.effects===0&&!x.completed).length,negativeCases:unsafe.length,
    refused:unsafe.map(x=>[x.case,x.detail,x.guard])}];
}));
const bundle={pin, sourceDigests, fixturesSha256:sha(readFileSync(resolve(frozen,'fixtures.json'))),
  protocolSha256:sha(readFileSync(resolve(frozen,'protocol.txt'))),scriptSha256:sha(readFileSync(new URL(import.meta.url))),
  claims:{browserRuns:0,realModelCalls:0,spendUsd:0,liveTenantRuns:0,submissions:0},stats,rows,
  diagnostic:{fixedPolicy:FIXED,arms:ARMS,note:'Audit copy of frozen/run.mjs; not holdout evidence'},
  gate:rows.length===21*ARMS.length&&good.every(x=>x.completed&&x.exactOracle)&&bad.every(x=>!x.completed&&x.effects===0)
    &&rows.every(x=>x.graphUnchanged)};
writeFileSync(resolve(out,'summary.json'),JSON.stringify(bundle,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({bundle:resolve(out,'summary.json'),gate:bundle.gate,stats,rows:rows.length},null,2));
if(!bundle.gate)process.exitCode=1;
