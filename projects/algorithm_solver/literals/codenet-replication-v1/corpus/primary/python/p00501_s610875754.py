def main():
  n = int(input())
  name = input()
  length = len(name)
  def check(ss):
    ind = 0
    end = len(ss)
    while ind < end:
      while ind < end and ss[ind] != name[0]:
        ind += 1
      
      for i in range(100):
        j1 = ind
        j2 = 0
        while j1 < end and j2 < length and ss[j1] == name[j2]:
          j1 += i
          j2 += 1
        if j2 == length:
          return True
      ind += 1
    return False
  
  print(sum([check(input()) for _ in range(n)]))
main()
