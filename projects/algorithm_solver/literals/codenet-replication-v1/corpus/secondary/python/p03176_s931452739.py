import sys
input = sys.stdin.readline

N=int(input())
H=list(map(int,input().split()))
A=list(map(int,input().split()))


#Segment tree（区間の最大値を求めるバージョン）
for i in range(30):#要素数以上の2のベキを見つける
    if N<=2**i:
        seg_el=2**i#Segment treeの台の要素数
        break

SEG=[0]*(2*seg_el-1)#Segment treeを一次元リストとして作る

def update(n,x,seg_el):#A[n]=xに更新（反映）
    i=n+seg_el-1
    while i>=0:
        SEG[i]=max(x,SEG[i])
        i=(i-1)//2

def getvalues(a,b,k,l,r):#区間[a,b)での,SEG[k],つまり区間[l,r)に関する最大値を調べる
    if r<=a or b<=l:#区間[a,b)が対象区間の外にあれば,infを出力
        return -float("inf")
    if a<=l and r<=b:#区間[a,b)が対象区間の中にあればSEG[k]を出力
        return SEG[k]
    vl=getvalues(a,b,k*2+1,l,(l+r)//2)#それ以外のときは,SEG[k*2+1]とSEG[k*2+2]で場合分け（木の子ノード二つを見る）
    vr=getvalues(a,b,k*2+2,(l+r)//2,r)
    return max(vl,vr)

for i in range(N):
    h,a=H[i],A[i]
    x=getvalues(0,h,0,0,seg_el)
    update(h-1,x+a,seg_el)

print(getvalues(0,N,0,0,seg_el))