while True:

    s = input()

    if s == "#":
        break

    index = -1

    bits = []

    for i in range(2<<11):
        bit = []
        for j in range(11):
            bit.append(i >> j & 1 == 1)
        bits.append(bit)
        

    def formula(string):
        global index
        index += 1
        if string[index] == "T":
            return True
        elif string[index] == "F":
            return False
        elif string[index] == "-":
            return not formula(string)
        elif string[index] == "(":
            left = formula(string)
            index += 1
            ope = string[index]
            if ope == "-":
                index += 1
            right = formula(string)
            index += 1
            if ope == "+":
                return left or right
            elif ope == "*":
                return left and right
            else:

                return False if left and not right else True
        else:
            return bit[ord(string[index]) - ord("a")]
    
    f = True
    for bit in bits:
        l,r = s.split("=")

        index = -1 
        l_b = formula(l)
        index = -1
        r_b = formula(r)

        if l_b != r_b:
            f = False
    
    if f:
        print("YES")
    else:
        print("NO")

    # l,r = s.split("=")
    # l_b = formula()
