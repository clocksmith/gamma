from collections import namedtuple

Data = namedtuple("Data", "name weight limit")


def search(food_list, select_list, total_weight):
    if len(food_list) == 0:
        return select_list

    limit = select_list[len(select_list) - 1].limit

    for lp, food in enumerate(food_list):

        if total_weight <= limit:

            select_list.append(food)
            food_list.remove(food)
            total_weight -= food.weight

            search(food_list, select_list, total_weight)

            if len(food_list) == 0:
                return select_list
            else:
                select_list.pop()
                food_list.insert(lp, food)
                total_weight += food.weight

    return None


while True:
    input_count = int(input())

    if input_count == 0:
        break

    input_data = [input().split(" ") for _ in range(input_count)]
    input_data = [Data(item[0], int(item[1]), int(item[2])) for item in input_data]

    input_data.sort(key=lambda x: (x.weight, x.limit), reverse=True)

    total_weight = sum([item.weight for item in input_data])

    result = search(input_data, [Data("sentinel", 0, 999999)], total_weight)
    del result[0]

    output = [item.name for item in result]
    print("\n".join(output))

