class Solution {
  canPlaceFlowers(values, count) {
    if (count <= 0) return true;
    let previous = 0;
    for (let index = 0; index < values.length; index++) {
      const next = index + 1 < values.length ? values[index + 1] : 0;
      if (values[index] === 0 && previous === 0 && next === 0) {
        count--;
        previous = 1;
        if (count <= 0) return true;
      } else {
        previous = values[index];
      }
    }
    return false;
  }
}
