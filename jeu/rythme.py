# rythme.py - V7.2 : NOUVEAU FICHIER
#
# LE TEMPS DE REFLEXION DE STOCKFISH, ADAPTE A LA CADENCE (ta demande :
# "rapidite stockfish pas adapte en bullet - vitesse similaire selon la duree
# de partie, 1 MIN ou 30 MIN").
#
# CE QUI N'ALLAIT PAS : le budget de reflexion venait de config.json - entre
# 700 et 5000 ms - et ne regardait JAMAIS la pendule. En partie de 30 minutes
# c'est bien trop rapide ; en bullet d'une minute, c'est absurde : cinq
# secondes sur un coup, c'est un DOUZIEME de toute sa partie. Au bout de douze
# coups il aurait perdu au temps, et toi tu passes la partie a l'attendre.
#
# CE QUE FAIT CE FICHIER : il calcule le budget comme le ferait un joueur -
# a partir du TEMPS QUI RESTE et du nombre de coups qu'il pense encore devoir
# jouer, plus l'increment.
#
#       budget = temps_restant / coups_restants_estimes  +  0.7 x increment
#
# Avec deux garde-fous :
#   - jamais plus d'un dixieme du temps restant sur un seul coup ;
#   - jamais moins de 100 ms, sinon ca ne ressemble plus a rien.
#
# CE QUE CA DONNE, EN PRATIQUE :
#       1+0   (bullet)   environ 0,5 s par coup, et de moins en moins apres
#       3+2   (blitz)    environ 2 s
#       5+0   (blitz)    environ 2,6 s
#       10+5  (rapide)   environ 6,5 s
#       30+20 (longue)   8 s (le plafond : personne n'attend plus longtemps)
#       sans limite      on retombe sur tes reglages de config.json
#
# Ce fichier ne connait ni pygame ni le plateau : il ne fait que des nombres.
# C'est ce qui permet de le tester serieusement.
#
# AUCUNE FONCTION SUPPRIMEE : ce fichier n'existait pas avant.

COUPS_RESTANTS_MIN = 12       # en fin de partie on ne descend pas plus bas
COUPS_RESTANTS_MAX = 40       # en ouverture on prevoit large
PART_MAXIMALE = 0.10          # au plus un dixieme du temps restant sur un coup
BUDGET_PLANCHER_MS = 100

# CE N'EST PAS UN MOTEUR QUI JOUE POUR GAGNER AU TEMPS : c'est un adversaire, et
# EN FACE IL Y A QUELQU'UN QUI ATTEND. Une gestion de pendule "de tournoi"
# donnerait 45 secondes par coup en partie de 30 minutes - correct pour une
# machine, insupportable pour toi. On ne prend donc qu'un TIERS de la part
# calculee, et on plafonne a huit secondes.
FACTEUR_CONFORT = 0.35
BUDGET_PLAFOND_MS = 8000


def coups_restants_estimes(demi_coups_joues):
    """Combien de coups le moteur pense encore devoir jouer.

    En ouverture il prevoit large (40), puis de moins en moins : c'est ce qui
    fait qu'il ralentit au debut et accelere quand la pendule descend.
    """
    coups = max(0, int(demi_coups_joues)) // 2
    estime = COUPS_RESTANTS_MAX - coups * 0.8
    return int(max(COUPS_RESTANTS_MIN, min(COUPS_RESTANTS_MAX, estime)))


def budget_ms(temps_restant_s, increment_s=0, demi_coups_joues=0,
              defaut_ms=1500):
    """Le temps a passer sur CE coup, en millisecondes.

    temps_restant_s : ce qu'il reste au moteur a sa pendule. None ou 0 = pas de
                      pendule du tout : on rend `defaut_ms` et le rythme humain
                      de background_ai reprend la main, comme avant.
    """
    if not temps_restant_s or temps_restant_s <= 0:
        return int(max(BUDGET_PLANCHER_MS, defaut_ms))

    restants = coups_restants_estimes(demi_coups_joues)
    part = (temps_restant_s / float(restants)
            + 0.7 * float(increment_s or 0)) * FACTEUR_CONFORT

    # Garde-fou : on ne mise jamais plus d'un dixieme de ce qui reste. C'est ce
    # qui empeche de perdre au temps quand la pendule devient courte.
    part = min(part, temps_restant_s * PART_MAXIMALE + float(increment_s or 0) * 0.7)

    # Sous cinq secondes au chrono, on joue quasiment a vue : mieux vaut un
    # coup moyen tout de suite qu'un bon coup apres la chute du drapeau.
    if temps_restant_s < 5:
        part = min(part, temps_restant_s * 0.05)

    return int(max(BUDGET_PLANCHER_MS, min(part * 1000.0, BUDGET_PLAFOND_MS)))


def bornes_ms(temps_restant_s, increment_s=0, demi_coups_joues=0,
              defaut_min_ms=700, defaut_max_ms=5000):
    """(mini, maxi) pour le tirage au sort du rythme humain.

    On garde le hasard - c'est lui qui evite le rythme mecanique - mais on le
    recentre autour du budget de la cadence au lieu de bornes fixes.
    """
    if not temps_restant_s or temps_restant_s <= 0:
        return int(defaut_min_ms), int(defaut_max_ms)
    cible = budget_ms(temps_restant_s, increment_s, demi_coups_joues)
    mini = max(BUDGET_PLANCHER_MS, int(cible * 0.35))
    maxi = max(mini + 100, int(cible * 1.8))
    return mini, maxi


def temps_moteur_ms(budget, plafond_ms=3000):
    """Ce qu'on laisse VRAIMENT calculer a Stockfish.

    Le reste du budget est une pause d'attente : c'est ce qui lui donne un
    rythme humain sans lui faire perdre de la force. On plafonne quand meme,
    parce qu'au-dela le gain devient invisible a ces niveaux.
    """
    return int(max(50, min(int(budget), int(plafond_ms))))


def description(temps_restant_s, increment_s=0):
    """Une ligne lisible pour le journal : a quoi s'attendre a cette cadence."""
    if not temps_restant_s:
        return "sans pendule : rythme de config.json"
    debut = budget_ms(temps_restant_s, increment_s, 0) / 1000.0
    milieu = budget_ms(temps_restant_s * 0.6, increment_s, 30) / 1000.0
    return ("pendule %.0f s + %d s : environ %.1f s par coup en ouverture, "
            "%.1f s au milieu" % (temps_restant_s, increment_s or 0, debut,
                                  milieu))
