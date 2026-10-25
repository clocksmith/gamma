class Solution:
    def distributeCandies(self, candies: int, num_people: int) -> list[int]:
        result = [0] * num_people
        remaining = candies
        gift = 1
        person = 0
        while remaining > 0:
            amount = min(gift, remaining)
            result[person] += amount
            remaining -= amount
            gift += 1
            person = (person + 1) % num_people
        return result
