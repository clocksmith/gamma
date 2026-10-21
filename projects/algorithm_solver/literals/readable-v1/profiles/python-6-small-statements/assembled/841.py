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
