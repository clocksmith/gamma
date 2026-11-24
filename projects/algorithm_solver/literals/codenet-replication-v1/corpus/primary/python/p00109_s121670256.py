import re
class o:
    def __str__(self):
        return str(self.x)
    def __init__(self,value):
        self.x=value
    def __add__(self,value):
        return o(self.x+value.x)
    def __sub__(self,value):
        return o(self.x-value.x)
    def __mul__(self,value):
        return o(self.x*value.x)
    def __truediv__(self,value):
        return o(int(self.x/value.x))
    
n=int(input())
for i in range(n):
    s=input()[:-1]
    s=re.sub(r'(\d+)',r'o(\1)',s)
    print(eval(s))

