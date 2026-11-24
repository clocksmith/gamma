a, b = map(str, input().split())

c = int(a+b)

import math
if (math.sqrt(c)).is_integer():
    print ('Yes')
else:
    print ('No')