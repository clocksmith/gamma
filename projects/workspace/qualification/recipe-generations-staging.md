# Managed recipe generation: isolated hosted D1 gate

On 2026-11-21 UTC, Wrangler 4.141.0 deployed the synthetic qualification
entrypoint to an isolated staging Worker with a newly created D1 database.
Deployment reported exactly one D1 binding, `STAGING_DB`, pointing at the
dedicated staging database. The production Worker, database and configuration
were not used for any qualification request or mutation. The staged endpoint
returned 404 to the anonymous seed request before secrets were provisioned.

Verified against the real HTTPS staging endpoint:

| Check | Result |
| --- | --- |
| Synthetic corpus versus independent, fresh local SQLite oracle | 7 cases; all 16 probe classifications and checkpoint diagnostics agree |
| Legacy parity | 15 expected matches; one intentionally lagged legacy resolver correctly reported mismatch |
| Signed generation read | Exact generation 1 accepted using independently pinned Ed25519 public key, namespace, policy and replay floor |
| Independent content oracle | Snapshot and generation digests match the local SQLite result |
| Bearer scope | Anonymous and foreign-workspace seed attempts rejected; foreign workspace denied the signed generation |
| Cache transport policy | Signed response private/no-store; verified client admitted the bounded packet |

## Reproduce in a new, empty staged database

Use the staging-only entrypoint `qualification/recipe-generations-staging-worker.js`
with Node compatibility, a new D1 binding named `STAGING_DB`, and
`GAMMA_STAGING_ONLY=synthetic-recipe-qualification-v1`. Deploy only under a
`gamma-ws-qualification-stage-*` Worker name. Keep previews disabled and
verify the bound database identity before deployment. Anonymous requests fail
closed, including when there are no secrets.

Generate new random 32-byte bearer, foreign bearer and namespace values in
hex, plus an Ed25519 keypair. Set SHA-256 of each bearer as
`GAMMA_STAGE_BEARER_HASH` and `GAMMA_STAGE_FOREIGN_HASH`, namespace hex as
`GAMMA_STAGE_SCOPE_SECRET`, and the private PKCS#8 PEM as
`GAMMA_STAGE_SIGNER_PEM` using the supported Worker secret channel.
Never put these values in config or commit them. The verifier reads a
private local JSON file with `token`, `foreignToken`, `namespaceSecret`
and independently generated public SPKI PEM `publicKey`:

```sh
node qualification/recipe-generations-staging-check.js \
  https://gamma-ws-qualification-stage-<id>.<subdomain>.workers.dev /private/operator.json
```

This seeds a fixed synthetic corpus once and checks its dedicated namespace;
it is not a production deployment recipe or a live-workflow migration.
No hosted multi-region failover, production authorization, or route cutover
was attempted. The usual production Worker does not import the stage handler.
