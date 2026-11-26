def search(a_cards, b_cards, left, right, turn):
  #print(a_cards, b_cards, left, right, turn)
  if a_cards == []:
    return True
  if b_cards == []:
    return False

  ret = False
  if turn == 0:
    if left not in a_cards and right not in a_cards:
      return search(a_cards, b_cards, left, right, 1)
    if left in a_cards:
      ret = ret or search([i for i in a_cards if i != left], b_cards, left - 1, right, 1)
    if right in a_cards:
      ret = ret or search([i for i in a_cards if i != right], b_cards, left, right + 1, 1)
    return ret
  
  ret = True
  if turn == 1:
    if left not in b_cards and right not in b_cards:
      return search(a_cards, b_cards, left, right, 0)
    if left in b_cards:
      ret = ret and search(a_cards, [i for i in b_cards if i != left], left - 1, right, 0)
    if right in b_cards:
      ret = ret and search(a_cards, [i for i in b_cards if i != right], left, right + 1, 0)
    return ret


n = int(input())
all_cards = [i + 1 for i in range(13) if i != 6]
for _ in range(n):
  a_cards = list(map(int, input().split()))
  b_cards = [i for i in all_cards if i not in a_cards]
  if search(a_cards, b_cards, 6, 8, 0):
    print("yes")
  else:
    print("no")
