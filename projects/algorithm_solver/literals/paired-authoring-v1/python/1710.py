class Solution:
    def maximumUnits(self, boxTypes: list[list[int]], truckSize: int) -> int:
        ordered = sorted(boxTypes, key=lambda item: -item[1])
        remaining = truckSize
        units = 0
        for boxes, per_box in ordered:
            taken = min(boxes, remaining)
            units += taken * per_box
            remaining -= taken
            if remaining == 0:
                break
        return units
