#演習2-17

coins = [10, 50, 100, 500]
def solve(price):
    maisuu = list(map(int, input().split()))
    pay = [0, 0, 0, 0]
    otsuri = sum([maisuu[i] * coins[i] for i in range(len(coins))]) - price
    otsuri_maisuu = [otsuri % 50 // 10, otsuri % 100 // 50, otsuri % 500 // 100, otsuri // 500]
    for types, saifu, tsuri in zip(coins, maisuu, otsuri_maisuu):
        if saifu > tsuri:
            print(types, saifu - tsuri)
            
p = int(input())
solve(p)
while True:
    p = int(input())
    if not p:
        break
    print()
    solve(p)
