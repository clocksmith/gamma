# L2: NetBox v4.0.11 to v4.1.0, VLAN group ranges

One command runs the whole case (gates A, B and C, three repeats each, every repeat on a stack
started from nothing) and writes `../../results/L2.json`:

```sh
SCREEN_SCRATCH=/some/dir/outside/the/repository \
SCREEN_HOLD_FILE=/path/to/HOLD \
python3 run.py
```

`SCREEN_HOLD_FILE` is optional. `--reuse` keeps repeats already recorded in the scratch directory and
runs only the missing ones. Python 3 standard library and the `docker` command are the only
requirements. Every password, the Django secret key and the API tokens are generated per stack.

Steps of one repeat:

1. **Bring-up** (`netbox.py`): PostgreSQL 16, one Redis (database 0 for queues, 1 for the cache) and
   the community NetBox image, all pulled by the digests in the sealed list. The from-version stack
   uses `127.0.0.1:28640`, the to-version stack `127.0.0.1:28641`; they run side by side and share
   nothing.
2. **Set-up** through the REST API with the superuser token: a non-superuser `neteng` with object
   permissions view/add/change on `ipam.vlangroup`, and an API token for it.
3. **Old workflow** (gates A and B) as `neteng`, exactly as sealed: `POST /api/ipam/vlan-groups/`
   with `{"name": "campus-a", "slug": "campus-a", "min_vid": 100, "max_vid": 199}`; HTTP 201 is
   success.
4. **Correct path** (gate C) as `neteng`, on a second group on the instance that served gate B:
   `{"name": "campus-c", "slug": "campus-c", "vid_ranges": [[100, 199]]}`.
5. **Database read**: the `ipam_vlangroup` row of the returned id with `psql` inside the PostgreSQL
   container (`min_vid`, `max_vid` on v4.0.11; `vid_ranges` on v4.1.0). A read of the group by the
   superuser is kept as a second witness.
6. **Supplementary probe**, after the stored value has been read: the superuser tries to add VLAN
   500 and VLAN 150 to the group. It shows what the stored range means for the business outcome and
   does not enter the disposition.
7. **Tear-down**: containers, volumes and the network, selected by the labels
   `gammatron-screen=iu1-b` and `iu1-b-case=L2f` / `L2t`.

Files: `run.py` (the case), `netbox.py` (bring-up and set-up, identical to the copy in `../L3`),
`lib.py` (helpers shared by this lane's cases).
