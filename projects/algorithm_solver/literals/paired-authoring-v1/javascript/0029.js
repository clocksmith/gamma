class Solution {
  divide(dividend, divisor) {
    const negative = (dividend < 0) !== (divisor < 0);
    // Negative magnitudes keep the minimum signed integer representable.
    let remaining = dividend > 0 ? -dividend : dividend;
    let chunk = divisor > 0 ? -divisor : divisor;
    let multiple = -1;
    const chunks = [];
    while (chunk >= remaining) {
      chunks.push([chunk, multiple]);
      if (chunk < -1073741824) {
        break;
      }
      chunk += chunk;
      multiple += multiple;
    }

    let quotient = 0;
    for (let index = chunks.length - 1; index >= 0; index -= 1) {
      const [current_chunk, current_multiple] = chunks[index];
      if (current_chunk >= remaining) {
        remaining -= current_chunk;
        quotient += current_multiple;
      }
    }
    if (quotient === 0) {
      return 0;
    }
    if (negative) {
      return quotient;
    }
    if (quotient === -2147483648) {
      return 2147483647;
    }
    return -quotient;
  }
}
