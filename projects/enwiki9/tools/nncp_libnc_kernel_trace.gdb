set pagination off
set debuginfod enabled off
break main
run 2048 1024 32 4
set $base=(char*)mat_mul-0x47310
set $firstout=0
break *($base+0x7ad8)
commands 2
silent
if $firstout == 0
  set $firstout=$rdi
end
if $rdi == $firstout
  printf "thread=%d inner=%ld alpha=%f out=%p weight=%p src=%p\n", $_thread, $rbx, $xmm0.v4_float[0], $rdi, $rdx, $r8
end
continue
end
continue
