class Solution {
  calculateTime(keyboard, word) {
    const positions = Array(26).fill(0);
    const firstCode = "a".charCodeAt(0);
    for (let index = 0; index < keyboard.length; index += 1) {
      positions[keyboard.charCodeAt(index) - firstCode] = index;
    }
    let current = 0;
    let time = 0;
    for (const character of word) {
      const destination = positions[character.charCodeAt(0) - firstCode];
      time += Math.abs(destination - current);
      current = destination;
    }
    return time;
  }
}
