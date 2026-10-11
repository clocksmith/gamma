import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {config, factions, headlines, mandates} from './helpers/smaller-game.mjs';
test('writing-free kit preserves all 82 cards with 153 physical items', () => {
  const cards=config.trainingDeck.cards.reduce((n,c)=>n+c.count,0)+factions.factions.length+headlines.headlines.length+mandates.mandates.length;
  const pieces=config.sharedSupply.hexTiles+config.playerKits.length*(config.playerSupply.agents+config.playerSupply.resourceTrackCubes)+config.sharedSupply.playerMats+config.sharedSupply.currentEraMarkers+config.sharedSupply.initiativeMarkers;
  assert.equal(cards,82);
  assert.equal(cards+pieces,153);
  assert.equal(config.sharedSupply.pencils,undefined);
  assert.equal(config.scoreDisplay.maximum,config.resources.capability.cap*config.scoring.capability+config.resources.customers.cap*config.scoring.customer+config.resources.reputation.cap*config.scoring.reputation+config.scoring.agi+config.rounds.length*config.scoring.objectiveWinner);
});
test('printed score encodes every value and both recognition states without writing', async () => {
  const html=await readFile(new URL('../dist/site/gallery-baseline.html',import.meta.url),'utf8');
  assert.equal((html.match(/class="final-score-scale"/g)||[]).length,5);
  for(let n=0;n<=config.scoreDisplay.maximum;n++)assert.equal((html.match(new RegExp(`data-score="${n}"`,'g'))||[]).length,5);
  assert.equal((html.match(/class="identity-pointer pointer-top"/g)||[]).length,6);
  assert.equal((html.match(/class="identity-pointer pointer-bottom"/g)||[]).length,6);
  assert.doesNotMatch(html,/Final Mandate: _|AGI recognized: □/);
});
