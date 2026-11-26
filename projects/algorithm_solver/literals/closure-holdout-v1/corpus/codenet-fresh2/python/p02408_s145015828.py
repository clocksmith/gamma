n = int(input())
suits = ('S', 'H', 'C', 'D')
cards = dict(zip(suits, [[]]*4))
for i in range(n):
    card = input().split()
    cards[card[0]] = cards[card[0]] + [int(card[1])]
a_suit = list(range(1, 14))
for k in suits:
    temp = a_suit[:]
    for c in cards[k]:
        temp.remove(c)
    cards[k] = temp
for s in suits:
    for i in range(len(cards[s])):
        print(s, cards[s][i])
