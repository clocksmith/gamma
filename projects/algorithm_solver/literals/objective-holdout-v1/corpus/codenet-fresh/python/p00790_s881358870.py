# AOJ 1210: Die Game
# Python3 2018.7.22 bal4u

dic = {'s':1, 'w':2, 'e':3, 'n':4}
rot = [[0,1,2,3,4,5,6],[0,2,6,3,4,1,5],[0,4,2,1,6,5,3],[0,3,2,6,1,5,4],[0,5,1,3,4,6,2]]
	
while True:
    n = int(input())
    if n == 0: break
    dice = [i for i in range(7)]
    for j in range(n):
        a = input()[0]
        dice = [dice[rot[dic[a]][i]] for i in range(7)]
    print(dice[1])
