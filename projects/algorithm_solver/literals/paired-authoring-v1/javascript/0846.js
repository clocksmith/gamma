class Solution {
  isNStraightHand(hand, groupSize) {
    if (hand.length % groupSize !== 0) {
      return false;
    }

    const counts = new Map();
    for (const value of hand) {
      counts.set(value, (counts.get(value) || 0) + 1);
    }
    const ordered = Array.from(counts.keys()).sort((left, right) => {
      if (left < right) {
        return -1;
      }
      if (left > right) {
        return 1;
      }
      return 0;
    });
    for (const start of ordered) {
      const remaining = counts.get(start);
      if (remaining === 0) {
        continue;
      }
      for (let offset = 0; offset < groupSize; offset += 1) {
        const value = start + offset;
        const available = counts.get(value) || 0;
        if (available < remaining) {
          return false;
        }
        counts.set(value, available - remaining);
      }
    }
    return true;
  }
}
