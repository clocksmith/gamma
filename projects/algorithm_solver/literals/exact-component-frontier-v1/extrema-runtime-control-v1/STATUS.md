# Superseded unrun runtime-control preparation

Freeze c10ab921620448ac52b7925205ff71a7d641a65a7e8e4e052a48ce57bc699233 was independently rejected BEFORE native execution because fixture/harness bytes were reread after their initial code pin check. Keep this code as counterevidence. The linked extrema-runtime-control-v2 snapshots, hashes and reuses the actual buffers; only v2 was executed. V1 host tests were one positive/four negative, five total.
