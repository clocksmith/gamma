'use strict';
// Local receiver/dispatch stubs only. No numbered candidate module is loaded.
const assert = require('node:assert/strict');
const {observe, shape} = require('./native_harness.cjs');
const transport = require('../../public-domain-qualification-easy16-v1/harness.cjs');

const created = [], receivers = [];
class ExamTracker {
  constructor() {this.count = 0; created.push(this);}
  record(time, score) {this.count++; receivers.push(this);}
  totalScore(startTime, endTime) {receivers.push(this); return this.count;}
}
function forbiddenSolve() {throw Error('functional fallback must never execute');}
forbiddenSolve.ExamTracker = ExamTracker;
const args = [['ExamTracker', 'record', 'record', 'totalScore'], [[], [1, 1], [2, 1], [1, 2]]];
for (let i = 0; i < 2; i++) {
  const row = observe(forbiddenSolve, 3709, {args}, transport);
  assert.deepEqual(row.result, [null, null, null, 2]);
  assert.deepEqual(row.native_method_return_types, ['constructed', 'undefined', 'undefined', 'number']);
  assert.deepEqual(row.native_method_snapshots, row.result);
  assert.equal(row.native_receiver_count, 1);
  assert.deepEqual(row.args_before, args);
  assert.deepEqual(row.args_after, args);
  assert.deepEqual(row.alias_edges, []);
}
assert.equal(created.length, 2);
assert(receivers.slice(0, 3).every(x => x === created[0]));
assert(receivers.slice(3).every(x => x === created[1]));
assert.throws(() => observe({}, 3709, {args}, transport), /original named class export/);
assert.throws(() => observe(forbiddenSolve, 3709, {args, expected: 9}, transport), /argument-only/);
assert.throws(() => shape(3709, [['ExamTracker', '__proto__'], [[], []]]), /unapproved/);
assert.throws(() => shape(3709, [['ExamTracker', 'record'], [[], [1]]]), /unapproved/);
assert.throws(() => shape(true, args), /exact native identity/);
class WrongConstructor {constructor() {return {};}}
assert.throws(() => observe({ExamTracker: WrongConstructor}, 3709, {args: [['ExamTracker'], [[]]]}, transport), /own instance/);

class AuctionSystem {
  constructor() {this.events = 0;}
  addBid() {this.events++;}
  updateBid() {this.events++;}
  removeBid() {this.events++;}
  getHighestBidder() {return this.events;}
}
const auction = observe({AuctionSystem}, 3815, {args: [['AuctionSystem', 'addBid', 'updateBid', 'removeBid', 'getHighestBidder'], [[], [1, 1, 1], [1, 1, 2], [1, 1], [1]]]}, transport);
assert.deepEqual(auction.result, [null, null, null, null, 3]);

class RideSharingSystem {
  constructor() {this.calls = 0;}
  addRider() {this.calls++;}
  addDriver() {this.calls++;}
  cancelRider() {this.calls++;}
  matchDriverWithRider() {return [this.calls, this.calls];}
}
const ride = observe({RideSharingSystem}, 3829, {args: [['RideSharingSystem', 'addRider', 'addDriver', 'matchDriverWithRider'], [[], [2], [2], []]]}, transport);
assert.deepEqual(ride.result, [null, null, null, [2, 2]]);
console.log('Direct native observer synthetic controls passed: all three class routes; no candidate execution.');
