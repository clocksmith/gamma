import test from 'node:test';
import assert from 'node:assert/strict';
import {auditDevelopmentExposure} from './exposure_audit.mjs';
test('sequence witnesses distinguish all 46 indexed elementwise maps without confirmation data',async()=>{
  const audit=await auditDevelopmentExposure();
  assert.deepEqual(audit.summary,{knownMaps:46,developmentFamilies:3,distinctFromKnownMaps:true});
  assert.equal(audit.confirmationCreated,false);
  for(const w of audit.witnesses){assert.notEqual(w.before,w.after);assert.equal(w.original[w.index],w.changed[w.index]);}
});
