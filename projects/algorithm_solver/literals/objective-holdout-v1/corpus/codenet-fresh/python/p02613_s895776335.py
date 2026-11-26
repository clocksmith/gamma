N=int(input())

AC=0
WA=0
TLE=0
RE=0


for i in range(N):
	word = input()
	if word =="AC":
		AC+=1
	if word =="WA":
		WA+=1
	if word =="TLE":
		TLE+=1
	if word =="RE":
		RE+=1
print("AC x " +str(AC))
print("WA x " +str(WA))
print("TLE x " +str(TLE))
print("RE x " +str(RE))