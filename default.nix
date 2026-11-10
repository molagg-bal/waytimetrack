# Einstiegspunkt für configuration.nix:
#
#   imports = [ (fetchTarball "https://github.com/BENUTZERNAME/waytimetrack/archive/refs/heads/main.tar.gz") ];
#
# Importieren genügt: der Befehl `waytimetrack` wird damit automatisch installiert
# (abschaltbar mit programs.waytimetrack.enable = false;).
{ lib, ... }:
{
  imports = [ ./nix/module.nix ];
  programs.waytimetrack.enable = lib.mkDefault true;
}
