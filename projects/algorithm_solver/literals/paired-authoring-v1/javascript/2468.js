class Solution {
  splitMessage(message, limit) {
    let digitTotal = 0;
    let parts = 0;
    for (let candidate = 1; candidate <= message.length; candidate += 1) {
      const digits = String(candidate).length;
      digitTotal += digits;
      if (limit <= 2 * digits + 3) {
        return [];
      }
      const capacity = candidate * (limit - digits - 3) - digitTotal;
      if (capacity >= message.length) {
        parts = candidate;
        break;
      }
    }
    if (parts === 0) {
      return [];
    }
    const output = [];
    let offset = 0;
    for (let index = 1; index <= parts; index += 1) {
      const suffix = "<" + String(index) + "/" + String(parts) + ">";
      const capacity = limit - suffix.length;
      output.push(message.slice(offset, offset + capacity) + suffix);
      offset += capacity;
    }
    return output;
  }
}
