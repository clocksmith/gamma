# Owner-authorized provider retirement during confirmation

The owner explicitly no longer needed the Jupiter 27B Reploid provider and asked
for its memory to be freed. This changes the earlier requirement to keep that
service active. It does not authorize changing model outputs or the frozen shader
criteria.

[The operational receipt](service-retirement-04.json) records the original guard,
new monitor identity, command, timestamps, process absence and available-memory
change. The original read-only monitor was suspended and terminated only after
an independently validated replacement was live; the locked runtime guard path
was atomically linked to its fresh output. This avoided interpreting the owner's
requested shutdown as an experiment failure. No experiment GPU/model process was
stopped; the retired provider's processes exited through its systemd service.

The old provider was idle. The main experiment continued. Memory residency and
any request overlapping service teardown are an environment deviation for timing
interpretation; retain all raw costs and quality outputs. Further parallel model
work needs its own recorded contention interval. The new monitor continues to
require at least 32 GiB available RAM and refuses provider restart.
