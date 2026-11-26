import bisect
    
def main():
    while True:
        d = int(input())
        if d == 0:
            break
        n = int(input())
        m = int(input())
        s = [0] + [int(input()) for i in range(n - 1)] + [d]
        s.sort()
        
        print(sum(dist(s, int(input())) for i in range(m)))

def dist(s, o):
    return min(o- s[bisect.bisect_right(s, o) - 1], s[bisect.bisect_left(s,o)] - o)
        
if __name__=="__main__":
	main()
