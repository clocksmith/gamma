class Solution {
  maximumUnits(boxTypes, truckSize) {
    const ordered = boxTypes.slice().sort((first, second) => second[1] - first[1]);
    let remaining = truckSize;
    let units = 0;
    for (const [boxes, perBox] of ordered) {
      const taken = Math.min(boxes, remaining);
      units += taken * perBox;
      remaining -= taken;
      if (remaining === 0) {
        break;
      }
    }
    return units;
  }
}
