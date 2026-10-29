"""Native official class; original development candidate, qualification pending."""
class ParkingSystem:
    def __init__(self, big, medium, small):
        self.remaining = [big, medium, small]

    def addCar(self, carType):
        index = carType - 1
        if self.remaining[index] == 0:
            return False
        self.remaining[index] -= 1
        return True
