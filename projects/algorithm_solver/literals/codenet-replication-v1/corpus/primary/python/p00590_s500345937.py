while True:
	try:
		n = eval(input())
		is_prime = [True for _ in range(n+1)]
		is_prime[1] = False
		for i in range(2,int((n+1)/2)):
			if is_prime[i]:
				for j in range(i*2,n+1,i):
					is_prime[j] = False
		is_prime_rev = list(is_prime)
		is_prime_rev.reverse()
		count = 0
		for i in range(1,n+1):
			count = count + (1 if is_prime[i] and is_prime_rev[i-1] else 0)
		print(count)
	except EOFError:
		break