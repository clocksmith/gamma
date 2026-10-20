const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('fs'),assert=require('assert/strict'),path=require('path');
const out=process.env.LITERAL_TEST_OUTPUT;if(!out)throw Error('Set LITERAL_TEST_OUTPUT to an existing output directory');const data=JSON.parse(fs.readFileSync(path.join(__dirname,'literal-language.json')));
(async()=>{const browser=await chromium.launch({...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--disable-gpu']});const receipts=[];
try{for(const [name,viewport,problem] of [['desktop',{width:1280,height:900},'0242'],['mobile',{width:390,height:844},'0594']]){
 const context=await browser.newContext({viewport,acceptDownloads:true,hasTouch:name==='mobile'}),page=await context.newPage(),errors=[],failed=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400&&r.url().startsWith(new URL(process.env.LITERAL_DEMO_URL||'http://127.0.0.1:8874/labs/two-button/').origin))failed.push([r.url(),r.status()]);});page.on('dialog',d=>d.accept());
 await page.goto(process.env.LITERAL_DEMO_URL||'http://127.0.0.1:8874/labs/two-button/');await page.locator('#workspaceBtn').click();if(await page.locator('#gammaLiteralValidationDetails').count())await page.locator('#gammaLiteralValidationDetails').evaluate(e=>e.open=true);await page.waitForFunction(()=>document.getElementById('gammaLiteralIdentity').textContent.includes('79 entries'));
 await page.locator('#inputMode').selectOption('literal');await page.locator('#inputMode').selectOption('ascii');const prior=await page.evaluate(()=>editor.text);await page.locator('#gammaLiteralProblem').selectOption(problem);
 const p=data.problems.find(p=>p.id===problem),word=i=>i.toString(2).padStart(7,'0');
 await page.locator('#gammaLiteralZero').focus();for(const b of word(79))await page.keyboard.press(b);assert.match(await page.locator('#gammaLiteralStatus').textContent(),/Unused literal ID 79/);
 for(let i=0;i<7;i++)await page.locator('#gammaUndoLiteralBit').click();assert.equal(await page.locator('#gammaLiteralStream').inputValue(),'');
 const prefix=[0,125,126].map(word).join(''),bits=prefix+p.sequence.map(word).join('')+word(127);
 for(const b of bits){if(name==='mobile')await page.locator(`[data-literal-bit="${b}"]`).click();else {await page.locator('#gammaLiteralZero').focus();await page.keyboard.press(b);}}
 assert.equal(await page.locator('#gammaLiteralSource').textContent(),p.sequence.map(i=>data.literals[i]).join(''));assert.equal(await page.evaluate(()=>editor.text),prior);
 assert.equal(await page.locator('#gammaTestLiteral').isEnabled(),true);
 const popupPromise=page.waitForEvent('popup');await page.locator('#connectGamma').click();const popup=await popupPromise;await popup.locator('#connect').click();await page.waitForFunction(()=>document.getElementById('bridgeStatus').textContent==='Gamma connected.');
 await page.locator('#gammaTestLiteral').click();await page.waitForFunction(()=>document.getElementById('gammaLiteralResult').textContent.includes('"tests_passed"'),{},{timeout:30000});
 const result=JSON.parse(await page.locator('#gammaLiteralResult').textContent());assert(result.passed);assert.equal(result.tests_passed,p.reference_cases);assert.equal(result.cost.control_bits,21);
 await page.locator('#gammaLiteralReplayFile').locator('..').locator('..').evaluate(e=>e.open=true);
 const dlPromise=page.waitForEvent('download');await page.locator('#gammaExportLiteral').click();const download=await dlPromise;const saved=path.join(out,`${name}-session.json`);await download.saveAs(saved);const record=JSON.parse(fs.readFileSync(saved));assert.equal(record.bits,bits);assert.equal(record.tests.length,1);assert.equal(record.cost.undo_bit_actions,7);
 await page.locator('#gammaLiteralReplayFile').setInputFiles(saved);await page.waitForFunction(()=>document.getElementById('gammaLiteralStatus').textContent.includes('Read-only replay'));assert(await page.locator('#gammaTestLiteral').isDisabled());assert(await page.locator('#gammaLiteralZero').isDisabled());assert.equal(await page.evaluate(()=>editor.text),prior);
 if(process.env.LITERAL_EXPECT_SEMANTIC==='1')assert(await page.locator('#semanticFoundation').isVisible());assert.equal(await page.locator('#inputMode option').count(),4);if(process.env.LITERAL_EXPECT_EXPLORER==='1')assert.equal(await page.locator('a[href="./compositions/"]').count(),1);assert.equal(await page.locator('#compositionGame').count(),1);
 await page.locator('#gammaLiteralTitle').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,`${name}.png`)});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);assert.equal(overflow,false);assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
 receipts.push({name,viewport,problem,checks:result.tests_passed,source_sha256:result.source_sha256,control_bits:result.cost.control_bits,retained_stream_bits:bits.length,unused_id_rejected:true,read_only_replay:true,main_editor_unchanged:true,existing_modes_present:true,console_errors:errors,failed_requests:failed,horizontal_overflow:overflow});
 await context.close();console.log(name,'passed',result.tests_passed);
}fs.writeFileSync(path.join(out,'browser-receipt.json'),JSON.stringify({scope:'Automated desktop/mobile integration, not human productivity',receipts},null,2)+'\n');}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
