# waytimetrack

Waybar-Modul + Sway-Umschalter für timetrack (`~/timetrack`, Flask-API auf Port 54321).

- `waytimetrack.py`: nur Python-Stdlib. `status` = Waybar-JSON (text/class/tooltip), `toggle` = POST /api/toggle,
  danach SIGRTMIN+WAYTIMETRACK_SIGNAL an eigene waybar-Prozesse (comm `waybar` oder `.waybar-wrapped`)
- `default.nix` = NixOS-Modul-Einstieg (aktiviert sich selbst), `nix/module.nix` (Optionen url/signal, Wrapper), `nix/package.nix`
- In der Sandbox gibt es kein Nix; testen gegen `TIMETRACK_DB_SQLITE=... TIMETRACK_PORT=... ~/timetrack/.venv/bin/python -m timetrack`
- timetrack-Sicherheit: nur Host localhost/127.0.0.1/[::1], ändernde Anfragen nur als JSON → `api()` sendet bei POST immer JSON
