class ListNode {
    constructor(val = 0, next = null) {
        this.val = val;
        this.next = next;
    }
}

function modifiedList(nums, head) {
    const removed = new Set(nums);
    const dummy = new ListNode(0, head);
    let previous = dummy;
    while (previous.next !== null) {
        if (removed.has(previous.next.val)) previous.next = previous.next.next;
        else previous = previous.next;
    }
    return dummy.next;
}

// Value-array adapter does not mutate either input array.
function solve(nums, headValues) {
    let head = null;
    for (let i = headValues.length - 1; i >= 0; --i) {
        head = new ListNode(headValues[i], head);
    }
    const result = [];
    for (let node = modifiedList(nums, head); node !== null; node = node.next) {
        result.push(node.val);
    }
    return result;
}
module.exports = {solve, ListNode, modifiedList};
