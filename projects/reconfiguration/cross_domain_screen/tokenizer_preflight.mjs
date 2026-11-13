import {readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {tokenContract} from '../../distillation/wgsl/channel_gain/token_contract.mjs';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function qualifyTokenizer({dopplerRoot,manifest:manifestPath,tokenizer:tokenizerPath,tasks:tasksPath,config:configPath,taskFormat='json',expectedCount=6}){
 const [manifestBytes,tokenizerBytes,taskBytes]=await Promise.all([manifestPath,tokenizerPath,tasksPath].map(path=>readFile(path)));
 if(!['json','jsonl'].includes(taskFormat)||!Number.isSafeInteger(Number(expectedCount))||Number(expectedCount)<1)throw Error('Explicit task format/count required');
 const manifest=JSON.parse(manifestBytes),rows=taskFormat==='jsonl'?taskBytes.toString().trim().split('\n').map(line=>JSON.parse(line)):JSON.parse(taskBytes).tasks,config=configPath?JSON.parse(await readFile(configPath)):null;
 const mod=path=>import(pathToFileURL(join(resolve(dopplerRoot),path)).href);
 const [{initTokenizer},{parseModelConfigFromManifest},{resolvePromptInput}]=await Promise.all([
  mod('src/inference/pipelines/text/init-tokenizer.js'),mod('src/inference/pipelines/text/config.js'),mod('src/inference/pipelines/text/generator/prompt-input.js')]);
 const tokenizer=await initTokenizer(manifest,{storageContext:{loadTokenizerJson:async()=>tokenizerBytes.toString()}});
 const modelConfig=parseModelConfigFromManifest(manifest,config?.runtimeConfig?.inference?.modelOverrides);
 const state={tokenizer,modelConfig},contracts=[],failures=[];
 for(const task of rows){try{const contract=tokenContract({row:task,render:prompt=>resolvePromptInput(state,prompt,true,'cross-domain CPU preflight'),encode:text=>tokenizer.encode(text)});contracts.push({taskId:task.id??task.taskId,...contract});}catch(error){failures.push({taskId:task.id??task.taskId,error:error.message});}}
 return {schema:'gamma.cross-domain-tokenizer-preflight/v1',passed:failures.length===0&&contracts.length===Number(expectedCount),modelManifestSha256:hash(manifestBytes),tokenizerSha256:hash(tokenizerBytes),tasksSha256:hash(taskBytes),modelOverrides:config?.runtimeConfig?.inference?.modelOverrides??null,
  chatTemplateType:modelConfig.chatTemplateType,chatTemplateThinking:modelConfig.chatTemplateThinking,contracts,failures,execution:'CPU only; exact provisioned tokenizer and Doppler formatter; no weights, inference or GPU initialization'};
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{const options={};for(let i=2;i<process.argv.length;i+=2){if(!process.argv[i].startsWith('--')||!process.argv[i+1])throw Error('Expected --option value');options[process.argv[i].slice(2).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=process.argv[i+1];}
  const receipt=await qualifyTokenizer(options);await writeFile(options.output,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify({passed:receipt.passed,contracts:receipt.contracts.length,failures:receipt.failures}));if(!receipt.passed)process.exitCode=2;
 }catch(error){console.error(error.stack??String(error));process.exitCode=2;}
}
