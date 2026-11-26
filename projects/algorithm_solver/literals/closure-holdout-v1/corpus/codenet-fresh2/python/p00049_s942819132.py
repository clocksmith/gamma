import sys
blood = {"A": 0, "B": 0, "AB": 0, "O": 0}
for line in sys.stdin:
    if line == "\n":
        break
    no, b = line.rstrip().split(",")
    blood[b] += 1
print(blood["A"])
print(blood["B"])
print(blood["AB"])
print(blood["O"])