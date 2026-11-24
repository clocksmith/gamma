import sys
N,M=map(int,input().split())

A=[list(input()) for _ in range(N)]
B=[list(input()) for _ in range(M)]
offset=N-M
 
for row_offs in range(offset+1):
  for col_offs in range(offset+1):
    is_match=True
    for row in range(M):
      img_row=A[row+row_offs][col_offs:col_offs+M]
      tmp_row=B[row][:]
      if img_row != tmp_row:
        is_match=False
    if is_match:
      print("Yes")
      sys.exit()
print("No")
