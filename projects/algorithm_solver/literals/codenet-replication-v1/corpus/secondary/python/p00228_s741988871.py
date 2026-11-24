nums = ["0111111", "0000110", "1011011", "1001111", "1100110",
        "1101101", "1111101", "0100111", "1111111", "1101111"]

while 1:
    n = int(input())
    if n == -1:
        break

    sig = "0000000"
    for _ in range(n):
        d = int(input())
        num = nums[d]
        out = ""
        for s, n in zip(sig, num):
            if s == n:
                out += "0"
            else:
                out += "1"

        print(out)
        sig = num

