# outils/vulture_liste_blanche.py - noms que vulture croit inutiles mais qui servent.
# vulture cherche les fonctions jamais appelees. Certaines le sont « par leur nom »
# (pygame, Steam, json, appels construits avec getattr) : on les cite ici pour
# qu'il ne les signale plus. Une ligne = un nom, avec la raison.
#
# Ajouter un nom ici seulement apres avoir verifie qu'il sert vraiment.

_ = None  # noqa: F841  (fichier lu par vulture, jamais execute par le jeu)

# 23/10 : valeurs « rangees mais jamais relues » qui sont en fait lues ailleurs.
_.dwLength   # structure Windows (ctypes) : c'est Windows qui lit ce champ
_.dwFlags    # structure Windows (ctypes) : c'est Windows qui lit ce champ
_.comment    # commentaire d'un coup PGN : lu par python-chess a l'export
_.midtop     # rectangle pygame : place le rectangle, c'est sa position qui sert

# 31/10 (menage, constat 9b) : valeurs rangees que lisent les tests et les outils.
_.terminees          # analyse_de_fond : compte relu par tests/test_analyse_de_fond.py
_.analyse_libre      # ecran_revue : relu par tests/test_analyse_libre.py et outils/recette_auto.py
_.ep_square          # plateau python-chess : prise en passant, c'est python-chess qui le lit (regle)

# 31/10 (menage, constat 9c) : fonctions appelees seulement par les tests ou les outils
# (vulture ne lit que jeu/).
_.roles_vivants      # moteurs : tests/test_analyse_libre_moteur.py, test_moteur_decale.py, recette_auto.py
_.texte_temps_restant  # analyse_partie : tests/test_temps_revue.py
_.retirer_crochet    # ui : tests/test_invitations.py, test_plantage.py
_.couleur_revanche   # mode_en_ligne : tests/test_multijoueur.py
_.oublier_les_tranches  # puzzles : tests/test_problemes.py
_.afficher_ligne     # notation : tests/test_analyse_directe.py
# Gardees par prudence (a decider avec Julien) :
_.refuser_revanche   # mode_en_ligne : refus de revanche en ligne, pas encore branche sur un bouton
_.secondes_avant_reclamation  # pendule_reseau : chute au temps en ligne (regle), gardee
_.set_time           # timer : tests/test_noyau.py
_.ESPACE             # design : l'echelle d'espacement de la charte (reference ecrite), gardee
_.identifiant        # profil : adresse du joueur pour le jeu en ligne (autre chantier en cours), gardee
