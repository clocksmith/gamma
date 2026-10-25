class Solution {
  flipAndInvertImage(image) {
    for (const row of image) {
      let left = 0;
      let right = row.length - 1;
      while (left <= right) {
        const first = row[left];
        const last = row[right];
        row[left] = 1 - last;
        row[right] = 1 - first;
        left += 1;
        right -= 1;
      }
    }
    return image;
  }
}
