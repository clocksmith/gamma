import {readFile, writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {isDeepStrictEqual} from 'node:util';
import {pathToFileURL} from 'node:url';
import {SelectedRulesMatch} from '../../lab/environment/selected-rules-match.js';
import {createPlayerPolicy} from '../../lab/policies/policy-factory.js';
import {loadGameIdentity, sha256} from '../../lab/versioning/game-identity.js';
import {verifyRelease} from '../../tasks/release-artifacts.mjs';
import {createRng, shuffle} from '../../web/src/engine.js';
import {subsets} from './2026-10-11-seat-diversity.mjs';
import {assertOutcome} from './2026-10-11-capacity-counterplay.mjs';
import {summarizeOutcome} from './2026-10-11-plan-traces.mjs';

export const CANDIDATES = {customers3: {customerPoints: 3}, equipment3: {facilityCost: 3}};
const ROOT = 'economy-20261011-trained-v1';
const FILES = ['2026-10-11-economy-field.mjs', '2026-10-11-economy-profiles.json',
  '2026-10-11-economy-preregistration.md'];
const INPUTS = ['game-config', 'factions', 'headlines', 'projects', 'mandates'];
const rotate = (xs, n) => xs.map((_, i) => xs[(i + n) % xs.length]);

export function scenarios(count, backend, smoke = false) {
  if (![3,4,5].includes(count) || !['greedy','weighted'].includes(backend)) throw new RangeError('Unsupported cohort');
  const rows = [];
  for (const [subset, ids] of subsets([0,1,2,3,4,5], count).entries())
    for (const mode of ['fixed','variable'])
      for (let repeat=0; repeat < (count === 3 ? 2 : 4); repeat++) {
        const prefix = `${ROOT}:${smoke ? 'smoke' : 'holdout'}:${backend}:${count}:${subset}:${mode}:${repeat}`;
        const order = shuffle(ids, createRng(`${prefix}:institutions`));
        for (let policyRotation=0; policyRotation<4; policyRotation++)
          for (let rotation=0; rotation<count; rotation++) {
            rows.push({count, backend, subset, mode, repeat, policyRotation, rotation,
              institutions: rotate(order, rotation), seed: `${prefix}:${policyRotation}:${rotation}`});
            if (smoke && rows.length === 3) return rows;
          }
      }
  return rows;
}

export async function play(input, profiles, block, overlay = {}, projection = 'batch') {
  const roster = Array.from({length:block.count}, (_, seat) => profiles[(seat+block.policyRotation)%4]);
  const match = new SelectedRulesMatch({config: input['game-config'],
    factions: block.institutions.map(i=>input.factions.factions[i]), profiles:roster,
    backends:roster.map(()=>block.backend), headlines:input.headlines, projects:input.projects,
    mandates:input.mandates, seed:block.seed, playerCount:block.count,
    mandateMode:block.mode, projection, recordReplay:false, rulesVariant:overlay});
  const policies = roster.map(p=>createPlayerPolicy(p,block.backend,{rosterProfileIds:roster.map(p=>p.id)}));
  const result = await match.play(policies); assertOutcome(match,result);
  const outcome = summarizeOutcome(result,input['game-config']);
  for (const p of outcome.players) {
    if (Object.values(p.scoreParts).reduce((a,b)=>a+b,0)!==p.score) throw new Error('Score mismatch');
    if (Object.values(p.actions).reduce((a,b)=>a+b,0)!==12) throw new Error('Turn count mismatch');
    const actual=match.players[p.seat];
    for (const k of ['runway','compute','capability','reputation','customers'])
      if (actual[k]>input['game-config'].resources[k].cap) throw new Error('Resource cap exceeded');
    p.orgs=actual.pieces.length; p.equipped=actual.pieces.filter(o=>o.equipped).length;
  }
  return outcome;
}

export async function run({count,backend,candidate,shard=0,shards=1,smoke=false}) {
  if (!Object.hasOwn(CANDIDATES,candidate) || !Number.isInteger(shard) || !Number.isInteger(shards) ||
      shards<1 || shard<0 || shard>=shards) throw new RangeError('Invalid candidate/shard');
  if (execFileSync('git',['status','--porcelain'],{encoding:'utf8'}).trim()) throw new Error('Clean source required');
  await verifyRelease(process.cwd());
  const allProfiles=JSON.parse(await readFile(`evidence/studies/${FILES[1]}`)), profiles=allProfiles[backend].profiles;
  const input=Object.fromEntries(await Promise.all(INPUTS.map(async n=>[n,JSON.parse(await readFile(`dist/runtime/${n}.json`))])));
  const fileHashes=Object.fromEntries(await Promise.all(FILES.map(async f=>[f,sha256(await readFile(`evidence/studies/${f}`))])));
  const options={profiles,backends:[backend],policyProjection:'batch',experimentKind:'economy_trained_field',
    experimentConfiguration:{root:ROOT,count,backend,candidate,shard,shards,smoke}};
  const identity=await loadGameIdentity(options);
  const blocks=scenarios(count,backend,smoke).filter((_,i)=>i%shards===shard);
  const output=`evidence/studies/simulation/2026-10-11-economy-${candidate}-${backend}-${count}-${shard}${smoke?'-smoke':''}.json`;
  const raw={status:'running',evidenceType:'simulation',identity,fileHashes,options,profiles,
    inputHashes:Object.fromEntries(await Promise.all(INPUTS.map(async n=>[n,sha256(await readFile(`dist/runtime/${n}.json`))]))),rows:[]};
  await writeFile(output,JSON.stringify({status:'running',identity})+'\n',{flag:'wx'});
  try {
    for (const block of blocks) {
      const arms={canonical:await play(input,profiles,block),candidate:await play(input,profiles,block,CANDIDATES[candidate])};
      if (smoke) for (const [name,overlay] of [['canonical',{}],['candidate',CANDIDATES[candidate]]])
        if (!isDeepStrictEqual(arms[name],await play(input,profiles,block,overlay,'rich'))) throw new Error('Rich/batch divergence');
      raw.rows.push({block,arms});
      if (raw.rows.length%100===0) process.stderr.write(`${backend}/${count}/${shard}: ${raw.rows.length}/${blocks.length}\n`);
    }
    if (!isDeepStrictEqual(identity,await loadGameIdentity(options))) throw new Error('Source identity drift');
    for (const f of FILES) if (sha256(await readFile(`evidence/studies/${f}`))!==fileHashes[f]) throw new Error('Study drift');
    raw.status=smoke?'smoke_only':'complete';
  } catch (e) {raw.status='failed'; raw.error=String(e.stack); throw e;}
  finally {await writeFile(output,JSON.stringify(raw)+'\n');}
  console.log(JSON.stringify({output,rows:raw.rows.length,status:raw.status,sha256:sha256(await readFile(output))}));
}
if (process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) {
  const args=Object.fromEntries(process.argv.slice(2).map(x=>x.split('=')));
  await run({count:Number(args.players),backend:args.backend,candidate:args.candidate,
    shard:Number(args.shard??0),shards:Number(args.shards??1),smoke:args.smoke==='true'});
}
