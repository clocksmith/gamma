import decimal
x = int(input())


int_val = decimal.Decimal(x / 3)
answer = int_val * int_val * int_val

print(answer)
