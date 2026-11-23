# Fixed-source vocabulary comparison v1: frozen design

Written before any dictionary was built on this corpus. Only file counts, byte
counts and alphabet sizes had been read. Owner direction, 2026-11-23: "What is
the best shared vocabulary for a fixed collection of real programs?"

## Inputs

`manifest.json` freezes 400 problem IDs and one qualified reference solution per
language, by SHA-256: 800 files, 148,488 bytes of Python and 116,420 of
JavaScript, alphabets of 91, 92 and 94 together. These are the 300-fit and
100-exposed development programs of `pure-literal-compare-v1`. The final held-out
and protected problems stay closed. Source text, dictionaries and parses stay
private and outside Git. Only hashes and aggregates are published here.

No rewriting, renaming, helpers or raw escape. One corpus chooses and evaluates
every dictionary. This is in-sample by design and says nothing about unseen code.

## Rules

- **Corpora:** Python, JavaScript, both.
- **Entry:** a nonempty byte string of at most `L` bytes. A multi-byte entry must
  occur in at least two different files and may not equal a whole file. Single
  characters are always eligible, except in the no-singleton arm.
- **Grid:** `K` in 64, 96, 128, 192, 256, 384, 512, 768, 1024, 2048, 4096;
  `L` in 1, 2, 4, 8, 16, 32, 64; stored bytes `B` in 1, 2, 4, 8, 16, 32, 64 KiB
  or uncapped. Stored bytes are the sum over entries of one length byte plus the
  entry. Two dictionaries also pay 4 bytes of routing header.
- **Score:** total token emissions over every file of the corpus, under the
  shortest-path parse of that dictionary. Totals are compared only between
  dictionaries that spell every file.

## Arms

1. `char`: single characters only.
2. `freq-occ`, `freq-doc`: alphabet, then eligible strings ranked by
   (non-overlapping occurrences or file count) times (length - 1).
3. `bpe`: byte pair encoding with the entry rule; `bpe-free`: without the
   two-file rule. Each is reported with its ordinary merge segmentation and with
   the shortest-path parse of the same codebook.
4. `greedy-entry`, `greedy-byte`: alphabet, then the eligible string with the
   largest exact drop in total emissions, per entry or per stored byte. Lazy
   evaluation; a heuristic, with no optimality claim.
5. `no-singleton`: entries of 2 to `L` bytes only.
6. `shared` against `separate`: one dictionary for both languages against two
   whose entries and stored bytes sum to the same budget, with the best split.

## Labels

Every number is one of: **verified construction** (a stored dictionary, every
file decoded and compared byte for byte by a separate checker), **bound** (a
stored dual certificate rechecked in exact integers), or **proved optimum**
(construction equals bound). An uncovered corpus is either **proved impossible**
(no eligible dictionary of that size or kind exists, by a rank or reachability
certificate) or **no dictionary found**.

## Work limits

At most 8 worker processes at the lowest CPU priority, 45 minutes per chain, 32
GB. A chain stopped by its limit is reported as stopped. Improving the search
within these rules is allowed. A change to the corpus, eligibility, grid, or
score is a named variant, and this run stays on record.

## Predictions, written first

- **P1.** At `K` = 256 and `L` = 16 on both languages, `greedy-entry` uses at
  least 5% fewer emissions than the best frequency or BPE arm under the same
  shortest-path parser.
- **P2.** Shortest-path parsing lowers BPE's emissions by at least 3% at that cell.
- **P3.** At the same combined budget, one shared dictionary beats two separate
  ones at every `K` up to 1024 with `L` = 16 and no byte cap.
- **P4.** At `K` = 4096 and `L` = 16, two separate dictionaries beat one shared.
- **P5.** The no-singleton arm cannot spell all 800 files at any `K` for `L` = 16,
  and this is proved by reachability, not merely unfound.
- **P6.** No dictionary of fewer entries than the alphabet spells a whole corpus,
  proved by block rank, for each corpus at `L` = 16.
- **P7.** At `K` = 256, `L` = 16 on both languages, entries that cross a lexical
  boundary (for example a keyword with its following space and punctuation)
  account for more than half of the emissions saved.
