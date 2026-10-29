"""Original frontend 1500 variant; qualification unknown."""
import heapq


class FileSharing:
    def __init__(self, m: int):
        self.m = m
        self.free_ids = []
        self.next_id = 1
        self.user_chunks = {}
        self.chunk_users = {}

    def join(self, ownedChunks) -> int:
        if self.free_ids:
            uid = heapq.heappop(self.free_ids)
        else:
            uid = self.next_id
            self.next_id += 1
        chunks = set(ownedChunks)
        self.user_chunks[uid] = chunks
        for c in chunks:
            self.chunk_users.setdefault(c, set()).add(uid)
        return uid

    def leave(self, userID: int) -> None:
        chunks = self.user_chunks.pop(userID, ())
        for c in chunks:
            s = self.chunk_users.get(c)
            if s is not None:
                s.discard(userID)
        heapq.heappush(self.free_ids, userID)

    def request(self, userID: int, chunkID: int):
        owners = sorted(self.chunk_users.get(chunkID, ()))
        if owners:
            self.user_chunks[userID].add(chunkID)
            self.chunk_users.setdefault(chunkID, set()).add(userID)
        return owners


def solve(operation_names, argument_lists):
    inst = FileSharing(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "join":
            out.append(inst.join(args[0]))
        elif op == "leave":
            inst.leave(args[0])
            out.append(None)
        else:
            out.append(inst.request(args[0], args[1]))
    return out
