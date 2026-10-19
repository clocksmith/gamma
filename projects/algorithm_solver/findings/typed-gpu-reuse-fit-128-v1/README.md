# Rejected combined-process GPU reuse attempt

Both CPU and GPU capture phases completed using original assets, but the combined
CPU-then-GPU process failed its conservative6 GiB RSS-plus-GPU-reservation check.
No public decisions or independent scoring ran. The original captures, manifest,
resource failure and partial CPU setup are retained; this attempt is not a
qualified latency result. Peak sampled process-tree RSS was5.381 GB.

The CPU arm exactly reproduced all ten historical raw predictions. Its complete
captures were retained for the separately frozen
[v2 follow-up](../typed-gpu-reuse-fit-128-v2/README.md), which uses a fresh GPU-only
process and the same model/inputs/search limits. It never treats this failed run
as an accepted resource result. The endpoint failure occurred after GPU capture;
the code had not yet published GPU allocation figures, so no exact missing figure
is invented. Raw records stay in `runs/typed-gpu-reuse-fit-128-v1`.

The shared Monitor's failure receipt labels threads 4; actual Torch/OMP/BLAS were 2,
CPUQuota 200% and affinity [0,1]. This reporting defect does not mean four threads
were authorized for this process. The v2 summary records two explicitly.
