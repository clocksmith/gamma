class Solution {
  isLongPressedName(name, typed) {
    let matched = 0;
    for (let index = 0; index < typed.length; index += 1) {
      const character = typed[index];
      if (matched < name.length && character === name[matched]) {
        matched += 1;
      } else if (index === 0 || character !== typed[index - 1]) {
        return false;
      }
    }
    return matched === name.length;
  }
}
