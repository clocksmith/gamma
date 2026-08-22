# FTRL512 Joint Decision v7

This correction-only decision successor reads the unchanged sealed v5 arm
artifacts and retains every v6 synchronization, resource, package, control, and
compression gate. It grants zero compression credit.

v7 replaces equal-length cross-arm payload tests with all of:

```text
payload byte count equal
payload SHA-256 equal
durable payload files present
direct chunked byte comparison equal
```

The stronger identity is required for C=P and P=K. Equal archive or payload
length alone is never identity evidence.
