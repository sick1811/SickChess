# cache_manager.py - V6
# Gestion centralisee des options de performance de Stockfish (Hash, Threads, MultiPV).
#
# CE QUI CHANGE PAR RAPPORT A V5 (bug m3 du rapport) :
#   - En V5, CacheManager posait Hash=512 / Threads=2, puis set_custom_elo() remettait
#     Hash=16 / Threads=1 juste apres. Les deux se contredisaient.
#     Desormais c'est CacheManager qui fait autorite : engine.set_custom_elo() ne touche
#     plus jamais au Hash ni aux Threads, il ne s'occupe que du niveau de jeu.
#   - Le nombre de threads s'adapte au processeur au lieu d'etre fige a 2.
#   - Le Hash est plafonne pour ne pas demander 512 Mo sur une machine qui n'en a pas.
#
# 31/10 (menage) : get_hash_size et get_threads, jamais appelees, sont
# retirees ; les autres sont conservees.

import os


class CacheManager:
    """Gestion centralisee du cache Stockfish (512 MB recommande)."""

    def __init__(self, hash_size_mb=512, threads=None):
        # Valeur par defaut a 512 MB (conforme a la demande de l'utilisateur),
        # mais plafonnee si la machine ne peut pas suivre.
        self.hash_size_mb = self._plafonner_hash(hash_size_mb)
        self.threads = self._choisir_threads(threads)
        self.multipv = 1
        self._log("CacheManager initialise avec Hash = %d MB, Threads = %d"
                  % (self.hash_size_mb, self.threads))

    # ------------------------------------------------------------------ interne

    def _log(self, message):
        """Log interne (visible dans le launcher)."""
        print("[CACHE MANAGER] " + str(message))

    def _memoire_disponible_mb(self):
        """Estime la RAM totale de la machine, sans dependance externe."""
        try:
            # Linux / macOS
            pages = os.sysconf("SC_PHYS_PAGES")
            taille = os.sysconf("SC_PAGE_SIZE")
            return int(pages * taille / (1024 * 1024))
        except (ValueError, OSError, AttributeError):
            pass
        try:
            # Windows
            import ctypes

            class _MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = _MemoryStatusEx()
            stat.dwLength = ctypes.sizeof(_MemoryStatusEx)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return int(stat.ullTotalPhys / (1024 * 1024))
        except Exception:
            return 0

    def _plafonner_hash(self, demande):
        """Ne jamais reserver plus du quart de la RAM de la machine."""
        demande = max(16, int(demande))
        total = self._memoire_disponible_mb()
        if total <= 0:
            return demande
        plafond = max(16, total // 4)
        if demande > plafond:
            self._log("Hash ramene de %d MB a %d MB (RAM detectee : %d MB)"
                      % (demande, plafond, total))
            return plafond
        return demande

    def _choisir_threads(self, demande):
        """Laisse toujours un coeur libre pour l'affichage du jeu."""
        if demande is not None:
            return max(1, int(demande))
        coeurs = os.cpu_count() or 2
        return max(1, min(4, coeurs - 1))

    # ------------------------------------------------------------------ lecture

    def get_uci_set_hash_command(self):
        """Retourne la commande UCI pour definir le Hash."""
        return "setoption name Hash value %d" % self.hash_size_mb

    def get_recommended_options(self):
        """Retourne toutes les options UCI recommandees pour un bon niveau."""
        return [
            self.get_uci_set_hash_command(),
            "setoption name Threads value %d" % self.threads,
            "setoption name MultiPV value %d" % self.multipv,
        ]

    # ------------------------------------------------------------------ ecriture

    def set_hash_size(self, hash_size_mb):
        """Change la taille du cache (plafonnee selon la RAM)."""
        self.hash_size_mb = self._plafonner_hash(hash_size_mb)
        return self.hash_size_mb

    def set_threads(self, threads):
        """Change le nombre de threads."""
        self.threads = self._choisir_threads(threads)
        return self.threads

    def apply_to_engine(self, engine):
        """Applique les options de performance au moteur Stockfish."""
        self._log("Application des options de performance au moteur Stockfish...")
        # engine expose maintenant send_command() en public ; _send_command reste
        # disponible pour ne rien casser dans l'ancien code.
        envoyer = getattr(engine, "send_command", None) or engine._send_command
        for option in self.get_recommended_options():
            envoyer(option)
        # V7.2 : le moteur tient a jour le nombre de threads qu'il a recu
        # (engine.regler_threads n'envoie rien si la valeur ne change pas).
        try:
            engine.threads_courant = self.threads
        except Exception:
            pass
        self._log("Cache = %d MB, Threads = %d" % (self.hash_size_mb, self.threads))


# Instance unique pour toute l'application (toile d'araignee)
_cache_manager_instance = None


def get_cache_manager(hash_size_mb=None, threads=None):
    """Fonction d'acces centralisee (importable partout sans duplication)."""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager(
            hash_size_mb if hash_size_mb is not None else 512, threads
        )
    else:
        if hash_size_mb is not None:
            _cache_manager_instance.set_hash_size(hash_size_mb)
        if threads is not None:
            _cache_manager_instance.set_threads(threads)
    return _cache_manager_instance
