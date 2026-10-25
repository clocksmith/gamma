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
      counts[index]++;
    }

    let missing = window_size;
    for (let right = 0; right < s2.length; right++) {
      const incoming = s2.charCodeAt(right) - 97;
      if (counts[incoming] > 0) {
        missing--;
      }
      counts[incoming]--;

      if (right >= window_size) {
        const outgoing = s2.charCodeAt(right - window_size) - 97;
        counts[outgoing]++;
        if (counts[outgoing] > 0) {
          missing++;
        }
      }

      if (missing === 0) {
        return true;
      }
    }
    return false;
  }
}
