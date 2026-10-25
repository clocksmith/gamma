class Solution {
  restoreIpAddresses(s) {
    if (s.length < 4 || s.length > 12) {
      return [];
    }

    const addresses = [];
    const parts = [];

    function collect(start) {
      const slots = 4 - parts.length;
      const remaining = s.length - start;
      if (remaining < slots || remaining > 3 * slots) {
        return;
      }
      if (slots === 0) {
        addresses.push(parts.join("."));
        return;
      }

      let value = 0;
      for (let end = start; end < Math.min(start + 3, s.length); end += 1) {
        if (end > start && s[start] === "0") {
          break;
        }
        value = value * 10 + s.charCodeAt(end) - 48;
        if (value > 255) {
          break;
        }
        parts.push(s.slice(start, end + 1));
        collect(end + 1);
        parts.pop();
      }
    }

    collect(0);
    return addresses;
  }
}
