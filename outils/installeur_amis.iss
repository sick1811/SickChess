; outils/installeur_amis.iss - installeur Windows de la version amis (Inno Setup 6.3+).
;
; Fabrique par outils/publier_maj.py (CONSTRUIRE_VERSION_AMIS.bat), qui passe :
;   /DVersion=0.1.0  /DNumero=12  /DSource=<dossier du jeu pret>  /DSortie=<dossier>
; A la main (pour essayer) :
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DVersion=0.1.0 /DNumero=1 ^
;       /DSource=build_amis\installeur\SickChess /DSortie=build_amis outils\installeur_amis.iss
;
; Choix faits pour que Windows fasse confiance au programme (sans rien cacher) :
;   - installation pour l'utilisateur seulement : AUCUNE demande d'administrateur ;
;   - dossier inscriptible (%LOCALAPPDATA%\Programs\SickChess) : la mise a jour
;     automatique peut remplacer les fichiers sans droits speciaux ;
;   - nom, editeur, version et description renseignes (installeur ET SickChess.exe) ;
;   - pas de compression « exotique » ni de lanceur qui se deguise ;
;   - signature numerique possible (voir outils/maj_config.json, cle "signature").
; Les parties, le profil et les reglages restent dans le dossier du jeu et ne sont
; pas effaces par la desinstallation (seuls les fichiers installes le sont).

#ifndef Version
  #define Version "0.1.0"
#endif
#ifndef Numero
  #define Numero "0"
#endif
#ifndef Source
  #define Source "..\build_amis\installeur\SickChess"
#endif
#ifndef Sortie
  #define Sortie "..\build_amis"
#endif

[Setup]
AppId={{6F1C2B4E-5A7D-4C1E-9B3A-51C4E5C8A9D2}
AppName=SickChess
AppVersion={#Version} (n°{#Numero})
AppVerName=SickChess {#Version}
AppPublisher=sick1811
AppPublisherURL=https://github.com/sick1811/SickChess-amis
AppSupportURL=https://github.com/sick1811/SickChess-amis
VersionInfoVersion={#Version}.{#Numero}
VersionInfoProductName=SickChess
VersionInfoProductVersion={#Version}
VersionInfoCompany=sick1811
VersionInfoDescription=Installation de SickChess (version amis)
VersionInfoCopyright=sick1811
PrivilegesRequired=lowest
DefaultDirName={autopf}\SickChess
DisableProgramGroupPage=yes
DefaultGroupName=SickChess
OutputDir={#Sortie}
OutputBaseFilename=SickChess_Installation
SetupIconFile=..\assets\icone.ico
UninstallDisplayIcon={app}\SickChess.exe
UninstallDisplayName=SickChess
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
ShowLanguageDialog=no

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "bureau"; Description: "Mettre une icône SickChess sur le Bureau"; GroupDescription: "Raccourcis :"

[Files]
Source: "{#Source}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\SickChess"; Filename: "{app}\SickChess.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\SickChess"; Filename: "{app}\SickChess.exe"; WorkingDir: "{app}"; Tasks: bureau

[Run]
Filename: "{app}\SickChess.exe"; WorkingDir: "{app}"; Description: "Lancer SickChess"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\maj_temp"
