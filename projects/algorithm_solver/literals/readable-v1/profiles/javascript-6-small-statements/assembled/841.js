function canReachAllRooms(roomKeys) {
  const visitedRooms = Array(roomKeys.length).fill(false);
  visitedRooms[0] = true;
  const pendingRooms = [0];
  let visitedCount = 1;
  while ((pendingRooms.length > 0)) {
    const roomIndex = pendingRooms.pop();
    for (const nextRoom of roomKeys[roomIndex]) {
      if ((!visitedRooms[nextRoom])) {
        visitedRooms[nextRoom] = true;
        visitedCount += 1;
        pendingRooms.push(nextRoom);
      }
    }
  }
  return (visitedCount === roomKeys.length);
}
class Solution {
  canVisitAllRooms(rooms) {
    return canReachAllRooms(rooms);
  }
}
