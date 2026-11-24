rule = ["I","V","X","L","C","D","M"]
val = [1,5,10,50,100,500,1000]
while True:
    try:
        nums = input()
        ans = val[rule.index(nums[0])]

        for i in range(1,len(nums)):
            ans += val[rule.index(nums[i])]
            if rule.index(nums[i]) > rule.index(nums[i-1]):
                ans -= (2*val[rule.index(nums[i-1])])

        print(ans)
    except EOFError: break