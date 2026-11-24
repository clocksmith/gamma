N,K=1407,38
print(N,K)
P=0
ANS=[]
for i in range(K):
  P=[]
  P.append(1)
  for j in range(i*(K-1)+2,i*(K-1)+K+1):
    P.append(j)
  print(*P)
  ANS.append(set(P))
def f(R):
  Q=R[:]
  for i in range(len(Q)):
    Q[i]=Q[i]+i*(K-1)+2
  return Q
for i in range(2,K+1):
  X=[0]*K
  for j in range(K-1):
    X[j+1]=(X[j+1]+(i-2)*j)%(K-1)
  X[0]=i-2
  for j in range(K-1):
    print(*f(X))
    ANS.append(set(f(X)))
    for k in range(1,K):
      X[k]=(X[k]+1)%(K-1)