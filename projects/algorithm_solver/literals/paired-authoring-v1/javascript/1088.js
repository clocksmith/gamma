class Solution {
  confusingNumberII(limit) {
    const digits = [[0, 0], [1, 1], [6, 9], [8, 8], [9, 6]];
    const pending = [[0, 0, 1]];
    let total = 0;
    while (pending.length > 0) {
      const [number, rotated, place] = pending.pop();
      if (number !== rotated) {
        total += 1;
      }
      for (const [digit, rotation] of digits) {
        const successor = number * 10 + digit;
        if (successor > 0 && successor <= limit) {
          pending.push([successor, rotation * place + rotated, place * 10]);
        }
      }
    }
    return total;
  }
}
