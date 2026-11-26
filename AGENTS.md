# Scope and working rules

This repository documents Daniel's VPS preparation and two WordPress migrations.
It is an operations case study with reusable examples, not application source.

- Work locally unless the user explicitly authorizes a server operation.
- Do not modify production, change DNS, cancel hosting, send email, import a
  database or initiate a payment merely to improve this portfolio repository.
- Never publish `ops/`: it contains original, environment-specific operational
  material that must remain on Daniel's workstation.
- Keep credentials, SQL dumps, customer data, private SSH keys, real server
  addresses, account identifiers, raw logs and deployment passwords out of Git.
- Use `.example.invalid` hostnames and documentation IP ranges in examples.
- Do not copy WordPress, commercial plugins/themes, the embroidery editor or
  customer downloads into this repository. They have separate ownership and
  repositories.
- Describe historical results as historical. A passing syntax test is not a
  successful production migration. A queued email is not a delivered email.
- Follow `docs/06-estado-y-limitaciones.md` when reporting completion.
- Run `make check` and `make test` before committing. Stage named project files
  only; do not use `git add .` or `git add --all` in this workspace.
- The tools default to planning or read-only checks. Preserve explicit opt-in
  for copying data. Never add destructive rsync flags to copy mode.
- New task branches use the `codex/` prefix. No force pushes or secret uploads.
