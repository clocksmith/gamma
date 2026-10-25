class Solution {
  confusingNumberII(limit) {
    if (limit <= 0) return 0;
    const digits = [0, 1, 6, 8, 9];
    const rotations = [0, 1, 9, 8, 6];
    const bound = String(limit);
    let total = 0;
    for (let length = 1; length < bound.length; length += 1) total += 4 * 5 ** (length - 1);
    let complete = true;
    for (let index = 0; index < bound.length; index += 1) {
      const digit = Number(bound[index]);
      const allowed = index === 0 ? digits.slice(1) : digits;
      total += allowed.filter(value => value < digit).length * 5 ** (bound.length - index - 1);
      if (!allowed.includes(digit)) {
        complete = false;
        break;
      }
    }
    if (complete) total += 1;
    let unchanged = 0;
    function visit(buffer, left, right) {
      if (left > right) {
        const value = Number(buffer.join(""));
        if (value > 0 && value <= limit) unchanged += 1;
        return;
      }
      for (let index = 0; index < digits.length; index += 1) {
        const digit = digits[index];
        const rotation = rotations[index];
        if (left === 0 && buffer.length > 1 && digit === 0) continue;
        if (left === right && digit !== rotation) continue;
        buffer[left] = String(digit);
        buffer[right] = String(rotation);
        visit(buffer, left + 1, right - 1);
      }
    }
    for (let length = 1; length <= bound.length; length += 1) visit(new Array(length).fill(""), 0, length - 1);
    return total - unchanged;
  }
}
