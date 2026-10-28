class Solution:
    def solveSudoku(self, board):
        rows, columns, boxes = [0] * 9, [0] * 9, [0] * 9
        empty = []
        for r in range(9):
            for c in range(9):
                if board[r][c] == '.':
                    empty.append((r, c))
                else:
                    bit = 1 << (int(board[r][c]) - 1)
                    rows[r] |= bit
                    columns[c] |= bit
                    boxes[(r // 3) * 3 + c // 3] |= bit
        def search(index):
            if index == len(empty):
                return True
            best = index
            best_count = 10
            for j in range(index, len(empty)):
                r, c = empty[j]
                mask = 511 & ~(rows[r] | columns[c] | boxes[(r // 3) * 3 + c // 3])
                count = mask.bit_count()
                if count < best_count:
                    best, best_count = j, count
                if count <= 1:
                    break
            if best_count == 0:
                return False
            empty[index], empty[best] = empty[best], empty[index]
            r, c = empty[index]
            box = (r // 3) * 3 + c // 3
            mask = 511 & ~(rows[r] | columns[c] | boxes[box])
            while mask:
                bit = mask & -mask
                mask -= bit
                rows[r] |= bit
                columns[c] |= bit
                boxes[box] |= bit
                board[r][c] = str(bit.bit_length())
                if search(index + 1):
                    return True
                rows[r] ^= bit
                columns[c] ^= bit
                boxes[box] ^= bit
                board[r][c] = '.'
            empty[index], empty[best] = empty[best], empty[index]
            return False
        search(0)
