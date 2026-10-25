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
  minMeetingRooms(intervals) {
    const [starts, ends] = sortedEndpoints(intervals);
    let endIndex = 0;
    let activeRooms = 0;
    let peakRooms = 0;
    for (const start of starts) {
      // Release all rooms whose meetings end at or before this start.
      while (endIndex < ends.length && ends[endIndex] <= start) {
        activeRooms -= 1;
        endIndex += 1;
      }
      activeRooms += 1;
      peakRooms = Math.max(peakRooms, activeRooms);
    }
    return peakRooms;
  }
}
