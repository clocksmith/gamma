# Prelaunch resource amendment — 2026-10-23

The original freeze 1016c92cc assigned R to core 0 and naming to core 1 after
item 30 completed. At 22:24Z, Claude confirmed that cores 14 and 15 are idle
and available for item 33. Assign R to 14 and naming to 15, allowing the T2
bound run to proceed concurrently with item 30 on cores 0–7 and item 29 on
11–13. Report release of 14/15 through the team LOG.

Only affinity and the resulting queue restriction change. The source population,
full substring class, optimizer, predictions, 8 GiB worker caps, 1,200-second
ascent budgets and 2,400-second whole-job deadline remain unchanged. Team
compute stays within the owner's cores 0–15. No corpus probe preceded this
amendment. The contract pins this document and the updated generator.
