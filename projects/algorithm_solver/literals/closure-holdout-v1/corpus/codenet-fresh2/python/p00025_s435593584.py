import sys
Lines = sys.stdin.readlines()

for i in range(0, len(Lines), 2):
    Anumbers = list(map(int, Lines[i].split()))
    Bnumbers = list(map(int, Lines[i+1].split()))
    Hit = 0    
    for j in range(len(Anumbers)):
        Hit += 1 if (Anumbers[j] == Bnumbers[j]) else 0
    Blow = len(set(Anumbers) & set(Bnumbers)) - Hit
    print(Hit, Blow)