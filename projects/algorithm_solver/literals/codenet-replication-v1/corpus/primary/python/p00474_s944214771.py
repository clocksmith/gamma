def orderN(N,L,ices):
    upPeak = L - ices[0]
    downPeak = L - ices[0]
    peaks = []
    for i in range(len(ices)):
        if i < N-1:
            if ices[i] < ices[i+1]:
                peaks.append(downPeak)
                downPeak = L - ices[i+1]
                upPeak += L - ices[i+1]
            elif ices[i] > ices[i+1]:
                peaks.append(upPeak)
                upPeak = L - ices[i+1]
                downPeak += L - ices[i+1]
        elif i == N-1:
            peaks.append(upPeak)
            peaks.append(downPeak)
    print(max(peaks))

N,L = map(int,input().strip().split())
ices = [int(input().strip()) for _ in range(N)]


orderN(N,L,ices)