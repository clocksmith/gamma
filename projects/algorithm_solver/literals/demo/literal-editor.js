import {PROFILE,DICTIONARY_SHA,CONTROLS,LiteralSession,verifyLanguage,replayRecord,sha256} from './literal-input.js?v=literal-shared7-v1';
export async function bindLiteralEditor(editor,api){
  const $=id=>document.getElementById(id),panel=$('literalComposition'),maxRecordBytes=1048576;
  let language,session,revision=0,busy=false;
  const status=text=>{$('literalStatus').textContent=text;};
  try{const response=await fetch(new URL('./literal-language.json?v=literal-shared7-v1',import.meta.url));if(!response.ok)throw Error('Cannot load literal dictionary');language=await verifyLanguage(await response.json());session=new LiteralSession(language,language.problems[0].id);}
  catch(error){status(error.message);return;}
  $('literalProblem').replaceChildren(...language.problems.map(p=>{const o=document.createElement('option');o.value=p.id;o.textContent=`#${Number(p.id)} · ${p.title}`;return o;}));
  $('literalIdentity').textContent=`79 entries · 7-bit IDs · dictionary SHA256 ${DICTIONARY_SHA}`;
  $('literalVocabulary').textContent=language.literals.map((text,id)=>`${id.toString(2).padStart(7,'0')} · ${id}\n${JSON.stringify(text)}`).join('\n\n')+'\n\n79–124: unused; rejected.\n'+Object.entries(CONTROLS).map(([id,name])=>`${Number(id).toString(2)} · ${name} (protocol control, not dictionary entry)`).join('\n');
  function render(){
    const s=session.snapshot(),guide=language.problems.find(p=>p.id===session.problem);
    $('literalPrefix').textContent=`Next word: ${s.prefix.padEnd(7,'·')} (${s.prefix.length}/7 bits)`;
    $('literalPieces').replaceChildren(...s.selected.map((id,i)=>{const li=document.createElement('li');li.textContent=`${i+1}. ${id.toString(2).padStart(7,'0')} · ID ${id}: ${JSON.stringify(language.literals[id])}`;return li;}));
    $('literalSource').textContent=s.source;$('literalStream').value=session.bits;
    const entered=session.events.filter(e=>e.kind==='bit').length,undos=session.events.filter(e=>e.kind==='backspace').length;
    $('literalCost').textContent=`Stream: ${s.literal_bits} literal + ${s.control_bits} control + ${s.rejected_bits} rejected + ${s.partial_bits} partial = ${s.total_bits} bits. Retained source: ${s.selected.length} selections / ${s.source_only_bits} bits. Entered this attempt: ${entered} bits; ${undos} undo-bit actions (separate controls, not converted to bits).`;
    $('literalGuide').textContent=`Reference IDs (guidance only): ${guide.sequence.join(', ')}. Seven-bit stream: ${guide.sequence.map(i=>i.toString(2).padStart(7,'0')).join(' ')}. Then Finish: 1111111. This guide inserts nothing.`;
    $('literalResult').textContent=session.tests.length?`${session.replay?'Imported historical receipts; not revalidated.\n':''}${JSON.stringify(session.tests.at(-1),null,2)}`:'';
    $('testLiteral').disabled=busy||session.replay||!s.complete;
    $('undoLiteralBit').disabled=session.replay||!session.bits.length;
    panel.querySelectorAll('[data-literal-bit]').forEach(b=>b.disabled=session.replay||s.complete||Boolean(s.error));
    status(s.error||(session.replay?'Read-only replay verified. New attempt returns to input.':s.complete?'Finished. Test through paired Gamma; no source is inserted into the editor.':'Enter only 0/1. Undo literal: 1111101 · Reset source: 1111110 · Finish: 1111111.'));
  }
  function act(fn){try{fn();revision++;render();}catch(error){status(error.message);}}
  function fresh(problem){session=new LiteralSession(language,problem);revision++;render();$('literalZero').focus();}
  $('literalProblem').addEventListener('change',()=>{const next=$('literalProblem').value;if(session.bits&&!confirm('Start a new literal attempt? Export the current attempt first if you want to keep it.')){$('literalProblem').value=session.problem;return;}fresh(next);});
  $('newLiteralAttempt').addEventListener('click',()=>{if(!session.bits||confirm('Start a new literal attempt? The current local attempt will be replaced.'))fresh(session.problem);});
  panel.querySelectorAll('[data-literal-bit]').forEach(button=>button.addEventListener('click',()=>act(()=>session.bit(Number(button.dataset.literalBit)))));
  $('undoLiteralBit').addEventListener('click',()=>act(()=>session.backspace()));
  panel.addEventListener('keydown',event=>{
    if(event.ctrlKey||event.metaKey||event.altKey||event.target.closest('textarea,input,select,summary'))return;
    const value=event.key==='0'||event.key==='1'?event.key:editor.keyBit(event.key.toLowerCase());
    if(value!==null&&value!==undefined){event.preventDefault();event.stopPropagation();if(!event.repeat)act(()=>session.bit(Number(value)));}
    else if(event.key==='Backspace'){event.preventDefault();event.stopPropagation();if(!event.repeat)act(()=>session.backspace());}
  });
  $('testLiteral').addEventListener('click',async()=>{
    if(busy||session.replay||!session.snapshot().complete)return;
    const current=session,version=revision,bits=session.bits,problem=session.problem,source=session.snapshot().source;
    busy=true;render();status('Checking completed source in the paired Gamma sandbox…');
    try{
      const result=await api.job({operation:'literal_check',profile:PROFILE,dictionary_sha256:DICTIONARY_SHA,problem_id:problem,bits});
      if(current!==session||revision!==version||session.bits!==bits){status('Attempt changed; earlier test result discarded.');return;}
      if(result.source_sha256!==await sha256(source)||result.dictionary_sha256!==DICTIONARY_SHA||result.problem_id!==problem)throw Error('Result identity mismatch');
      if(current!==session||revision!==version)return;
      session.tests.push(result);session.tests=session.tests.slice(-16);render();
      status(result.passed?`${result.tests_passed}/${result.tests_total} known development checks passed, including input preservation. Not autonomous synthesis.`:`Checks did not all pass: ${result.tests_passed}/${result.tests_total}. ${result.reason||'Inspect the result.'}`);
    }catch(error){if(current===session&&revision===version)status(error.message);}
    finally{busy=false;$('testLiteral').disabled=session.replay||!session.snapshot().complete;}
  });
  $('exportLiteral').addEventListener('click',async()=>{
    try{const record=await session.report(),blob=new Blob([JSON.stringify(record)],{type:'application/json'});if(blob.size>maxRecordBytes)throw Error('Replay record exceeds 1 MiB');const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='literal-shared7-session-v1.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(error){status(error.message);}
  });
  $('literalReplayFile').addEventListener('change',async()=>{
    const file=$('literalReplayFile').files?.[0];if(!file)return;
    try{if(file.size>maxRecordBytes)throw Error('Replay file exceeds 1 MiB');const version=revision,next=await replayRecord(language,JSON.parse(await file.text()));if(version!==revision)throw Error('Attempt changed while loading replay');if(session.bits&&!confirm('Replace this view with a read-only replay? Export the current attempt first to retain it.'))return;session=next;revision++;$('literalProblem').value=session.problem;render();}
    catch(error){status(error.message);}finally{$('literalReplayFile').value='';}
  });
  render();return {report:()=>session.report()};
}
