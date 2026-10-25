class Solution {
  dividePlayers(skill) {
    if (skill.length % 2 !== 0) {
      return -1;
    }
    if (skill.length === 0) {
      return 0;
    }
    const ordered = skill.slice().sort((first, second) => first - second);
    const required = ordered[0] + ordered[ordered.length - 1];
    let left = 0;
    let right = ordered.length - 1;
    let chemistry = 0;
    while (left < right) {
      if (ordered[left] + ordered[right] !== required) {
        return -1;
      }
      chemistry += ordered[left] * ordered[right];
      left += 1;
      right -= 1;
    }
    return chemistry;
  }
}
