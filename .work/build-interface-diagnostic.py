import json,hashlib
from pathlib import Path
p=Path('projects/reconfiguration/cross_domain_screen');out=p/'interface-diagnostic-01';out.mkdir()
sha=lambda b:hashlib.sha256(b.encode()).hexdigest()
scaffold='''struct Params { length: u32, output_offset: u32, first: f32, second: f32, }
@group(0) @binding(0) var<storage, read> left_values: array<f32>;
@group(0) @binding(1) var<storage, read> right_values: array<f32>;
@group(0) @binding(2) var<storage, read_write> output_values: array<f32>;
@group(0) @binding(3) var<uniform> params: Params;
override WORKGROUP_SIZE: u32 = 32u;
@compute @workgroup_size(WORKGROUP_SIZE)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
  let i = gid.x;
  if (i >= params.length) { return; }
  let x = left_values[i];
  let y = right_values[i];
  output_values[params.output_offset + i] = 0.0; // REPLACE_EXPRESSION
}
'''
old=[json.loads(x) for x in Path('projects/distillation/wgsl/channel_gain/corpus-v1/smoke/prompts.jsonl').read_text().splitlines()]
rows=[]
for row in old:
 r=dict(row);prefix='Complete the WGSL shader below. Replace only the marked 0.0 with an expression implementing the specification. Keep the bindings, valid override declaration, bounds guard and output index unchanged. Return the entire WGSL source, beginning with struct Params; no Markdown fences or explanation.\n<specification>\n';suffix='\n</specification>\n<shader_to_complete>\n'+scaffold+'</shader_to_complete>\n'
 r['prompt']=prefix+r['specification']+suffix;r['promptSha256']=sha(r['prompt']);r['instructionSpan']={'start':len(prefix),'end':len(prefix)+len(r['specification']),'textSha256':sha(r['specification'])};r['diagnosticPromptChange']='Shared explicit valid interface scaffold; arithmetic placeholder unchanged across tasks; original exposed specification and public checks retained';rows.append(r)
(out/'prompts.jsonl').write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
(out/'scaffold.wgsl').write_text(scaffold)
source=json.loads((p/'probe-protocol.json').read_text())
protocol={k:source[k] for k in ['sourceCandidate','sourceCandidateSha256','candidate','candidateSha256','architectureMapping','generation','controlSeed','conditions','cacheArm']}
protocol.update({'schema':'gamma.channel-gain-interface-diagnostic/v1','status':'freeze_before_calls','classification':'exposed-task interface debugging, not improvement confirmation','intervention':'Same explicit WGSL interface scaffold for base and gain; analytical gain rule unchanged','priorExposure':{'original9BConfirmationCompleted':True,'previous27BScreenRequests':24,'previous27BShaderProbeRequests':4,'previousShaderProbeBasePass':0,'previousShaderProbeGainPass':0},'generationRequests':4,'resetPrefillRequests':2,'scoring':'All four outputs sealed before unchanged original public checks; raw complete source, no repair or fence stripping','readinessCriterion':'Both base sources compile and dispatch, and at least one base public semantic pass; report exact counts regardless. This is readiness for a useful next study, not a gain success threshold.','nextStudy':'Do not reuse original confirmation families as fresh data; no automatic expanded campaign from this diagnostic','stop':'Finish four fixed calls unless runtime, memory or service failure; no candidate tuning','resourceAdmission':'Cooperative exclusive GPU lock plus fresh retired-provider guard; no claim of global isolation'})
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
config=json.loads((p/'native-jupiter-27b-probe-config.json').read_text());config['serviceGuardPath']='/home/x/deco/gamma/.work/channel-gain-20261112/projects/reconfiguration/cross_domain_screen/interface-diagnostic-01/guard.json';config['executionContext']='After completed9B and27B studies; exclusive cooperative admission; new exposed-task interface diagnostic'
(out/'config.json').write_text(json.dumps(config,indent=2)+'\n')
print('Created two exposed scaffold prompts, unchanged rule, four-request diagnostic contract.')
