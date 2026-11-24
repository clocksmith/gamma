items = {}
recipes = {}


def reset():
    items.clear()
    recipes.clear()


def algorithm():
    while True:
        reset()

        for _ in range(int(input())):
            item, price = input().split()
            items[item] = int(price)

        if len(items) == 0:
            break

        for _ in range(int(input())):
            recipe = input().split()
            recipes[recipe[0]] = recipe[2:]

        for _ in range(len(recipes)):
            for k, v in recipes.items():
                total = 0
                for i in range(len(v)):
                    total += items[v[i]]
                items[k] = items[k] if items[k] < total else total

        print(items[input()])


def main():
    algorithm()


if __name__ == '__main__':
    main()