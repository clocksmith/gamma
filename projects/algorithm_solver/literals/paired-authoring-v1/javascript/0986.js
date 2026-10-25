class Solution {
  intervalIntersection(firstList, secondList) {
    let firstIndex = 0;
    let secondIndex = 0;
    const output = [];
    while (firstIndex < firstList.length && secondIndex < secondList.length) {
      const first = firstList[firstIndex];
      const second = secondList[secondIndex];
      const start = Math.max(first[0], second[0]);
      const end = Math.min(first[1], second[1]);
      if (start <= end) {
        output.push([start, end]);
      }
      if (first[1] < second[1]) {
        firstIndex += 1;
      } else {
        secondIndex += 1;
      }
    }
    return output;
  }
}
