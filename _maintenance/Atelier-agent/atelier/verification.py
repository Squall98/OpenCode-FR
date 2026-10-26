"""Vérifie une config OpenCode candidate avec OpenCode lui-même, avant de l'écrire.

OpenCode ne refuse pas une config fautive : il ignore en silence l'élément invalide et l'écrit seulement dans son
journal (« configuration normalization diagnostic »). On démarre donc un OpenCode jetable sur une copie de la config
(dossiers temporaires, MCP désactivés pour qu'aucun ne se lance), on lui fait charger la config, on lit son journal,
puis on l'arrête.
"""
import base64
import json
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.request
from pathlib import Path


class Resultat:
    def __init__(self, ok, erreurs, agents=None, detail=""):
        self.ok = ok
        self.erreurs = erreurs  # liste de {"chemin": "$.agents.x.mode", "message": "..."}
        self.agents = agents or []
        self.detail = detail

    def en_dict(self):
        return {"ok": self.ok, "erreurs": self.erreurs, "agents": self.agents, "detail": self.detail}


def _copie_sans_mcp(config):
    """Copie de la config où tous les MCP sont désactivés : leur format est vérifié, mais aucun ne démarre."""
    copie = json.loads(json.dumps(config))
    for serveur in (copie.get("mcp") or {}).get("servers", {}).values():
        if isinstance(serveur, dict):
            serveur["disabled"] = True
    return copie


def _lire_diagnostics(texte):
    erreurs = []
    for ligne in texte.splitlines():
        if "normalization diagnostic" not in ligne:
            continue
        chemin = re.search(r'path=("?)([^"\s]+)\1', ligne)
        action = re.search(r'action="([^"]*)"', ligne) or re.search(r"action=(\S+)", ligne)
        erreurs.append({
            "chemin": chemin.group(2) if chemin else "$",
            "message": action.group(1) if action else ligne.strip()[:300],
        })
    return erreurs


def verifier(config, exe, delai=40):
    """Renvoie un Resultat. `config` est le dict complet à écrire, `exe` le chemin d'opencode.exe."""
    if not Path(exe).exists():
        return Resultat(False, [], detail=f"OpenCode introuvable : {exe}")
    dossier = Path(tempfile.mkdtemp(prefix="atelier-verif-"))
    processus = None
    try:
        (dossier / "config" / "opencode").mkdir(parents=True)
        (dossier / "config" / "opencode" / "opencode.json").write_text(
            json.dumps(_copie_sans_mcp(config), ensure_ascii=False, indent=2), encoding="utf-8")
        for nom in ("data", "state", "cache", "home"):
            (dossier / nom).mkdir()
        mot_de_passe = secrets.token_hex(16)
        env = dict(os.environ)
        env.update({
            "XDG_CONFIG_HOME": str(dossier / "config"), "XDG_DATA_HOME": str(dossier / "data"),
            "XDG_STATE_HOME": str(dossier / "state"), "XDG_CACHE_HOME": str(dossier / "cache"),
            "USERPROFILE": str(dossier / "home"), "HOME": str(dossier / "home"),
            "OPENCODE_SERVER_PASSWORD": mot_de_passe,
        })
        processus = subprocess.Popen(
            [exe, "serve", "--hostname", "127.0.0.1", "--port", "0", "--print-logs", "--log-level", "warn"],
            cwd=str(dossier), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        sortie = []
        adresse = {}

        def lire():
            for brut in processus.stdout:
                ligne = brut.decode("utf-8", "replace")
                sortie.append(ligne)
                trouve = re.search(r"listening on (http://127\.0\.0\.1:\d+)", ligne)
                if trouve:
                    adresse["url"] = trouve.group(1)

        threading.Thread(target=lire, daemon=True).start()
        fin = time.time() + delai
        while "url" not in adresse and time.time() < fin and processus.poll() is None:
            time.sleep(0.1)
        if "url" not in adresse:
            return Resultat(False, [], detail="OpenCode n'a pas démarré pour vérifier la config :\n" + "".join(sortie)[-1500:])
        auth = "Basic " + base64.b64encode(f"opencode:{mot_de_passe}".encode()).decode()
        # La config se charge à la première requête : on redemande jusqu'à voir « build », toujours présent.
        agents = []
        while time.time() < fin and "build" not in agents:
            requete = urllib.request.Request(adresse["url"] + "/api/agent", headers={"Authorization": auth})
            with urllib.request.urlopen(requete, timeout=delai) as reponse:
                donnees = json.loads(reponse.read() or b"[]")
            liste = donnees.get("data", donnees) if isinstance(donnees, dict) else donnees
            agents = [a.get("id") for a in liste if isinstance(a, dict)]
            if "build" not in agents:
                time.sleep(0.3)
        if "build" not in agents:
            return Resultat(False, [], detail="OpenCode n'a pas chargé la config à temps.")
        time.sleep(0.5)  # laisser le journal arriver
        erreurs = _lire_diagnostics("".join(sortie))
        # Un agent demandé mais absent de la réponse = rejeté par OpenCode, même sans message lisible.
        for nom in (config.get("agents") or {}):
            if nom not in agents and not any(f".agents.{nom}" in e["chemin"] for e in erreurs):
                erreurs.append({"chemin": f"$.agents.{nom}", "message": "agent refusé par OpenCode"})
        return Resultat(not erreurs, erreurs, agents)
    except Exception as erreur:  # noqa: BLE001 - toute panne de vérification bloque l'écriture
        return Resultat(False, [], detail=f"Vérification impossible : {erreur}")
    finally:
        if processus and processus.poll() is None:
            processus.kill()
            try:
                processus.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
        shutil.rmtree(dossier, ignore_errors=True)


if __name__ == "__main__":
    import sys
    exe = sys.argv[2] if len(sys.argv) > 2 else r"D:\IA LOCAL\opencode\node_modules\@opencode\cli\bin\opencode.exe"
    conf = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(verifier(conf, exe).en_dict(), ensure_ascii=False, indent=2))
