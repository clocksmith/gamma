#先人の方々の知恵を借りて、workの評価式と<(x-x_r)^2>のテーブルを使ってみる
#clst、xlst、tableをタプル化してパフォーマンスを向上
#比較的重いtb1へのアクセスをsetにする


def main():
    inf=float("inf")

    while 1 :
        n,m=map(int,input().split())
        if (n,m)==(0,0) : break
        clst=tuple(int(input()) for _ in range(m))
        xlst=tuple(int(input()) for _ in range(n))

        #tb1=tuple(tuple(255 if i+work>255 else 0 if i+work<0 else i+work for work in clst) for i in range(256))
        tb1=set((max(0,min(255,i+work)),i) for work in clst for i in range(256))
        #ij成分が(i-j)^2に対応する行列
        tb2=tuple(tuple((i-j)**2 for j in range(256)) for i in range(256))

        dp_new=[inf]*256
        dp_new[128]=0
        for val in xlst:
            dp_old=dp_new[:]
            dp_new=[inf]*256
            xlst_tb=tb2[val]
            for j,i in tb1:
                error=dp_old[i]+xlst_tb[j]
                if error<dp_new[j] :
                    dp_new[j]=error
        
        print(min(dp_new))

main()
