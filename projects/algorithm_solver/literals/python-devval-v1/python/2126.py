def solve(mass, asteroids):
    for asteroid in sorted(asteroids):
        if asteroid > mass:
            return False
        mass += asteroid
    return True
