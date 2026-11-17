# Square connection (not built yet)

Everything that talks to Square will live in this folder, so the rest of the
site stays simple static files.

Rules:
- Square access tokens never go in this repo. They go in `.env` (ignored by git)
  or the host's secret settings.
- Start with read-only connections (menu, hours) before ordering or payments.

Planned order of work, to be confirmed:
1. Read the Square item catalog and write it to `data/menu.json`.
2. Online ordering or payment links.
3. Reservations, if Square's tools fit.
