# Vérification du jeu en ligne

Le 31/10/2026 13:42 · dossier vérifié : `C:\Users\mesck\AppData\Local\Temp\SickChessEssai061`

Fabriqué par `python outils/verifier_en_ligne.py`.

- ✅ steam_api64.dll présent à côté du jeu
- ✅ steam_appid.txt contient un numéro (480)
- ⚪ Numéro 480 = test de Valve (« Spacewar ») : accepter une invitation quand SickChess est FERMÉ lancerait Spacewar. L'ami doit ouvrir SickChess d'abord, puis accepter (ou taper le code).
- ✅ SickChess.exe présent (version installée)
- ✅ Connexion à Steam
- ✅ Compte : Sick · numéro du jeu : 480
- ✅ 37 ami(s) Steam visibles (dont 8 en ligne)
- ✅ Salon créé, code U0W2-QFF8-FNZ
- ✅ Le code redonne bien le même salon
- ✅ Écriture / lecture des informations du salon
- ✅ Tu es bien l'hôte du salon
- ✅ Salon refermé
- ✅ test_multijoueur.py : 41 contrôles OK, 0 en échec
- ✅ test_en_ligne_nulle.py : 15 contrôles OK, 0 en échec

## Dernier test, à faire à deux (ne peut pas se faire seul)
1. Deux PC, deux comptes Steam **amis**, Steam ouvert des deux côtés, SickChess installé chez les deux (installeur ou version amis).
2. Les deux ouvrent SickChess → *Jouer en ligne*.
3. Toi : *Créer une partie* → *Inviter* ton ami (liste dans le jeu) ou donne-lui le code.
4. L'ami : accepte l'invitation dans Steam **avec SickChess déjà ouvert**, ou tape le code.
5. Jouer quelques coups, écrire dans le chat, proposer la nulle, abandonner, revanche.
6. Couper le Wi-Fi d'un PC 20 s : la partie doit reprendre ; plus de 60 s : partie interrompue.

**Verdict** : tout est bon de ce côté.
