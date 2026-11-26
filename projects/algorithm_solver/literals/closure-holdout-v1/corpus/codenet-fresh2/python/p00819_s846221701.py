n = int(input())
for i in range(n):
    order = str(input())
    mes = str(input())
    l = len(mes)

    for p in reversed(order):
        if p == "J":
            mes = mes[-1] + mes[:-1]

        elif p == "C":
            mes = mes[1:] + mes[0]

        elif p == "E":
            if l % 2 == 0:
                mes = mes[l // 2:] + mes[:l // 2]
            else:
                mes = mes[(l + 1) // 2:] + mes[(l - 1) // 2] + mes[:(l - 1) // 2]

        elif p == "A":
            mes = mes[::-1]

        elif  p == "P":
            mes_li = list(mes)
            for itr, c in enumerate(mes_li):
                if c.isdigit():
                    mes_li[itr] = str((int(c) + 9) % 10)
            mes = "".join(mes_li)

        elif p == "M":
            mes_li = list(mes)
            for itr, c in enumerate(mes_li):
                if c.isdigit():
                    mes_li[itr] = str((int(c) + 1) % 10)
            mes = "".join(mes_li)

    print(mes)
