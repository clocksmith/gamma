# Atomic admission preserves the literal result, no ready constructor arm

All2,000views independently decode and reuse exact D11 qualification. L1, LB
and TB each use8,324validation actions; T1 uses8,334. **No ready structured
candidate.** TB accepts one literal bundle, exactly like LB, and accepts no
constructor bundle. Its improvement over T1 therefore does not establish an
atomic-constructor benefit. All searches stop at their300-second boundaries;
this is bounded search evidence, not impossibility of the mechanism.

[Freeze](FREEZE.md), [design](DRAFT.md), [review](REVIEW.md),
[accepted move counts](ADMISSION-COUNTS.md), [complete metadata](evidence/results.json).

The tables below label median/p90 in **actions**, including Finish; subtract
one for selection quantiles. L1/LB/TB median61.5,p90154,p95197 selections;
T1 p95190. TB character share49.8176% exceeds D11's49.0838% and T1's49.7207%;
raw package16,242bytes exceeds LB's14,962. Typed decoder cost252,171bytes is
fully charged, giving TB268,413bytes including decoder sources. T1's one
template-used validation program retains its seven-action local saving versus
literal, with full conditional overhead visible. M1 and the flat default stay
unchanged.

## Detailed matched results

Separate 2c evidence; no flat M1 promotion.

| Arm | Validation actions | Median | p90 | C/N | Package bytes | Used programs | Distinct P/I entries used |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| L1 | 8324 | 62.5 | 155 | 0.498176 | 14962 | 0 | 0/0 |
| T1 | 8334 | 62.5 | 155 | 0.497207 | 16358 | 1 | 0/1 |
| LB | 8324 | 62.5 | 155 | 0.498176 | 14962 | 0 | 0/0 |
| TB | 8324 | 62.5 | 155 | 0.498176 | 16242 | 0 | 0/0 |
| D11 | 8341 | 63.0 | 155 | 0.490838 | 14966 | 0 | 0/0 |

TB passes the full predeclared structured rule: False.
All predicate failures, per-program coverage, pairwise changes, decoder-inclusive bytes and costs are in [metadata](evidence/results.json).

Search deadlines are checked between exact trials; the hard supervisor covers the whole job. Actual search time and any overrun follow.

| Arm | Trials | Search seconds | Budget overrun seconds | Longest recorded trial seconds |
| --- | ---: | ---: | ---: | ---: |
| L1 | 2654 | 300.086844 | 0.086850 | 0.503063 |
| T1 | 2581 | 300.235249 | 0.235254 | 0.491366 |
| LB | 1970 | 300.063562 | 0.063569 | 0.510132 |
| TB | 1761 | 300.016964 | 0.016970 | 0.549241 |

| Prediction | Expected | Observed | Correct |
| --- | --- | --- | --- |
| S1_all_views_decode_and_qualify | True | True | True |
| S2_TB_fewer_actions_than_T1 | True | True | True |
| S3_TB_fewer_actions_than_LB | True | False | False |
| S4_TB_not_ready | True | True | True |

Conditional subsets are descriptive and may overlap. Their exact IDs and paired costs are in [metadata](evidence/results.json). Each package below retains the entire global dictionary; subsets receive no dictionary discount and must not be summed.

| Selection arm | Subset | Count | Actions | N | C | C/N | Full dictionary + subset packets |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| L1 | common_pool_eligible | 99 | 8316 | 8217 | 4093 | 0.498114 | 14914 |
| L1 | arm_pool_eligible | 0 | 0 | 0 | 0 | null | 2638 |
| L1 | P_used | 0 | 0 | 0 | 0 | null | 2638 |
| L1 | I_used | 0 | 0 | 0 | 0 | null | 2638 |
| L1 | either_used | 0 | 0 | 0 | 0 | null | 2638 |
| L1 | both_used | 0 | 0 | 0 | 0 | null | 2638 |
| T1 | common_pool_eligible | 99 | 8326 | 8227 | 4090 | 0.497144 | 16310 |
| T1 | arm_pool_eligible | 99 | 8326 | 8227 | 4090 | 0.497144 | 16310 |
| T1 | P_used | 0 | 0 | 0 | 0 | null | 4024 |
| T1 | I_used | 1 | 191 | 190 | 77 | 0.405263 | 4255 |
| T1 | either_used | 1 | 191 | 190 | 77 | 0.405263 | 4255 |
| T1 | both_used | 0 | 0 | 0 | 0 | null | 4024 |
| LB | common_pool_eligible | 99 | 8316 | 8217 | 4093 | 0.498114 | 14914 |
| LB | arm_pool_eligible | 0 | 0 | 0 | 0 | null | 2638 |
| LB | P_used | 0 | 0 | 0 | 0 | null | 2638 |
| LB | I_used | 0 | 0 | 0 | 0 | null | 2638 |
| LB | either_used | 0 | 0 | 0 | 0 | null | 2638 |
| LB | both_used | 0 | 0 | 0 | 0 | null | 2638 |
| TB | common_pool_eligible | 99 | 8316 | 8217 | 4093 | 0.498114 | 16194 |
| TB | arm_pool_eligible | 99 | 8316 | 8217 | 4093 | 0.498114 | 16194 |
| TB | P_used | 0 | 0 | 0 | 0 | null | 3918 |
| TB | I_used | 0 | 0 | 0 | 0 | null | 3918 |
| TB | either_used | 0 | 0 | 0 | 0 | null | 3918 |
| TB | both_used | 0 | 0 | 0 | 0 | null | 3918 |
| D11 | common_pool_eligible | 99 | 8333 | 8234 | 4041 | 0.490770 | 14918 |
| D11 | arm_pool_eligible | 0 | 0 | 0 | 0 | null | 2625 |
| D11 | P_used | 0 | 0 | 0 | 0 | null | 2625 |
| D11 | I_used | 0 | 0 | 0 | 0 | null | 2625 |
| D11 | either_used | 0 | 0 | 0 | 0 | null | 2625 |
| D11 | both_used | 0 | 0 | 0 | 0 | null | 2625 |
