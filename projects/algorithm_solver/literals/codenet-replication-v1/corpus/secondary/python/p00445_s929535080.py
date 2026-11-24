while True:
   try:
      j = input()
      p=0
      q=0
      for i in range(len(j)-2):
         if j[i:i+3] == 'JOI':
            p += 1
         elif j[i:i+3] == 'IOI':
            q += 1
         else:
            pass
      print(p)
      print(q)
   except EOFError:
      break
