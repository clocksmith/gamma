class Solution {
  dayOfYear(date) {
    const year = Number(date.slice(0, 4));
    const month = Number(date.slice(5, 7));
    const day = Number(date.slice(8, 10));
    const lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if (year % 400 === 0 || (year % 4 === 0 && year % 100 !== 0)) {
      lengths[1] = 29;
    }
    let ordinal = day;
    for (let index = 0; index < month - 1; index += 1) {
      ordinal += lengths[index];
    }
    return ordinal;
  }
}
