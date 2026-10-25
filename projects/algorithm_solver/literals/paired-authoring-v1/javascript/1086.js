class Solution {
  highFive(items) {
    const leaders = new Map();
    for (const [student, score] of items) {
      if (!leaders.has(student)) {
        leaders.set(student, []);
      }
      const best = leaders.get(student);
      best.push(score);
      best.sort((left, right) => right - left);
      if (best.length > 5) {
        best.pop();
      }
    }
    const students = Array.from(leaders.keys()).sort((left, right) => left - right);
    const result = [];
    for (const student of students) {
      let total = 0;
      for (const score of leaders.get(student)) {
        total += score;
      }
      result.push([student, Math.floor(total / 5)]);
    }
    return result;
  }
}
