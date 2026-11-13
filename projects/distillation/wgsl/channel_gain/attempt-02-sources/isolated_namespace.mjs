import {mkdtemp,mkdir,copyFile,symlink,writeFile,rm,readFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,resolve,dirname} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
// Byte-identical campaign files; only this private temporary tree is writable.
// Neither campaign/.namespace nor files in the Doppler checkout are modified.
export async function openIsolatedNamespace({dopplerRoot}={}){
 const gammaRoot=resolve(dirname(fileURLToPath(import.meta.url)),'../../../..');
 const campaignRoot=join(gammaRoot,'projects/distillation/wgsl/campaign');
 dopplerRoot=resolve(dopplerRoot||process.env.DOPPLER_ROOT||join(gammaRoot,'../doppler'));
 const namespaceRoot=await mkdtemp(join(tmpdir(),'gamma-channel-gain-verifier-'));
 const copied=['tools/lib/wgsl-writer-semantic-harness.js','tools/lib/wgsl-semantic-harness.js','tools/lib/wgsl-browser-verifier.js','src/tooling/wgsl-repair-semantic-gate.js'];
 const sourceHashes={};
 try{
  for(const dir of ['tools/lib','src/tooling','src/utils'])await mkdir(join(namespaceRoot,dir),{recursive:true});
  await writeFile(join(namespaceRoot,'package.json'),JSON.stringify({type:'module'}));
  for(const relative of copied){await copyFile(join(campaignRoot,relative),join(namespaceRoot,relative));sourceHashes[`campaign/${relative}`]=hash(await readFile(join(campaignRoot,relative)));}
  for(const relative of ['src/formats','src/experimental','node_modules'])await symlink(join(dopplerRoot,relative),join(namespaceRoot,relative));
  // Frozen verifier predates Doppler's utils -> formats move.
  await symlink(join(dopplerRoot,'src/formats/sha256.js'),join(namespaceRoot,'src/utils/sha256.js'));
  for(const relative of ['src/formats/sha256.js','src/formats/plain-object.js','src/formats/stable-sort-object.js','src/experimental/training/wgsl-repair.js'])sourceHashes[`doppler/${relative}`]=hash(await readFile(join(dopplerRoot,relative)));
  const [writer,numeric,browser]=await Promise.all([
   import(pathToFileURL(join(namespaceRoot,'tools/lib/wgsl-writer-semantic-harness.js')).href),
   import(pathToFileURL(join(namespaceRoot,'src/tooling/wgsl-repair-semantic-gate.js')).href),
   import(pathToFileURL(join(namespaceRoot,'tools/lib/wgsl-browser-verifier.js')).href),
  ]);
  return {namespaceRoot,buildWgslWriterPrompt:writer.buildWgslWriterPrompt,parseCompleteWgslResponse:writer.parseCompleteWgslResponse,evaluateNumericAgreement:numeric.evaluateNumericAgreement,createWgslBrowserVerifier:browser.createWgslBrowserVerifier,provenance:{sourceHashes,compatibilityAliases:{'src/utils/sha256.js':'doppler/src/formats/sha256.js'},sharedNamespaceTouched:false},close:()=>rm(namespaceRoot,{recursive:true,force:true})};
 }catch(error){await rm(namespaceRoot,{recursive:true,force:true});throw error;}
}
