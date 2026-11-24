def main():
    while True:
        n = int(input())
        if n == 0: break

        teams = []
        for i in range(n):
            teams.append(list(map(int, input().split())))
       
        def same_len(l):
            return len(list(filter(lambda x: x[1] == e[1], ans))) 

        ans = []
        rank = sorted(sorted(sorted(teams, key=lambda x: x[0]), key=lambda x: x[3]), key=lambda x: x[2], reverse=True) 
        for e in rank:
            if len(ans) < 10 and same_len(ans) < 3:
                ans.append(e)
            elif len(ans) < 20 and same_len(ans) < 2:
                ans.append(e)
            elif len(ans) < 26 and same_len(ans) == 0:
                ans.append(e)

        for a in ans:
            print(a[0])


if __name__ == "__main__":
    main()


