"""Emplacements utilisés par l'Atelier.

ATELIER_BASE permet de travailler sur une autre installation d'OpenCode (l'environnement de test) :
    set ATELIER_BASE=D:\\IA LOCAL\\_maintenance\\OpenCode-web-test
"""
import os
from pathlib import Path

ATELIER = Path(__file__).resolve().parent.parent          # D:\IA LOCAL\_maintenance\Atelier-agent
BASE = Path(os.environ.get("ATELIER_BASE", r"D:\IA LOCAL"))
TEST = BASE.resolve() != Path(r"D:\IA LOCAL").resolve()

CONFIG_DIR = BASE / "config" / "opencode"
CONFIG = CONFIG_DIR / "opencode.json"
CONSIGNES = CONFIG_DIR / "AGENTS.md"
SKILLS = CONFIG_DIR / "skills"
EXE = BASE / "opencode" / "node_modules" / "@opencode" / "cli" / "bin" / "opencode.exe"

SAUVEGARDES = ATELIER / ("sauvegardes-test" if TEST else "sauvegardes")
ETAT = ATELIER / "etat"
WEB = ATELIER / "atelier" / "web"
# Fichier écrit par le lanceur de la fenêtre de l'agent : adresse et mot de passe du serveur OpenCode en cours,
# pour recharger la config sans le fermer. L'agent n'a pas le droit de lire _maintenance.
SESSION = ETAT / ("opencode-test.json" if TEST else "opencode.json")

RUNPOD_ENV = Path(os.environ.get("ATELIER_RUNPOD", r"D:\IA LOCAL\_maintenance\RunPod-GPU")) / ".env"
IA_LOCALE = "http://127.0.0.1:8090"
CATALOGUE_MCP = Path(r"C:\MCP\descriptions.json")
# Lancé par la fenêtre de l'agent, le « profil » peut être celui de l'agent : on vise le vrai profil de Nykaro.
CLAUDE_JSON = Path(os.environ.get("VRAI_USERPROFILE") or Path.home()) / ".claude.json"

PORT = int(os.environ.get("ATELIER_PORT", "4111" if TEST else "4110"))
EDGE = next((p for p in (Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
                         Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe")) if p.exists()), None)
PROFIL_FENETRE = ETAT / ("fenetre-edge-test" if TEST else "fenetre-edge")
