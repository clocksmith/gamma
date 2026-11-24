def insert(r, n):
    if 0 == len(T):
        T[n] = [None, None, None]
    else:
        if n < r:
            left = T[r][0]
            if left == None:
                T[r][0] = n
                T[n] = [None, None, r]
            else:
                insert(left, n)
        if r < n:
            right = T[r][1]
            if right == None:
                T[r][1] = n
                T[n] = [None, None, r]
            else:
                insert(right, n)

def find(n):
    if n in T:
        return True
    else:
        return False

def dele(r, n):
    z = T[n]
    left = z[0]
    right = z[1]
    p = z[2]
    if left is None and right is None:
        i = T[p].index(n)
        T[p][i] = None
        del T[n]
    elif left is None and right is not None:
        x = T[p].index(n)
        T[p][x] = right
        T[right][2] = z[2]
        del T[n]
    elif left is not None and right is None:
        x = T[p].index(n)
        T[p][x] = left
        T[left][2] = z[2]
        del T[n]
    elif left is not None and right is not None:
        inorder = list(map(int, print_inorder(r).split()))
        next_n = inorder[inorder.index(n) + 1]
        if r == n:
            r = next_n
        dele(r, next_n)
        T[next_n] = T[n]
        del T[n]
        n_r = T[next_n][1]
        n_p = T[next_n][2]
        if n_r is not None:
            v = T[n_r]
            if v[0] == n:
                v[0] = next_n
            if v[1] == n:
                v[1] = next_n
            if v[2] == n:
                v[2] = next_n
        if n_p is not None:
            v = T[n_p]
            if v[0] == n:
                v[0] = next_n
            if v[1] == n:
                v[1] = next_n
            if v[2] == n:
                v[2] = next_n
    return r

def print_inorder(r):
    left = T[r][0]
    right = T[r][1]
    ans = ""
    if left != None:
        ans += print_inorder(left)
    ans += " {}".format(r)
    if right != None:
        ans += print_inorder(right)
    return ans

def print_preorder(r):
    left = T[r][0]
    right = T[r][1]
    ans = " {}".format(r)
    if left != None:
        ans += print_preorder(left)
    if right != None:
        ans += print_preorder(right)
    return ans

n = int(input())
T = {}

root = None
for i in range(n):
    inst = input()
    if inst[0] == 'i':
        num = int(inst[7:])
        if i == 0:
            root = num
        insert(root, num)
    elif inst[0] == 'f':
        num = int(inst[5:])
        if find(num):
            print("yes")
        else:
            print("no")
    elif inst[0] == 'd':
        num = int(inst[7:])
        root = dele(root, num)
    elif inst[0] == 'p':
        print(print_inorder(root))
        print(print_preorder(root))