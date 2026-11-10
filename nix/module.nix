# NixOS-Modul für waytimetrack.
#
# Wird normalerweise über ../default.nix eingebunden (aktiviert sich dann selbst)
# und legt den Befehl `waytimetrack` systemweit an.
{ config, lib, pkgs, ... }:

let
  cfg = config.programs.waytimetrack;
  tt = config.services.timetrack or { };
  # timetrack nimmt nur Anfragen an localhost-Adressen an (Schutz vor DNS-Rebinding)
  ttListen = tt.listenAddress or "127.0.0.1";
  ttHost =
    if ttListen == "::1" then "[::1]"
    else if builtins.elem ttListen [ "0.0.0.0" "::" "" ] then "127.0.0.1"
    else ttListen;
in
{
  options.programs.waytimetrack = {
    enable = lib.mkEnableOption "waytimetrack (Waybar-Modul für timetrack)";

    url = lib.mkOption {
      type = lib.types.str;
      # Port aus dem timetrack-Modul übernehmen, falls es auf demselben Rechner läuft
      default = "http://${ttHost}:${toString (tt.port or 54321)}";
      defaultText = lib.literalExpression ''"http://127.0.0.1:''${toString config.services.timetrack.port}"'';
      description = ''
        Adresse des timetrack-Webservers. timetrack nimmt nur Anfragen an localhost,
        127.0.0.1 und [::1] an; andere Hostnamen müssen dort in
        services.timetrack.allowedHosts eingetragen sein.
      '';
    };

    signal = lib.mkOption {
      type = lib.types.ints.between 0 30;
      default = 8;
      description = ''
        Signalnummer, mit der Waybar nach einem Umschalten sofort aktualisiert wird
        (muss mit "signal" im Waybar-Modul übereinstimmen, 0 = aus).
      '';
    };

    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.callPackage ./package.nix { };
      defaultText = lib.literalExpression "pkgs.callPackage ./package.nix { }";
      description = "Das waytimetrack-Paket (ohne die Einstellungen oben).";
    };
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      (pkgs.symlinkJoin {
        name = "waytimetrack-configured";
        paths = [ cfg.package ];
        nativeBuildInputs = [ pkgs.makeWrapper ];
        postBuild = ''
          rm $out/bin/waytimetrack
          makeWrapper ${lib.getExe cfg.package} $out/bin/waytimetrack \
            --set-default WAYTIMETRACK_URL ${lib.escapeShellArg cfg.url} \
            --set-default WAYTIMETRACK_SIGNAL ${toString cfg.signal}
        '';
        meta.mainProgram = "waytimetrack";
      })
    ];
  };
}
