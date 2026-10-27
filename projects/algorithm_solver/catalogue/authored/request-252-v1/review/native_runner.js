'use strict';
// Expected values and sequence generation live in the independent test process.
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const root = path.resolve(__dirname, '..');
const cases = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const names = {3242: 'NeighborSum', 3408: 'TaskManager', 3484: 'Spreadsheet', 3508: 'Router'};
const instances = cases.map(test => {
    const args = structuredClone(test.constructor);
    const Constructor = require(path.join(root, 'javascript', `${test.problem_id}.js`))[names[test.problem_id]];
    const instance = new Constructor(...args);
    assert.deepStrictEqual(args, test.constructor, `constructor mutated input: ${test.problem_id}`);
    return instance;
});
let calls = 0;
// Interleave all 146 instances: accidental class/global state cannot pass serially.
for (let step = 0; step < Math.max(...cases.map(test => test.steps.length)); step++) {
    for (let i = 0; i < cases.length; i++) {
        if (step >= cases[i].steps.length) continue;
        const [method, originalArgs, expected] = cases[i].steps[step];
        const args = structuredClone(originalArgs);
        const actual = instances[i][method](...args);
        assert.deepStrictEqual(actual === undefined ? null : actual, expected,
            `id=${cases[i].problem_id} instance=${i} step=${step} method=${method}`);
        assert.deepStrictEqual(args, originalArgs, `method mutated input: ${method}`);
        calls++;
    }
}
const linked = require(path.join(root, 'javascript', '3217.js'));
let nativeLists = 0;
for (const size of [...Array.from({length: 64}, (_, i) => i + 1), 100000]) {
    const nodes = Array.from({length: size}, (_, i) => new linked.ListNode(i % 7 + 1));
    for (let i = 1; i < size; i++) nodes[i - 1].next = nodes[i];
    const removed = [2, 4, 6];
    const expected = nodes.filter(node => !removed.includes(node.val));
    let result = linked.modifiedList(removed, nodes[0]);
    for (const node of expected) {
        assert.strictEqual(result, node, `survivor identity changed at size ${size}`);
        result = result.next;
    }
    assert.strictEqual(result, null);
    assert.deepStrictEqual(removed, [2, 4, 6]);
    nativeLists++;
}
process.stdout.write(JSON.stringify({instances: cases.length, native_calls: calls, linked_identity_cases: nativeLists}));
