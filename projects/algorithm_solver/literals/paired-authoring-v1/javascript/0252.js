function sortedEndpoints(intervals) {
  const compareEndpoints = (left, right) => {
    if (left < right) {
      return -1;
    }
    if (left > right) {
      return 1;
    }
    return 0;
  };
  const starts = intervals.map((interval) => interval[0]);
  const ends = intervals.map((interval) => interval[1]);
  starts.sort(compareEndpoints);
  ends.sort(compareEndpoints);
  return [starts, ends];
}

class Solution {
  canAttendMeetings(intervals) {
    const [starts, ends] = sortedEndpoints(intervals);
    for (let index = 1; index < starts.length; index += 1) {
      // Touching half-open meetings do not overlap.
      if (starts[index] < ends[index - 1]) {
        return false;
      }
    }
    return true;
  }
}
