import sys
texts=sys.stdin.read()
texts=texts.lower()
cnt=[0]*26

letters=list('abcdefghijklmnopqrstuvwxyz')
for x in texts:
    i=0
    for y in letters:
        if x==y:
            cnt[i]+=1
        i+=1
for i in range(26):
    print(letters[i]+' : '+str(cnt[i]) )

