dic = {
  "yotta":24,
  "zetta":21,
  "exa"  :18,
  "peta" :15,
  "tera" :12,
  "giga" :9,
  "mega" :6,
  "kilo" :3,
  "hecto":2,
  "deca" :1,
  "deci" :-1,
  "centi":-2,
  "milli":-3,
  "micro":-6,
  "nano" :-9,
  "pico" :-12,
  "femto":-15,
  "ato"  :-18,
  "zepto":-21,
  "yocto":-24
}

n = int(input())
for _ in range(n):
  lst = input().split()
  if len(lst) == 2:
    x, z = lst
    sisuu = 0
  else:
    x, y, z = lst
    sisuu = dic[y]

  if "." not in x:
    x = x + "."
  ind = x.index(".")
  x = x[:ind] + x[ind+1:]
  
  while x[0] == "0":
    x = x[1:]
    ind -= 1
  if len(x) != 1:
    x = x[0] + "." + x[1:]

  sisuu += (ind - 1)

  print(x , "*", "10^"+str(sisuu), z)
