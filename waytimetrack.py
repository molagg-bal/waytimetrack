#!/usr/bin/env python3
"""waytimetrack: Waybar-Modul und Umschalter für timetrack.

  waytimetrack status   gibt eine Zeile JSON für ein Waybar-"custom"-Modul aus
  waytimetrack toggle   wechselt zwischen Arbeit und Pause und aktualisiert Waybar

Umgebungsvariablen (optional):
  WAYTIMETRACK_URL     Adresse von timetrack (Standard http://127.0.0.1:54321)
  WAYTIMETRACK_SIGNAL  Signalnummer des Waybar-Moduls (Standard 8, 0 = aus)
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import urllib.error
import urllib.request

URL = os.environ.get("WAYTIMETRACK_URL", "http://127.0.0.1:54321").rstrip("/")
SIGNAL = int(os.environ.get("WAYTIMETRACK_SIGNAL", "8"))
TIMEOUT = 5


def fmt_dur(sec: int) -> str:
    neg = sec < 0
    sec = abs(round(sec))
    return f"{'−' if neg else ''}{sec // 3600}h {(sec % 3600) // 60:02d}m"


def fmt_signed(sec: int) -> str:
    return ("+" if sec > 0 else "") + fmt_dur(sec)


def api(method: str, path: str, body: dict | None = None) -> dict:
    # timetrack nimmt ändernde Anfragen nur als JSON an (CSRF-Schutz), daher immer JSON senden
    data = json.dumps(body if body is not None else {}).encode() if method != "GET" else None
    req = urllib.request.Request(URL + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as res:
            return json.load(res)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error")
        except Exception:
            msg = None
        raise RuntimeError(msg or f"Fehler {e.code}") from None
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError(f"timetrack unter {URL} nicht erreichbar ({getattr(e, 'reason', e)})") from None


def waybar_json(status: dict) -> dict:
    working = status["state"] == "work"
    t = status["today"]
    lines = ["Arbeit läuft" if working else "Pause"]
    if status.get("since"):
        lines[0] += f" seit {status['since'][11:16]}"
    lines.append(f"Arbeitszeit heute: {fmt_dur(t['net'])}")
    lines.append(f"Pause heute: {fmt_dur(t['pause'])}")
    if t.get("deduction"):
        lines.append(f"Gesetzlicher Pausenabzug: {fmt_dur(t['deduction'])}")
    if t.get("target"):
        lines.append(f"Soll heute: {fmt_dur(t['target'])}")
    lines.append(f"Saldo heute: {fmt_signed(t['delta'])}")
    lines.append(f"Überstundenkonto: {fmt_signed(status['balance'])}")
    if t.get("mark"):
        lines.append(f"Tagesart: {t['mark']}")
    if status.get("open_days"):
        lines.append("Arbeitsende vergessen: " + ", ".join(status["open_days"][-5:]))
    return {
        "text": f"wt: {fmt_dur(t['net'])}",
        "alt": status["state"],
        "class": status["state"],
        "tooltip": "\n".join(lines),
    }


def refresh_waybar():
    """Schickt allen eigenen Waybar-Prozessen SIGRTMIN+SIGNAL (wie pkill -RTMIN+n waybar)."""
    if SIGNAL <= 0:
        return
    sig = signal.SIGRTMIN + SIGNAL
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/comm") as f:
                if f.read().strip() not in ("waybar", ".waybar-wrapped"):
                    continue
            os.kill(int(pid), sig)
        except OSError:
            pass


def notify(msg: str):
    if shutil.which("notify-send"):
        subprocess.run(["notify-send", "-a", "waytimetrack", "timetrack", msg],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def cmd_status() -> int:
    try:
        out = waybar_json(api("GET", "/api/status"))
    except RuntimeError as e:
        out = {"text": "wt: --", "alt": "error", "class": "error", "tooltip": str(e)}
    print(json.dumps(out, ensure_ascii=False), flush=True)
    return 0


def cmd_toggle() -> int:
    try:
        status = api("POST", "/api/toggle", {})
    except RuntimeError as e:
        notify(str(e))
        print(e, file=sys.stderr)
        refresh_waybar()
        return 1
    refresh_waybar()
    print(status["state"])
    return 0


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "status":
        return cmd_status()
    if cmd == "toggle":
        return cmd_toggle()
    print(__doc__.strip(), file=sys.stderr)
    return 0 if cmd in ("-h", "--help", "help") else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
