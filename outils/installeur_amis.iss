; outils/installeur_amis.iss - installeur Windows de la version amis (Inno Setup 6.3+).
;
; Fabrique par outils/publier_maj.py (CONSTRUIRE_VERSION_AMIS.bat), qui passe :
;   /DVersion=0.1.0  /DNumero=12  /DSource=<dossier du jeu pret>  /DSortie=<dossier>
; A la main (pour essayer) :
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DVersion=0.1.0 /DNumero=1 ^
;       /DSource=build_amis\installeur\SickChess /DSortie=build_amis outils\installeur_amis.iss
;
; Choix faits pour que Windows fasse confiance au programme (sans rien cacher) :
;   - installation pour l'utilisateur seulement : pas besoin d'administrateur pour
;     installer. SEULE exception (25/10, demande de Julien) : a la fin, Windows
;     demande UNE fois l'accord pour autoriser SickChess.exe dans le pare-feu
;     (Internet et Steam, reseau prive ET public). Refuse : le jeu redemandera
;     lui-meme au lancement (jeu/pare_feu.py). Rien d'autre n'est modifie ;
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
; Problemes et tables de finales (~1,2 Go) sont deja compresses : une compression
; normale non solide va bien plus vite pour le meme resultat.
Compression=lzma2/normal
SolidCompression=no
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

[Code]
// 25/10 : autoriser SickChess.exe dans le pare-feu de Windows, sur tous les
// reseaux (prive, public, domaine), en entree et en sortie. Les anciennes regles
// du programme (dont les regles de BLOCAGE creees par Windows quand on a clique
// « Annuler » sur son message) sont retirees d'abord. Memes commandes que
// jeu/pare_feu.py. Installation silencieuse (/VERYSILENT, essais) : rien demande.
function CommandesParFeu(const Exe: String): String;
begin
  Result := 'netsh advfirewall firewall delete rule name=SickChess & ' +
    'netsh advfirewall firewall delete rule name=all program="' + Exe + '" & ' +
    'netsh advfirewall firewall add rule name=SickChess dir=in action=allow program="' +
    Exe + '" enable=yes profile=any & ' +
    'netsh advfirewall firewall add rule name=SickChess dir=out action=allow program="' +
    Exe + '" enable=yes profile=any';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Code: Integer;
begin
  if (CurStep = ssPostInstall) and (not WizardSilent) then
  begin
    WizardForm.StatusLabel.Caption :=
      'Autorisation de SickChess (Internet et Steam) : Windows demande ton accord...';
    ShellExec('runas', ExpandConstant('{cmd}'),
      '/c ' + CommandesParFeu(ExpandConstant('{app}\SickChess.exe')),
      '', SW_HIDE, ewWaitUntilTerminated, Code);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Code: Integer;
begin
  if (CurUninstallStep = usUninstall) and (not UninstallSilent) then
    ShellExec('runas', ExpandConstant('{cmd}'),
      '/c netsh advfirewall firewall delete rule name=SickChess',
      '', SW_HIDE, ewWaitUntilTerminated, Code);
end;
