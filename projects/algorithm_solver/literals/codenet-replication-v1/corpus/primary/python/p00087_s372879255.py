while True:
  try:
    ss = input().split()
    stack = []

    for s in ss:
      if s == "+":
        a, b = stack.pop(), stack.pop()
        stack.append(b + a)
      elif s == "-":
        a, b = stack.pop(), stack.pop()
        stack.append(b - a)
      elif s == "*":
        a, b = stack.pop(), stack.pop()
        stack.append(b * a)
      elif s == "/":
        a, b = stack.pop(), stack.pop()
        stack.append(b / a)
      else:
        stack.append(int(s))

    print(stack[0])

  except EOFError:
    break
