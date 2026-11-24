
def MCXI_integer(mcxi):
    n = 0
    buff = 1
    for c in mcxi:
        if c in 'mcxi':
            buff *= 10**(3-['m', 'c', 'x', 'i'].index(c))
            n += buff
            buff = 1
        else:
            buff = int(c)
    return n

def integer_MCXI(n):
    mcxi = ''
    buff = 0
    for i in range(4):
        buff = n%(10**(4-i))//(10**(3-i))
        if buff == 0:
            pass
        elif buff == 1:
            mcxi += 'mcxi'[i]
        else:
            mcxi += str(buff) + 'mcxi'[i]
    return mcxi



def main():
    n = int(input())
    for _ in range(n):
        s = [x for x in input().split()]
        print(integer_MCXI(MCXI_integer(s[0]) + MCXI_integer(s[1])))

if __name__ == '__main__':
    main()