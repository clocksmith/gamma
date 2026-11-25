# L3: NetBox v4.1.11 to v4.2.0, prefix `site` replaced by scope

One command runs the whole case (gates A, B and C, three repeats each, every repeat on a stack
started from nothing) and writes `../../results/L3.json`:

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
   the community NetBox image, all pulled by the digests in the sealed list, on their own network.
   The image applies all migrations on first start and creates the superuser and its API token from
   its own environment settings. The from-version stack uses `127.0.0.1:28630`, the to-version stack
   `127.0.0.1:28631`; the two run side by side and share nothing.
2. **Set-up** through the REST API with the superuser token: site HQ; a non-superuser `neteng` with
   object permissions view/add/change on `ipam.prefix` and view on `dcim.site`; an API token for it.
3. **Old workflow** (gates A and B) as `neteng`, exactly as sealed: `POST /api/ipam/prefixes/` with
   `{"prefix": "192.0.2.0/24", "site": S, "status": "active"}`; HTTP 201 is success.
4. **Correct path** (gate C) as `neteng`, on a second prefix at the same site, on the instance that
   served gate B: `{"prefix": "198.51.100.0/24", "scope_type": "dcim.site", "scope_id": S,
   "status": "active"}`.
5. **Database read**: the `ipam_prefix` row of the returned id with `psql` inside the PostgreSQL
   container (`site_id` on v4.1.11; `scope_type_id`, `scope_id`, `_site_id` on v4.2.0, with the
   content type of `dcim.site` read from `django_content_type`). A read of the prefix by the
   superuser is kept as a second witness.
6. **Tear-down**: containers, volumes and the network, selected by the labels
   `gammatron-screen=iu1-b` and `iu1-b-case=L3f` / `L3t`.

Files: `run.py` (the case), `netbox.py` (bring-up and set-up, identical to the copy in `../L2`),
`lib.py` (helpers shared by this lane's cases).
