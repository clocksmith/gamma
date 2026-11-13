import {readFile,writeFile} from 'node:fs/promises';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {sha256} from './verify_shaders.mjs';
import {openIsolatedNamespace} from './isolated_namespace.mjs';
export const ORIGINAL_BROWSER_VERIFIER_SHA256='18a6107812f373fd5551defffce9fa52da5193693c0676d786f463a7ab61dadd';
const TARGET="              const pipeline = await device.createComputePipelineAsync({\n                label: request.id,\n                layout: 'auto',";
const REPLACEMENT=`              // The host task contract includes bindings that a correct unary
              // shader may leave unused. Auto layout drops those bindings.
              const seenBindings = new Set();
              const contractLayout = device.createBindGroupLayout({
                label: request.id + '-contract-layout',
                entries: request.buffers.map((buffer) => {
                  if (!Number.isInteger(buffer.binding) || buffer.binding < 0
                    || seenBindings.has(buffer.binding)) throw new Error('invalid_contract_binding');
                  if (!['uniform', 'storage', 'read-only-storage'].includes(buffer.kind)) {
                    throw new Error('invalid_contract_buffer_kind');
                  }
                  seenBindings.add(buffer.binding);
                  return { binding: buffer.binding, visibility: GPUShaderStage.COMPUTE,
                    buffer: { type: buffer.kind } };
                }),
              });
              const pipeline = await device.createComputePipelineAsync({
                label: request.id,
                layout: device.createPipelineLayout({ bindGroupLayouts: [contractLayout] }),`;
export function patchContractBrowserSource(source){
 if(sha256(source)!==ORIGINAL_BROWSER_VERIFIER_SHA256)throw Error('Historical browser verifier source hash changed');
 if(source.split(TARGET).length!==2)throw Error('Exact auto-layout patch boundary missing or ambiguous');
 return source.replace(TARGET,REPLACEMENT);
}
export async function openContractVerifierNamespace(options={}){
 const namespace=await openIsolatedNamespace(options);
 try{const source=await readFile(join(namespace.namespaceRoot,'tools/lib/wgsl-browser-verifier.js'),'utf8');const patched=patchContractBrowserSource(source);const path=join(namespace.namespaceRoot,'tools/lib/wgsl-browser-verifier-contract-v1.js');await writeFile(path,patched,{flag:'wx'});const {createWgslBrowserVerifier}=await import(pathToFileURL(path).href);
  const repair={schema:'gamma.channel-gain-contract-layout-repair/v1',originalSourceSha256:sha256(source),patchModuleSha256:sha256(await readFile(new URL(import.meta.url))),effectiveSourceSha256:sha256(patched),change:'Explicit group0 compute-stage buffer layout from frozen request binding/kind contract; compile/oracle/tolerance/dispatch/canary logic unchanged',historicalSourceModified:false};
  return {...namespace,createWgslBrowserVerifier,provenance:{...namespace.provenance,layoutRepair:repair}};
 }catch(error){await namespace.close();throw error;}
}
