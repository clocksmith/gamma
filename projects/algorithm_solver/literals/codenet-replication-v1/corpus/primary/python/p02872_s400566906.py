import sys
# recieve |V| and |E|
V, E = map(int, input().split())
es = [[] for i in range(V)]

for i in range(E):

	# recieve edges
	a, b, c = map(int, input().split())
	a, b = a-1, b-1
	es[a].append((b,c))
	es[b].append((a,c))

# recieve frequencies
F  = list(map(int,input().split()))

T = int(input())

# recieve info
for i in range(T):

	# the number of new order
	Nnew = int(input())
	for j in range(Nnew):
		new_id, dst = map(int, input().split())

	# the number of items transfered into the car at time t.
	Nput = int(input())
	for j in range(Nput):
		put_id = int(input())

	# insert your code here to get more meaningful output
	# you have to output a command here
	print(-1,flush=True)

	vardict = input()
	if vardict == 'NG':
		sys.exit()

	# the number of orders that have been delivered at time t.
	Nachive = int(input())
	for j in range(Nachive):
		achive_id = int(input())
