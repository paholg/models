{ appimageTools, fetchurl, webkitgtk_4_1 }:

let
  pname = "snapmaker-orca";
  version = "2.4.1";

  src = fetchurl {
    url = "https://github.com/Snapmaker/OrcaSlicer/releases/download/v${version}/Snapmaker_Orca_Linux_AppImage_Ubuntu2404_V${version}.AppImage";
    hash = "sha256-K1EX4i0Eo6J7zfxahzxV0o/zt86XIZRt4fE0+pfSzAY=";
  };

  contents = appimageTools.extract { inherit pname version src; };
in
appimageTools.wrapType2 {
  inherit pname version src;

  extraPkgs = _: [ webkitgtk_4_1 ];

  # Disable the input method (ibus/fcitx) for Orca: under XWayland it injects
  # stray text into ImGui text fields (e.g. the emboss tool) and steals focus.
  profile = ''
    export XMODIFIERS=@im=none
    export GTK_IM_MODULE=gtk-im-context-simple
    export QT_IM_MODULE=
  '';

  # Bundled printer/filament/process profiles (what Orca copies into ~/.config on startup).
  passthru.profiles = "${contents}/resources/profiles";

  extraInstallCommands = ''
    install -Dm444 ${contents}/io.github.Snapmaker.Snapmaker_Orca.desktop \
      $out/share/applications/snapmaker-orca.desktop
    substituteInPlace $out/share/applications/snapmaker-orca.desktop \
      --replace-fail 'Exec=AppRun' 'Exec=${pname}'
    install -Dm444 ${contents}/Snapmaker_Orca.png \
      $out/share/icons/hicolor/192x192/apps/Snapmaker_Orca.png
  '';
}
