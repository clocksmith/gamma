# Gamma gap campaign — chunk 11 source delivery

**Partial assignment delivery: 139 problem pairs, 278 source files; 41 assigned problems remain blocked.**

## Apply

From the Gamma repository root:

```sh
git apply /path/to/gamma-gap-11-js-python.patch
```

This command was not executed here. The patch adds files only; it does not overwrite existing sources.

Patch SHA-256: `e40d8e385f1308c991d1eef1843d4b2af00cd779cd1f888cfc34d20d563ccfcc`
Patch bytes: 390,531.

## Assignment identity

The earlier plan specified 12 capacities, not exact memberships. This delivery explicitly assigns all chunks by ascending numeric problem ID among the audit's 2,163 not-located rows, using capacities 181, 181, 181, then nine groups of 180. Chunk 11 is positions 1,804–1,983 (inclusive), spanning IDs 3654–3889 with gaps. This is a new deterministic allocation, not a recovered difficulty-balanced allocation.

Input inventory SHA-256: `3c3bbd936a57fb1fb238ac71b4a4e7910c50dbd58a4eae2f6a04f74673188cfd`.
The companion JSON retains all 12 ID lists, this chunk's complete dispositions, source paths, and byte hashes so other chunks can use exactly the same partition. It is not included in the source patch.

The audit's 128 already-written pairs are excluded through its not-located-row filter. IDs did not move or get replaced when their contracts proved unavailable.

## Repository and destination

Read-only main snapshot: `3cacb836c561e908a53b5550b8d12a582f686fb0`.
The published authored tree was `df956b4b14289284fc802be68ff97a77349709fa`, unchanged from the source audit. This establishes no newly published files in that tree, not absence from every private or experimental store.

New source destination:

```text
projects/algorithm_solver/catalogue/quarantined/gamma-gap-11/javascript/<id>.js
projects/algorithm_solver/catalogue/quarantined/gamma-gap-11/python/<id>.py
```

The quarantine location is intentional: per-ID development/evaluation classification is not fully resolved, and no training, index, serving, or qualification registry is changed. A directory name alone does not enforce secrecy or isolation; the coordinator must prevent unapproved ingestion.

## Source conventions and limitations

Python uses four-space indentation and explicit imports; JavaScript uses two-space indentation, explicit helpers and guarded CommonJS exports. Ordinary functions expose ordered-positional `solve(...)` plus forwarding interfaces. Stateful problems include their native class and a `solve(operations, arguments)` replay interface. Both languages follow the same intended algorithm. Arithmetic, ordering, and mutation behavior follow each inspected problem rather than a blanket immutability rule.

**These are authored candidates, not tested implementations.** No solution was executed, imported, syntax-checked, or tested. No Git apply check, commit, push, or qualification run occurred. Packaging only read literal source bytes and metadata, counted files, and computed hashes.

Forwarding method names have not been independently matched to every upstream judge stub. Canonical argument order and intended interface are retained per source and in the companion JSON; the coordinator must bind them to the actual consuming contract. Statement URLs are provenance, not frozen statement snapshots or qualification evidence.

Public descriptions were used to author the code. No source bodies from third-party solution collections, protected cases, test outputs, or private reference implementations are included.

## Complete delivery accounting

| Disposition | Problems | Source files |
|---|---:|---:|
| Candidate pair delivered | 139 | 278 |
| Specification unavailable or Premium-locked | 33 | 0 |
| SQL/Pandas problem without a defined Gamma dual-language interface | 8 | 0 |
| Total assignment | 180 | 278 |

### Blocked assignments — retained, not substituted

| ID | Title | Blocker |
|---:|---|---|
| 3656 | Determine if a Simple Graph Exists | Complete accessible specification not established |
| 3657 | Find Loyal Customers | SQL/Pandas interface not defined |
| 3662 | Filter Characters by Frequency | Complete accessible specification not established |
| 3667 | Sort Array By Absolute Value | Complete accessible specification not established |
| 3672 | Sum of Weighted Modes in Subarrays | Complete accessible specification not established |
| 3673 | Find Zombie Sessions | SQL/Pandas interface not defined |
| 3682 | Minimum Index Sum of Common Elements | Complete accessible specification not established |
| 3687 | Library Late Fee Calculator | Complete accessible specification not established |
| 3696 | Maximum Distance Between Unequal Words in Array I | Complete accessible specification not established |
| 3705 | Find Golden Hour Customers | SQL/Pandas interface not defined |
| 3706 | Maximum Distance Between Unequal Words in Array II | Complete accessible specification not established |
| 3711 | Maximum Transactions Without Negative Balance | Complete accessible specification not established |
| 3716 | Find Churn Risk Customers | SQL/Pandas interface not defined |
| 3717 | Minimum Operations to Make the Array Beautiful | Complete accessible specification not established |
| 3730 | Maximum Calories Burnt from Jumps | Complete accessible specification not established |
| 3735 | Lexicographically Smallest String After Reverse II | Complete accessible specification not established |
| 3744 | Find Kth Character in Expanded String | Complete accessible specification not established |
| 3749 | Evaluate Valid Expressions | Complete accessible specification not established |
| 3758 | Convert Number Words to Digits | Complete accessible specification not established |
| 3763 | Maximum Total Sum with Threshold Constraints | Complete accessible specification not established |
| 3764 | Most Common Course Pairs | SQL/Pandas interface not defined |
| 3773 | Maximum Number of Equal Length Runs | Complete accessible specification not established |
| 3778 | Minimum Distance Excluding One Maximum Weighted Edge | Complete accessible specification not established |
| 3787 | Find Diameter Endpoints of a Tree | Complete accessible specification not established |
| 3792 | Sum of Increasing Product Blocks | Complete accessible specification not established |
| 3793 | Find Users with High Token Usage | SQL/Pandas interface not defined |
| 3802 | Number of Ways to Paint Sheets | Complete accessible specification not established |
| 3807 | Minimum Cost to Repair Edges to Traverse a Graph | Complete accessible specification not established |
| 3808 | Find Emotionally Consistent Users | SQL/Pandas interface not defined |
| 3817 | Good Indices in a Digit String | Complete accessible specification not established |
| 3822 | Design Order Management System | Complete accessible specification not established |
| 3831 | Median of a Binary Search Tree Level | Complete accessible specification not established |
| 3832 | Find Users with Persistent Behavior Patterns | SQL/Pandas interface not defined |
| 3837 | Delayed Count of Equal Elements | Complete accessible specification not established |
| 3846 | Total Distance to Type a String Using One Finger | Complete accessible specification not established |
| 3851 | Maximum Requests Without Violating the Limit | Complete accessible specification not established |
| 3860 | Unique Email Groups | Complete accessible specification not established |
| 3865 | Reverse K Subarrays | Complete accessible specification not established |
| 3874 | Valid Subarrays With Exactly One Peak | Complete accessible specification not established |
| 3879 | Maximum Distinct Path Sum in a Binary Tree | Complete accessible specification not established |
| 3888 | Minimum Operations to Make All Grid Elements Equal | Complete accessible specification not established |

A specification blocker is not necessarily a claim that the problem is Premium-only. Some page fetches were unavailable. No subscription restriction was bypassed, no statement inferred from the title, and no placeholder implementation was emitted.

### Delivered candidate pairs

| ID | Title | Canonical parameters / adapter | Public specification |
|---:|---|---|---|
| 3654 | Minimum Sum After Divisible Sum Deletions | `solve(nums, k)` | https://leetcode.com/problems/minimum-sum-after-divisible-sum-deletions/description/ |
| 3655 | XOR After Range Multiplication Queries II | `solve(nums, queries)` | https://leetcode.com/problems/xor-after-range-multiplication-queries-ii/description/ |
| 3659 | Partition Array Into K-Distinct Groups | `solve(nums, k)` | https://leetcode.com/problems/partition-array-into-k-distinct-groups/description/ |
| 3660 | Jump Game IX | `solve(nums)` | https://leetcode.com/problems/jump-game-ix/description/ |
| 3664 | Two-Letter Card Game | `solve(cards, x)` | https://leetcode.com/problems/two-letter-card-game/description/ |
| 3665 | Twisted Mirror Path Count | `solve(grid)` | https://leetcode.com/problems/twisted-mirror-path-count/description/ |
| 3669 | Balanced K-Factor Decomposition | `solve(n, k)` | https://leetcode.com/problems/balanced-k-factor-decomposition/description/ |
| 3670 | Maximum Product of Two Integers With No Common Bits | `solve(nums)` | https://leetcode.com/problems/maximum-product-of-two-integers-with-no-common-bits/description/ |
| 3671 | Sum of Beautiful Subsequences | `solve(nums)` | https://leetcode.com/problems/sum-of-beautiful-subsequences/description/ |
| 3675 | Minimum Operations to Transform String | `solve(s)` | https://leetcode.com/problems/minimum-operations-to-transform-string/description/ |
| 3676 | Count Bowl Subarrays | `solve(nums)` | https://leetcode.com/problems/count-bowl-subarrays/description/ |
| 3679 | Minimum Discards to Balance Inventory | `solve(arrivals, w, m)` | https://leetcode.com/problems/minimum-discards-to-balance-inventory/description/ |
| 3680 | Generate Schedule | `solve(n)` | https://leetcode.com/problems/generate-schedule/description/ |
| 3681 | Maximum XOR of Subsequences | `solve(nums)` | https://leetcode.com/problems/maximum-xor-of-subsequences/description/ |
| 3685 | Subsequence Sum After Capping Elements | `solve(nums, k)` | https://leetcode.com/problems/subsequence-sum-after-capping-elements/description/ |
| 3686 | Number of Stable Subsequences | `solve(nums)` | https://leetcode.com/problems/number-of-stable-subsequences/description/ |
| 3689 | Maximum Total Subarray Value I | `solve(nums, k)` | https://leetcode.com/problems/maximum-total-subarray-value-i/description/ |
| 3690 | Split and Merge Array Transformation | `solve(nums1, nums2)` | https://leetcode.com/problems/split-and-merge-array-transformation/description/ |
| 3693 | Climbing Stairs II | `solve(n, costs)` | https://leetcode.com/problems/climbing-stairs-ii/description/ |
| 3694 | Distinct Points Reachable After Substring Removal | `solve(s, k)` | https://leetcode.com/problems/distinct-points-reachable-after-substring-removal/description/ |
| 3695 | Maximize Alternating Sum Using Swaps | `solve(nums, swaps)` | https://leetcode.com/problems/maximize-alternating-sum-using-swaps/description/ |
| 3698 | Split Array With Minimum Difference | `solve(nums)` | https://leetcode.com/problems/split-array-with-minimum-difference/description/ |
| 3702 | Longest Subsequence With Non-Zero Bitwise XOR | `solve(nums)` | https://leetcode.com/problems/longest-subsequence-with-non-zero-bitwise-xor/description/ |
| 3703 | Remove K-Balanced Substrings | `solve(s, k)` | https://leetcode.com/problems/remove-k-balanced-substrings/description/ |
| 3708 | Longest Fibonacci Subarray | `solve(nums)` | https://leetcode.com/problems/longest-fibonacci-subarray/description/ |
| 3709 | Design Exam Scores Tracker | `native class and solve operation replay` | https://leetcode.com/problems/design-exam-scores-tracker/description/ |
| 3710 | Maximum Partition Factor | `solve(points)` | https://leetcode.com/problems/maximum-partition-factor/description/ |
| 3713 | Longest Balanced Substring I | `solve(s)` | https://leetcode.com/problems/longest-balanced-substring-i/description/ |
| 3714 | Longest Balanced Substring II | `solve(s)` | https://leetcode.com/problems/longest-balanced-substring-ii/description/ |
| 3715 | Sum of Perfect Square Ancestors | `solve(n, edges, nums)` | https://leetcode.com/problems/sum-of-perfect-square-ancestors/description/ |
| 3719 | Longest Balanced Subarray I | `solve(nums)` | https://leetcode.com/problems/longest-balanced-subarray-i/description/ |
| 3720 | Lexicographically Smallest Permutation Greater Than Target | `solve(s, target)` | https://leetcode.com/problems/lexicographically-smallest-permutation-greater-than-target/description/ |
| 3722 | Lexicographically Smallest String After Reverse | `solve(s)` | https://leetcode.com/problems/lexicographically-smallest-string-after-reverse/description/ |
| 3723 | Maximize Sum of Squares of Digits | `solve(num, sum)` | https://leetcode.com/problems/maximize-sum-of-squares-of-digits/description/ |
| 3724 | Minimum Operations to Transform Array | `solve(nums1, nums2)` | https://leetcode.com/problems/minimum-operations-to-transform-array/description/ |
| 3725 | Count Ways to Choose Coprime Integers from Rows | `solve(mat)` | https://leetcode.com/problems/count-ways-to-choose-coprime-integers-from-rows/description/ |
| 3727 | Maximum Alternating Sum of Squares | `solve(nums)` | https://leetcode.com/problems/maximum-alternating-sum-of-squares/description/ |
| 3728 | Stable Subarrays With Equal Boundary and Interior Sum | `solve(capacity)` | https://leetcode.com/problems/stable-subarrays-with-equal-boundary-and-interior-sum/description/ |
| 3732 | Maximum Product of Three Elements After One Replacement | `solve(nums)` | https://leetcode.com/problems/maximum-product-of-three-elements-after-one-replacement/description/ |
| 3733 | Minimum Time to Complete All Deliveries | `solve(d, r)` | https://leetcode.com/problems/minimum-time-to-complete-all-deliveries/description/ |
| 3737 | Count Subarrays With Majority Element I | `solve(nums, target)` | https://leetcode.com/problems/count-subarrays-with-majority-element-i/description/ |
| 3738 | Longest Non-Decreasing Subarray After Replacing at Most One Element | `solve(nums)` | https://leetcode.com/problems/longest-non-decreasing-subarray-after-replacing-at-most-one-element/description/ |
| 3741 | Minimum Distance Between Three Equal Elements II | `solve(nums)` | https://leetcode.com/problems/minimum-distance-between-three-equal-elements-ii/description/ |
| 3742 | Maximum Path Score in a Grid | `solve(grid, k)` | https://leetcode.com/problems/maximum-path-score-in-a-grid/description/ |
| 3743 | Maximize Cyclic Partition Score | `solve(nums, k)` | https://leetcode.com/problems/maximize-cyclic-partition-score/description/ |
| 3746 | Minimum String Length After Balanced Removals | `solve(s)` | https://leetcode.com/problems/minimum-string-length-after-balanced-removals/description/ |
| 3747 | Count Distinct Integers After Removing Zeros | `solve(n)` | https://leetcode.com/problems/count-distinct-integers-after-removing-zeros/description/ |
| 3751 | Total Waviness of Numbers in Range I | `solve(num1, num2)` | https://leetcode.com/problems/total-waviness-of-numbers-in-range-i/description/ |
| 3752 | Lexicographically Smallest Negated Permutation that Sums to Target | `solve(n, target)` | https://leetcode.com/problems/lexicographically-smallest-negated-permutation-that-sums-to-target/description/ |
| 3755 | Find Maximum Balanced XOR Subarray Length | `solve(nums)` | https://leetcode.com/problems/find-maximum-balanced-xor-subarray-length/description/ |
| 3756 | Concatenate Non-Zero Digits and Multiply by Sum II | `solve(s, queries)` | https://leetcode.com/problems/concatenate-non-zero-digits-and-multiply-by-sum-ii/description/ |
| 3757 | Number of Effective Subsequences | `solve(nums)` | https://leetcode.com/problems/number-of-effective-subsequences/description/ |
| 3759 | Count Elements With at Least K Greater Values | `solve(nums, k)` | https://leetcode.com/problems/count-elements-with-at-least-k-greater-values/description/ |
| 3760 | Maximum Substrings With Distinct Start | `solve(s)` | https://leetcode.com/problems/maximum-substrings-with-distinct-start/description/ |
| 3761 | Minimum Absolute Distance Between Mirror Pairs | `solve(nums)` | https://leetcode.com/problems/minimum-absolute-distance-between-mirror-pairs/description/ |
| 3762 | Minimum Operations to Equalize Subarrays | `solve(nums, k, queries)` | https://leetcode.com/problems/minimum-operations-to-equalize-subarrays/description/ |
| 3765 | Complete Prime Number | `solve(num)` | https://leetcode.com/problems/complete-prime-number/description/ |
| 3766 | Minimum Operations to Make Binary Palindrome | `solve(nums)` | https://leetcode.com/problems/minimum-operations-to-make-binary-palindrome/description/ |
| 3767 | Maximize Points After Choosing K Tasks | `solve(technique1, technique2, k)` | https://leetcode.com/problems/maximize-points-after-choosing-k-tasks/description/ |
| 3768 | Minimum Inversion Count in Subarrays of Fixed Length | `solve(nums, k)` | https://leetcode.com/problems/minimum-inversion-count-in-subarrays-of-fixed-length/description/ |
| 3770 | Largest Prime from Consecutive Prime Sum | `solve(n)` | https://leetcode.com/problems/largest-prime-from-consecutive-prime-sum/description/ |
| 3771 | Total Score of Dungeon Runs | `solve(hp, damage, requirement)` | https://leetcode.com/problems/total-score-of-dungeon-runs/description/ |
| 3772 | Maximum Subgraph Score in a Tree | `solve(n, edges, good)` | https://leetcode.com/problems/maximum-subgraph-score-in-a-tree/description/ |
| 3775 | Reverse Words With Same Vowel Count | `solve(s)` | https://leetcode.com/problems/reverse-words-with-same-vowel-count/description/ |
| 3776 | Minimum Moves to Balance Circular Array | `solve(balance)` | https://leetcode.com/problems/minimum-moves-to-balance-circular-array/description/ |
| 3779 | Minimum Number of Operations to Have Distinct Elements | `solve(nums)` | https://leetcode.com/problems/minimum-number-of-operations-to-have-distinct-elements/description/ |
| 3780 | Maximum Sum of Three Numbers Divisible by Three | `solve(nums)` | https://leetcode.com/problems/maximum-sum-of-three-numbers-divisible-by-three/description/ |
| 3781 | Maximum Score After Binary Swaps | `solve(nums, s)` | https://leetcode.com/problems/maximum-score-after-binary-swaps/description/ |
| 3782 | Last Remaining Integer After Alternating Deletion Operations | `solve(n)` | https://leetcode.com/problems/last-remaining-integer-after-alternating-deletion-operations/description/ |
| 3784 | Minimum Deletion Cost to Make All Characters Equal | `solve(s, cost)` | https://leetcode.com/problems/minimum-deletion-cost-to-make-all-characters-equal/description/ |
| 3785 | Minimum Swaps to Avoid Forbidden Values | `solve(nums, forbidden)` | https://leetcode.com/problems/minimum-swaps-to-avoid-forbidden-values/description/ |
| 3786 | Total Sum of Interaction Cost in Tree Groups | `solve(n, edges, group)` | https://leetcode.com/problems/total-sum-of-interaction-cost-in-tree-groups/description/ |
| 3788 | Maximum Score of a Split | `solve(nums)` | https://leetcode.com/problems/maximum-score-of-a-split/description/ |
| 3789 | Minimum Cost to Acquire Required Items | `solve(cost1, cost2, costBoth, need1, need2)` | https://leetcode.com/problems/minimum-cost-to-acquire-required-items/description/ |
| 3790 | Smallest All-Ones Multiple | `solve(k)` | https://leetcode.com/problems/smallest-all-ones-multiple/description/ |
| 3795 | Minimum Subarray Length With Distinct Sum At Least K | `solve(nums, k)` | https://leetcode.com/problems/minimum-subarray-length-with-distinct-sum-at-least-k/description/ |
| 3796 | Find Maximum Value in a Constrained Sequence | `solve(n, restrictions, diff)` | https://leetcode.com/problems/find-maximum-value-in-a-constrained-sequence/description/ |
| 3797 | Count Routes to Climb a Rectangular Grid | `solve(grid, d)` | https://leetcode.com/problems/count-routes-to-climb-a-rectangular-grid/description/ |
| 3799 | Word Squares II | `solve(words)` | https://leetcode.com/problems/word-squares-ii/description/ |
| 3800 | Minimum Cost to Make Two Binary Strings Equal | `solve(s, t, flipCost, swapCost, crossCost)` | https://leetcode.com/problems/minimum-cost-to-make-two-binary-strings-equal/description/ |
| 3801 | Minimum Cost to Merge Sorted Lists | `solve(lists)` | https://leetcode.com/problems/minimum-cost-to-merge-sorted-lists/description/ |
| 3804 | Number of Centered Subarrays | `solve(nums)` | https://leetcode.com/problems/number-of-centered-subarrays/description/ |
| 3805 | Count Caesar Cipher Pairs | `solve(words)` | https://leetcode.com/problems/count-caesar-cipher-pairs/description/ |
| 3806 | Maximum Bitwise AND After Increment Operations | `solve(nums, k, m)` | https://leetcode.com/problems/maximum-bitwise-and-after-increment-operations/description/ |
| 3809 | Best Reachable Tower | `solve(towers, center, radius)` | https://leetcode.com/problems/best-reachable-tower/description/ |
| 3810 | Minimum Operations to Reach Target Array | `solve(nums, target)` | https://leetcode.com/problems/minimum-operations-to-reach-target-array/description/ |
| 3811 | Number of Alternating XOR Partitions | `solve(nums, target1, target2)` | https://leetcode.com/problems/number-of-alternating-xor-partitions/description/ |
| 3812 | Minimum Edge Toggles on a Tree | `solve(n, edges, start, target)` | https://leetcode.com/problems/minimum-edge-toggles-on-a-tree/description/ |
| 3814 | Maximum Capacity Within Budget | `solve(costs, capacity, budget)` | https://leetcode.com/problems/maximum-capacity-within-budget/description/ |
| 3815 | Design Auction System | `native class and solve operation replay` | https://leetcode.com/problems/design-auction-system/description/ |
| 3816 | Lexicographically Smallest String After Deleting Duplicate Characters | `solve(s)` | https://leetcode.com/problems/lexicographically-smallest-string-after-deleting-duplicate-characters/description/ |
| 3818 | Minimum Prefix Removal to Make Array Strictly Increasing | `solve(nums)` | https://leetcode.com/problems/minimum-prefix-removal-to-make-array-strictly-increasing/description/ |
| 3819 | Rotate Non Negative Elements | `solve(nums, k)` | https://leetcode.com/problems/rotate-non-negative-elements/description/ |
| 3820 | Pythagorean Distance Nodes in a Tree | `solve(n, edges, x, y, z)` | https://leetcode.com/problems/pythagorean-distance-nodes-in-a-tree/description/ |
| 3821 | Find Nth Smallest Integer With K One Bits | `solve(n, k)` | https://leetcode.com/problems/find-nth-smallest-integer-with-k-one-bits/description/ |
| 3824 | Minimum K to Reduce Array Within Limit | `solve(nums)` | https://leetcode.com/problems/minimum-k-to-reduce-array-within-limit/description/ |
| 3825 | Longest Strictly Increasing Subsequence With Non-Zero Bitwise AND | `solve(nums)` | https://leetcode.com/problems/longest-strictly-increasing-subsequence-with-non-zero-bitwise-and/description/ |
| 3826 | Minimum Partition Score | `solve(nums, k)` | https://leetcode.com/problems/minimum-partition-score/description/ |
| 3828 | Final Element After Subarray Deletions | `solve(nums)` | https://leetcode.com/problems/final-element-after-subarray-deletions/description/ |
| 3829 | Design Ride Sharing System | `native class and solve operation replay` | https://leetcode.com/problems/design-ride-sharing-system/description/ |
| 3830 | Longest Alternating Subarray After Removing At Most One Element | `solve(nums)` | https://leetcode.com/problems/longest-alternating-subarray-after-removing-at-most-one-element/description/ |
| 3834 | Merge Adjacent Equal Elements | `solve(nums)` | https://leetcode.com/problems/merge-adjacent-equal-elements/description/ |
| 3835 | Count Subarrays With Cost Less Than or Equal to K | `solve(nums, k)` | https://leetcode.com/problems/count-subarrays-with-cost-less-than-or-equal-to-k/description/ |
| 3836 | Maximum Score Using Exactly K Pairs | `solve(nums1, nums2, k)` | https://leetcode.com/problems/maximum-score-using-exactly-k-pairs/description/ |
| 3839 | Number of Prefix Connected Groups | `solve(words, k)` | https://leetcode.com/problems/number-of-prefix-connected-groups/description/ |
| 3840 | House Robber V | `solve(nums, colors)` | https://leetcode.com/problems/house-robber-v/description/ |
| 3841 | Palindromic Path Queries in a Tree | `solve(n, edges, s, queries)` | https://leetcode.com/problems/palindromic-path-queries-in-a-tree/description/ |
| 3843 | First Element with Unique Frequency | `solve(nums)` | https://leetcode.com/problems/first-element-with-unique-frequency/description/ |
| 3844 | Longest Almost-Palindromic Substring | `solve(s)` | https://leetcode.com/problems/longest-almost-palindromic-substring/description/ |
| 3845 | Maximum Subarray XOR with Bounded Range | `solve(nums, k)` | https://leetcode.com/problems/maximum-subarray-xor-with-bounded-range/description/ |
| 3847 | Find the Score Difference in a Game | `solve(nums)` | https://leetcode.com/problems/find-the-score-difference-in-a-game/description/ |
| 3848 | Check Digitorial Permutation | `solve(n)` | https://leetcode.com/problems/check-digitorial-permutation/description/ |
| 3849 | Maximum Bitwise XOR After Rearrangement | `solve(s, t)` | https://leetcode.com/problems/maximum-bitwise-xor-after-rearrangement/description/ |
| 3850 | Count Sequences to K | `solve(nums, k)` | https://leetcode.com/problems/count-sequences-to-k/description/ |
| 3853 | Merge Close Characters | `solve(s, k)` | https://leetcode.com/problems/merge-close-characters/description/ |
| 3854 | Minimum Operations to Make Array Parity Alternating | `solve(nums)` | https://leetcode.com/problems/minimum-operations-to-make-array-parity-alternating/description/ |
| 3855 | Sum of K-Digit Numbers in a Range | `solve(l, r, k)` | https://leetcode.com/problems/sum-of-k-digit-numbers-in-a-range/description/ |
| 3857 | Minimum Cost to Split into Ones | `solve(n)` | https://leetcode.com/problems/minimum-cost-to-split-into-ones/description/ |
| 3858 | Minimum Bitwise OR From Grid | `solve(grid)` | https://leetcode.com/problems/minimum-bitwise-or-from-grid/description/ |
| 3859 | Count Subarrays With K Distinct Integers | `solve(nums, k, m)` | https://leetcode.com/problems/count-subarrays-with-k-distinct-integers/description/ |
| 3862 | Find the Smallest Balanced Index | `solve(nums)` | https://leetcode.com/problems/find-the-smallest-balanced-index/description/ |
| 3863 | Minimum Operations to Sort a String | `solve(s)` | https://leetcode.com/problems/minimum-operations-to-sort-a-string/description/ |
| 3864 | Minimum Cost to Partition a Binary String | `solve(s, encCost, flatCost)` | https://leetcode.com/problems/minimum-cost-to-partition-a-binary-string/description/ |
| 3867 | Sum of GCD of Formed Pairs | `solve(nums)` | https://leetcode.com/problems/sum-of-gcd-of-formed-pairs/description/ |
| 3868 | Minimum Cost to Equalize Arrays Using Swaps | `solve(nums1, nums2)` | https://leetcode.com/problems/minimum-cost-to-equalize-arrays-using-swaps/description/ |
| 3869 | Count Fancy Numbers in a Range | `solve(l, r)` | https://leetcode.com/problems/count-fancy-numbers-in-a-range/description/ |
| 3871 | Count Commas in Range II | `solve(n)` | https://leetcode.com/problems/count-commas-in-range-ii/description/ |
| 3872 | Longest Arithmetic Sequence After Changing At Most One Element | `solve(nums)` | https://leetcode.com/problems/longest-arithmetic-sequence-after-changing-at-most-one-element/description/ |
| 3873 | Maximum Points Activated with One Addition | `solve(points)` | https://leetcode.com/problems/maximum-points-activated-with-one-addition/description/ |
| 3876 | Construct Uniform Parity Array II | `solve(nums1)` | https://leetcode.com/problems/construct-uniform-parity-array-ii/description/ |
| 3877 | Minimum Removals to Achieve Target XOR | `solve(nums, target)` | https://leetcode.com/problems/minimum-removals-to-achieve-target-xor/description/ |
| 3878 | Count Good Subarrays | `solve(nums)` | https://leetcode.com/problems/count-good-subarrays/description/ |
| 3881 | Direction Assignments with Exactly K Visible People | `solve(n, pos, k)` | https://leetcode.com/problems/direction-assignments-with-exactly-k-visible-people/description/ |
| 3882 | Minimum XOR Path in a Grid | `solve(grid)` | https://leetcode.com/problems/minimum-xor-path-in-a-grid/description/ |
| 3883 | Count Non Decreasing Arrays With Given Digit Sums | `solve(digitSum)` | https://leetcode.com/problems/count-non-decreasing-arrays-with-given-digit-sums/description/ |
| 3885 | Design Event Manager | `native class and solve operation replay` | https://leetcode.com/problems/design-event-manager/description/ |
| 3886 | Sum of Sortable Integers | `solve(nums)` | https://leetcode.com/problems/sum-of-sortable-integers/description/ |
| 3887 | Incremental Even-Weighted Cycle Queries | `solve(n, edges)` | https://leetcode.com/problems/incremental-even-weighted-cycle-queries/description/ |
| 3889 | Mirror Frequency Distance | `solve(s)` | https://leetcode.com/problems/mirror-frequency-distance/description/ |

## Coordinator next actions

Reconcile private source availability and role classification before admitting candidates. Resolve the 41 missing specifications/interfaces without changing their assigned IDs. After the authoring-only handoff, any requested execution should use Gamma's existing contract-bound qualification route, checking both language outputs, boundary values, numerical behavior, effects and resource bounds. No such checks are claimed by this delivery.
