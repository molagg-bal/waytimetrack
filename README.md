# waytimetrack

Waybar-Button für timetrack (Arbeitszeiterfassung, eigenes Repository): zeigt `wt: 3h 25m` (heutige Arbeitszeit,
wie auf der Startseite von timetrack) und schaltet per Klick oder Tastenkombination
zwischen Arbeit und Pause um.

- **grün** = WORK (Arbeit läuft), **rot** = PAUSE, **grau** = timetrack nicht erreichbar
- Tooltip: seit wann Arbeit/Pause, Pause heute, Soll, Saldo heute, Überstundenkonto
- Nach jedem Umschalten (Klick oder Tastatur) aktualisiert sich der Button sofort,
  sonst alle 30 Sekunden.
- Fehler beim Umschalten (z. B. an einem AU- oder EGZ-Tag) erscheinen als Benachrichtigung.

Es benutzt dieselbe API wie der Button der Web-App (`/api/status`, `/api/toggle`).
Ein Klick in Waybar und ein Klick im Browser sind also gleichwertig. Ein offener
Browser-Tab zeigt den neuen Stand nach dem Neuladen.

## 1. Installation (configuration.nix)

In `/etc/nixos/configuration.nix` eine Zeile in die `imports`-Liste, neben timetrack:

```nix
imports = [
  ./hardware-configuration.nix
  (fetchTarball "https://github.com/BENUTZERNAME/timetrack/archive/refs/heads/main.tar.gz")
  (fetchTarball "https://github.com/BENUTZERNAME/waytimetrack/archive/refs/heads/main.tar.gz")
];
```

Danach:

```bash
sudo nixos-rebuild switch
```

Damit ist der Befehl `waytimetrack` installiert. Mehr ist nicht nötig: Python und
`notify-send` bringt das Paket mit, die Adresse von timetrack (Port) übernimmt es
automatisch aus dem timetrack-Modul.

Hinweise:
- Das GitHub-Repository muss **öffentlich** sein. `BENUTZERNAME` ist dein GitHub-Benutzername.
- Updates kommen mit dem nächsten `nixos-rebuild switch` (Nix lädt `main` neu, wenn
  der Cache älter als 1 h ist).

Optionen (alle optional):

| Option | Standard | Bedeutung |
|---|---|---|
| `programs.waytimetrack.enable` | `true` (durch den Import) | Befehl installieren |
| `programs.waytimetrack.url` | `http://127.0.0.1:<services.timetrack.port>` | Adresse von timetrack |
| `programs.waytimetrack.signal` | `8` | Signal für die sofortige Aktualisierung, muss zu `"signal"` in Waybar passen |

## 2. Waybar

Waybar-Konfiguration: `~/.config/waybar/config` (oder `config.jsonc`). Falls es die
Datei noch nicht gibt, die mitgelieferte Vorlage kopieren:

```bash
mkdir -p ~/.config/waybar && cp "$(dirname "$(readlink -f "$(command -v waybar)")")"/../etc/xdg/waybar/* ~/.config/waybar/ && chmod u+w ~/.config/waybar/*
```

**a)** Das Modul in eine der Listen `modules-left`, `modules-center` oder
`modules-right` eintragen, zum Beispiel:

```jsonc
"modules-right": ["custom/wt", "pulseaudio", "network", "clock", "tray"],
```

**b)** Die Moduldefinition auf der obersten Ebene ergänzen (zwischen die anderen
Module wie `"clock": {...}`, Komma nicht vergessen):

```jsonc
"custom/wt": {
    "exec": "waytimetrack status",
    "return-type": "json",
    "interval": 30,
    "signal": 8,
    "on-click": "waytimetrack toggle",
    "tooltip": true
},
```

**c)** Farben in `~/.config/waybar/style.css` ans Ende anhängen:

```css
#custom-wt {
    padding: 0 10px;
    margin: 0 4px;
    border-radius: 4px;
    color: #ffffff;
    font-weight: bold;
}
#custom-wt.work  { background-color: #2e7d32; }  /* grün: Arbeit */
#custom-wt.pause { background-color: #c62828; }  /* rot: Pause */
#custom-wt.error { background-color: #616161; }  /* grau: timetrack nicht erreichbar */
```

Waybar neu laden: `swaymsg reload` (startet Waybar neu, wenn es über `bar { swaybar_command waybar }`
in der Sway-Konfiguration läuft). Läuft Waybar als systemd-Dienst (`programs.waybar.enable`),
dann `systemctl --user restart waybar`.

## 3. Sway-Tastenkombination

In `~/.config/sway/config` eine Zeile ergänzen (z. B. unter den anderen `bindsym`):

```
bindsym $mod+Shift+w exec waytimetrack toggle
```

Danach `swaymsg reload` (bzw. `$mod+Shift+c`). Die Kombination ist frei wählbar,
`$mod+Shift+w` ist in der Standard-Sway-Konfiguration nicht belegt.

## Fehlersuche

```bash
waytimetrack status    # muss eine Zeile JSON ausgeben, z. B. {"text": "wt: 3h 25m", ...}
waytimetrack toggle    # schaltet um und gibt den neuen Zustand aus (work/pause)
```

- Button grau mit `wt: --`: timetrack läuft nicht (`systemctl status timetrack`) oder die
  Adresse stimmt nicht (Tooltip zeigt den Fehler; `programs.waytimetrack.url` setzen).
- Button aktualisiert sich nach einem Klick erst nach bis zu 30 s: Die Zahl bei
  `"signal"` in Waybar passt nicht zu `programs.waytimetrack.signal` (Standard beide 8).

Ohne NixOS lässt sich das Skript auch direkt benutzen: `waytimetrack.py` braucht nur
Python ≥ 3.10; die Adresse kommt dann aus `WAYTIMETRACK_URL`, das Signal aus
`WAYTIMETRACK_SIGNAL`.

## Aufbau

- `waytimetrack.py`: das Programm (nur Python-Standardbibliothek)
- `default.nix`: NixOS-Modul-Einstieg (importiert `nix/module.nix`, aktiviert sich selbst)
- `nix/package.nix`, `nix/module.nix`: Paket und Modul
