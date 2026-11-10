{ lib, stdenvNoCC, python3, makeWrapper, libnotify }:

stdenvNoCC.mkDerivation {
  pname = "waytimetrack";
  version = "1.0.0";

  src = lib.cleanSourceWith {
    src = ../.;
    filter = path: type: baseNameOf path == "waytimetrack.py";
  };

  nativeBuildInputs = [ makeWrapper ];
  buildInputs = [ python3 ];

  installPhase = ''
    runHook preInstall
    install -Dm755 waytimetrack.py $out/libexec/waytimetrack.py
    patchShebangs $out/libexec/waytimetrack.py
    makeWrapper $out/libexec/waytimetrack.py $out/bin/waytimetrack \
      --suffix PATH : ${lib.makeBinPath [ libnotify ]}
    runHook postInstall
  '';

  doInstallCheck = true;
  installCheckPhase = ''
    $out/bin/waytimetrack --help
    WAYTIMETRACK_URL=http://127.0.0.1:1 $out/bin/waytimetrack status | grep -q '"class": "error"'
  '';

  meta = {
    description = "Waybar-Modul und Sway-Umschalter für timetrack (Arbeit/Pause)";
    mainProgram = "waytimetrack";
    platforms = lib.platforms.linux;
  };
}
