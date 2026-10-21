# Exact source and selection examples

Before: the previously qualified readable source. After: a sequence of exact dictionary IDs that reconstructs precisely those same bytes. This experiment does not rewrite these sources. The listed packet bits include framing and byte padding; no operands are free.

## Keys and Rooms — javascript

Dictionary SHA-256: `ded93fc6e9aad026bce6088abbf6a1981accfc2eb2d739126866385789a5f41a`. Source SHA-256: `655ee684718dcea651407a4ab7db7240d75ed7e07ba5075ad2f156b2d6546584`.

22 selections × 6 = 132 selection bits; 4 padding bits; 328 framing bits; total 464 packet bits.

Before and exact decoded after:

```javascript
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
```

After, dictionary IDs:

```json
[59, 41, 54, 38, 49, 55, 26, 27, 19, 12, 11, 10, 24, 34, 57, 51, 62, 58, 35, 30, 57, 62]
```

All string values are in [javascript-6-small-statements/dictionary.json](profiles/javascript-6-small-statements/dictionary.json). The original public fixture contract remains unchanged.

## Keys and Rooms — python

Dictionary SHA-256: `f109a07f52e2892f32b41c88ac6eadfa1a780198bb9012f1aeb645c1052bd671`. Source SHA-256: `65d9ab32e064ccd2e1e4aa5c9eddc65478dfd887b81bfdb2c429dae2e2772e49`.

17 selections × 6 = 102 selection bits; 2 padding bits; 328 framing bits; total 432 packet bits.

Before and exact decoded after:

```python
def can_reach_all_rooms(room_keys: list[list[int]]) -> bool:
    visited_rooms = ([False] * len(room_keys))
    visited_rooms[0] = True
    pending_rooms = [0]
    visited_count = 1
    while pending_rooms:
        room_index = pending_rooms.pop()
        for next_room in room_keys[room_index]:
            if (not visited_rooms[next_room]):
                visited_rooms[next_room] = True
                visited_count += 1
                pending_rooms.append(next_room)
    return (visited_count == len(room_keys))

class Solution:
    def canVisitAllRooms(self, rooms: list[list[int]]) -> bool:
        return can_reach_all_rooms(rooms)
```

After, dictionary IDs:

```json
[50, 45, 46, 37, 43, 48, 25, 18, 13, 8, 7, 6, 41, 0, 49, 28, 22]
```

All string values are in [python-6-small-statements/dictionary.json](profiles/python-6-small-statements/dictionary.json). The original public fixture contract remains unchanged.
