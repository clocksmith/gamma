# Hard32 wave3 original transport comparison

Native execution completed132 calls and3835/3836 checks, with15/16 pairs counted passing by the original comparator. The sole failure was Python2569 case120: trusted Python harness serialized its exact large integers using the existing canonical integer tags, but the host comparator decoded those tags only for JS. Native exit was0 with no resource or output failure. This is a comparator integration defect, not established candidate semantic error.

The original freeze55570, source code, raw observations and failed verdict remain unchanged. The separate `public-domain-qualification-hard32-wave3-transport-v2` successor decodes existing canonical tags for both languages at2569 only, preserving exact outer result types, integer values, cases, sources, runtime, limits and effects. Its independent review/replay is separate; no retroactive original pass is claimed.

Full8-ID/16-pair denominator remains visible. 2573 official matrix maximum1000 is validated but not fully executable under the unchanged packet/output budget; finite authored matrices reach100. Finite tests and algorithm review do not prove all official inputs.
