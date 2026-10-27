# Original candidate implementation. Contract: https://leetcode.com/problems/decremental-string-concatenation/
def solve(words):
    first=words[0];dp={(first[0],first[-1]):len(first)}
    for word in words[1:]:
        new={}
        for (a,b),length in dp.items():
            key=(a,word[-1]);cost=length+len(word)-(b==word[0]);new[key]=min(new.get(key,float('inf')),cost)
            key=(word[0],b);cost=length+len(word)-(word[-1]==a);new[key]=min(new.get(key,float('inf')),cost)
        dp=new
    return min(dp.values())
