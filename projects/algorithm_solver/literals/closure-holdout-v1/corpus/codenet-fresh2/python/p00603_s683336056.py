import sys
lines=[]
for line in sys.stdin:
    line= line.rstrip()
    lines.append(line)

for i in range(len(lines)//2):
    N,R=map(int,lines[2*i].split())
    ops=list(map(int,lines[2*i+1].split()))
    cards=[i for i in range(N)]
    for c in ops:
        deck_a=cards[N//2:N]
        deck_b=cards[0:N//2]
        deck_c=cards[0:0]
        while len(deck_a)>0 or len(deck_b)>0:
            d=deck_a[0:c]
            deck_a=deck_a[c:]
            deck_c+=d

            d=deck_b[0:c]
            deck_b=deck_b[c:]
            deck_c+=d
        cards=deck_c
    print(cards[-1])