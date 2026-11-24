#!/usr/bin/env python
# coding: utf-8

# In[4]:


from collections import Counter


# In[8]:


N = int(input())
A = list(map(int, input().split()))


# In[9]:


s = [0]
for i in range(N):
    s += [s[-1]+A[i]]
c = Counter(s)
ans = 0
for v in c.values():
    ans += v*(v-1)//2
print(ans)


# In[ ]:




