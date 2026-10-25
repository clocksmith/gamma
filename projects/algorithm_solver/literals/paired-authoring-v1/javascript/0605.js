class Solution {
  canPlaceFlowers(flowerbed, n) {
    if (n === 0) {
      return true;
    }

    let planted = 0;
    let previous = 0;
    for (let index = 0; index < flowerbed.length; index += 1) {
      const current = flowerbed[index];
      const following = index + 1 < flowerbed.length ? flowerbed[index + 1] : 0;
      if (previous === 0 && current === 0 && following === 0) {
        planted += 1;
        previous = 1;
        if (planted >= n) {
          return true;
        }
      } else {
        previous = current;
      }
    }
    return false;
  }
}
