def cut(S,H,W,K):
    cnt,h = 0,0
    OP = [[0 for _ in range(W)] for _ in range(H)]

    while "#" not in S[h]:
        h += 1

    burst = False
    for i in range(h,H):
        if "#" not in S[i]:
            OP[i] = [OP[i-1][j] for j in range(W)]
            burst = False
        else:
            cnt += 1
            cnt_h = 1
            for j in range(W):
                OP[i][j] = cnt
                if S[i][j] == "#" and cnt_h < S[i].count("#"):
                    cnt += 1
                    cnt_h += 1

    for i in reversed(range(h)):
        for j in range(W):
            OP[i][j] = OP[i+1][j]
    
    for i in range(H):
        OP[i] = " ".join(map(str,OP[i]))

    return OP

def main():
    H,W,K = map(int,input().split())
    S = [input() for _ in range(H)]

    ans = cut(S,H,W,K)

    for i in range(H):
        print(ans[i])

if __name__ == "__main__":
    main()
