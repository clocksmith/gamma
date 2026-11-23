# Screening set-up for later OpenProject releases

For `clocksmith/deco#88`, under amendment 2 of
`../second-upgrade-drift-rule.md`. **Not part of Stage A.** The frozen
bring-up in `../bringup/` is unchanged and is still what Stage A uses.

From OpenProject `16.4.0` a project must have a workspace type, and the frozen
seeder, written for `13.4.0` and `14.0.0`, cannot create its projects. This
folder holds what is needed to go on screening those releases:

| File | What it is |
| --- | --- |
| `seed_openproject_qual.rb` | The screening seeder. It differs from the frozen seeder only in setting the workspace type to an ordinary project on the four projects it creates, where the release has that field, and in its header comment. |
| `seeder.diff` | `diff ../bringup/seed_openproject_qual.rb seed_openproject_qual.rb`, in full |
| `openproject-up.sh` | A byte-identical copy of the frozen bring-up script. It is here only because that script mounts the seeder that lies beside it. |

No record is added or removed, and no value an arm or a label depends on is
changed: the same statuses, roles, four projects, two users and tokens. On
`16.4.0`, on a throwaway database, it printed the same status numbers (15 to
18) and user numbers (5 and 6) as the frozen seeder does on `14.0.0`.

A release that qualifies only with this seeder is reported as "bites with
adapted set-up" and needs its own freeze. Every entry screened with it also
records that check 4 was not met with the frozen seeder.
