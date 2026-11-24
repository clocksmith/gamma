input_line = input()
stack = []
area = 0
pond_area = 0
pond_areas = []

for i,s in enumerate(input_line):
    if s == '\\':
        stack.append(i)
        if pond_area: 
            pond_areas.append((l, pond_area))
            pond_area = 0
    elif stack and s == '/':
        l = stack.pop()
        area += i - l
        while True:
            if not pond_areas or pond_areas[-1][0] < l: break
            else: 
                pond_area += pond_areas.pop()[1]
        pond_area += i-l

if pond_area > 0: pond_areas.append((l, pond_area))

print(area)
print( " ".join([str(len(pond_areas))] + [str(a[1]) for a in pond_areas]) )
