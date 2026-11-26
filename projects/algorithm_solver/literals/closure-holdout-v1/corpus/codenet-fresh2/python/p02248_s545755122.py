def main():
    T, P = input(), input()
    t, p = len(T), len(P)
    if t>=p:
        ans = [str(n) for n, i in enumerate(range(p, t+1)) if T[n:i]==P]
        if ans:
            print("\n".join(ans))

if __name__ == "__main__":
    main()
