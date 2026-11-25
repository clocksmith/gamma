# N2: Dolibarr 18.0.9 to 19.0.2, order delivery date

One command runs the whole case (gates A, B and C, three repeats each, every repeat on an
instance started from nothing) and writes `../../results/N2.json`:

```sh
SCREEN_SCRATCH=/some/dir/outside/the/repository \
SCREEN_HOLD_FILE=/path/to/HOLD \
python3 run.py
```

`SCREEN_HOLD_FILE` is optional. Python 3 standard library and the `docker` command are the only
requirements. Passwords are generated per instance and are never written to the result file.

What `run.py` does, in order, for each repeat:

1. **Bring-up**: one MariaDB 10.6 container and one Dolibarr container, both pulled by the digest in
   the sealed list, on their own network, the application on `127.0.0.1:28610` only. The image
   installs itself on first start (`DOLI_INSTALL_AUTO=1`) and enables the third-party, order and REST
   API modules through its own `DOLI_ENABLE_MODULES` setting.
2. **Set-up** through the application: the administrator gets an API key from `POST /login`, creates
   two customers and the sales user through the REST API, and grants the sales user rights 81, 82,
   121 and 342 on the permissions page (an ordinary admin browser session). The sales user then gets
   its own API key from `POST /login`.
3. **Old workflow** (gates A and B), as the sales user, exactly as sealed:
   `POST /api/index.php/orders` with `{"socid": X, "date": 1795478400, "date_livraison": 1797292800}`;
   success is HTTP 200 and a returned order id.
4. **Correct path** (gate C), same user, second customer: the same request with `delivery_date` in
   place of `date_livraison`.
5. **Database read**: `llx_commande.date_livraison` for the returned id, with the `mariadb` client
   inside the database container. A read of the order by the administrator's key is kept as a
   second witness.
6. **Tear-down**: containers, anonymous volumes and the network, selected by the labels
   `gammatron-screen=iu1-b` and `iu1-b-case=N2`.

Files: `run.py` (the case), `lib.py` (helpers shared by this lane's cases: hold rule, pinned pulls,
request recording, redaction).
