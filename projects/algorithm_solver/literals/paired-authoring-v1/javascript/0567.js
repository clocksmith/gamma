class Solution {
  checkInclusion(s1, s2) {
    const window_size = s1.length;
    if (window_size === 0) {
      return true;
    }
    if (window_size > s2.length) {
      return false;
    }

    const counts = new Array(26).fill(0);
    for (const value of s1) {
      const index = value.charCodeAt(0) - 97;
      counts[index] += 1;
    }

    let missing = window_size;
    for (let right = 0; right < s2.length; right += 1) {
      const incoming = s2.charCodeAt(right) - 97;
      if (counts[incoming] > 0) {
        missing -= 1;
      }
      counts[incoming] -= 1;

      if (right >= window_size) {
        const outgoing = s2.charCodeAt(right - window_size) - 97;
        counts[outgoing] += 1;
        if (counts[outgoing] > 0) {
          missing += 1;
        }
      }

      if (missing === 0) {
        return true;
      }
    }
    return false;
  }
}
