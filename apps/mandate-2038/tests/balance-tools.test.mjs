import test from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync, spawnSync} from 'node:child_process';
import {fixture, config, host} from './helpers/smaller-game.mjs';
for (const cli of ['unified-matrix','balance-audit']) {
  test(`${cli}: help and invalid options cannot start an experiment`, () => {
    const script = `lab/cli/${cli}.mjs`;
    assert.match(execFileSync(process.execPath,[script,'--help'], {encoding:'utf8',timeout:5000}), /Options/);
    for (const args of [['--unrecognized'],['--runs'],['960']]) {
      const result=spawnSync(process.execPath,[script,...args], {encoding:'utf8',timeout:5000});
      assert.equal(result.status,1);
      assert.doesNotMatch(result.stderr,/initial:|adaptive:/);
      assert.match(result.stderr,/Unknown option|Missing value|Unexpected argument/);
    }
  });
}
test('Organize production comparison changes all three copies without mutating source', () => {
  for (const resource of ['compute','runway']) {
    const m=fixture({rulesVariant:{organizeProduction:resource}});
    const hexes=m.board.filter(t=>t.actionId==='organize');
    assert.equal(hexes.length,3);
    assert.ok(hexes.every(t=>t.yield.resource===resource && t.yield.amount===1));
  }
  assert.throws(()=>fixture({rulesVariant:{organizeProduction:'capability'}}),/Invalid Organize/);
  assert.equal(config.board.tiles.find(t=>t.id==='organize').yield.resource,'runway');
});

test('recruitment availability, preview and payment use the same configured cost', () => {
  const cfg=structuredClone(config);
  cfg.actionEffects.organize.recruitCost=3;
  const m=fixture({config:cfg});
  const p=m.players[0];
  p.runway=2;
  assert.ok(!m.legalResolutions(0,'organize').some(d=>d.parameters.mode==='recruit'));
  p.runway=3;
  const d=m.legalResolutions(0,'organize').find(d=>d.parameters.mode==='recruit');
  assert.equal(d.consequences.runway,-3);
  m.applyResolution(0,d);
  assert.equal(p.runway,0);
  assert.equal(p.pieces.length,3);
});
