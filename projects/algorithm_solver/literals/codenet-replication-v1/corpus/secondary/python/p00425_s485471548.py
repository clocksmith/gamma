operation = {"North": (1, 5, 2, 3, 0, 4),
             "East": (3, 1, 0, 5, 4, 2),
             "West": (2, 1, 5, 0, 4, 3),
             "South": (4, 0, 2, 3, 5, 1),
             "Right": (0, 2, 4, 1, 3, 5),
             "Left": (0, 3, 1, 4, 2, 5)}

while True:
    n = int(input())
    if n == 0:
        break
    
    dice = list(range(1, 7))
    ans = 1
    for _ in range(n):
        indices = operation[input().strip()]
        dice = [dice[i] for i in indices]
        ans += dice[0]
        
    print(ans)
