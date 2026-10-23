# outils/vulture_liste_blanche.py - noms que vulture croit inutiles mais qui servent.
# vulture cherche les fonctions jamais appelees. Certaines le sont « par leur nom »
# (pygame, Steam, json, appels construits avec getattr) : on les cite ici pour
# qu'il ne les signale plus. Une ligne = un nom, avec la raison.
#
# Ajouter un nom ici seulement apres avoir verifie qu'il sert vraiment.

_ = None  # noqa: F841  (fichier lu par vulture, jamais execute par le jeu)
