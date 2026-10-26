"""Ce qui tourne autour de l'agent : GPU RunPod, IA locale, serveur OpenCode en cours, catalogue et test des MCP."""
import base64
import json
import os
import shlex
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import chemins

RUNPOD_API = "https://rest.runpod.io/v1"
_cache = {}


def _memo(cle, duree, fonction):
    maintenant = time.time()
    if cle in _cache and maintenant - _cache[cle][0] < duree:
        return _cache[cle][1]
    valeur = fonction()
    _cache[cle] = (maintenant, valeur)
    return valeur


# ---------- GPU RunPod ----------

def _cle_runpod():
    if not chemins.RUNPOD_ENV.exists():
        return None
    for ligne in chemins.RUNPOD_ENV.read_text(encoding="utf-8-sig").splitlines():
        nom, _, valeur = ligne.partition("=")
        if nom.strip() == "RUNPOD_API_KEY" and valeur.strip():
            return valeur.strip().strip('"')
    return None


def _runpod(methode, chemin):
    cle = _cle_runpod()
    if not cle:
        raise RuntimeError("clé RunPod absente")
    requete = urllib.request.Request(
        RUNPOD_API + chemin, method=methode, data=b"{}" if methode == "POST" else None,
        # Sans User-Agent, Cloudflare (devant l'API RunPod) répond 403.
        headers={"Authorization": f"Bearer {cle}", "Content-Type": "application/json", "User-Agent": "atelier/1.0"})
    with urllib.request.urlopen(requete, timeout=20) as reponse:
        corps = reponse.read()
        return json.loads(corps) if corps else None


def etat_gpu(forcer=False):
    def lire():
        try:
            pods = _runpod("GET", "/pods") or []
        except Exception as erreur:  # noqa: BLE001
            return {"etat": "inconnu", "detail": str(erreur)[:200], "pods": []}
        liste = [{"id": p.get("id"), "nom": p.get("name") or p.get("id"), "allume": p.get("desiredStatus") == "RUNNING",
                  "prix": p.get("costPerHr"), "gpu": (p.get("machine") or {}).get("gpuDisplayName") or p.get("gpuTypeId") or "",
                  "depuis": p.get("lastStartedAt") or ""} for p in pods]
        allumes = [p for p in liste if p["allume"]]
        return {"etat": "allume" if allumes else "eteint", "pods": liste,
                "prix_heure": round(sum(p["prix"] or 0 for p in allumes), 2)}
    if forcer:
        _cache.pop("gpu", None)
    return _memo("gpu", 30, lire)


def arreter_gpu():
    resultats = []
    for pod in etat_gpu(forcer=True)["pods"]:
        if pod["allume"]:
            try:
                _runpod("POST", f"/pods/{pod['id']}/stop")
                resultats.append({"nom": pod["nom"], "ok": True})
            except Exception as erreur:  # noqa: BLE001
                resultats.append({"nom": pod["nom"], "ok": False, "detail": str(erreur)[:200]})
    _cache.pop("gpu", None)
    return resultats


# ---------- IA locale ----------

def etat_ia_locale():
    def lire():
        try:
            with urllib.request.urlopen(chemins.IA_LOCALE + "/running", timeout=3) as reponse:
                en_cours = json.loads(reponse.read()).get("running") or []
            with urllib.request.urlopen(chemins.IA_LOCALE + "/v1/models", timeout=3) as reponse:
                modeles = [{"id": m.get("id"), "nom": m.get("name") or m.get("id")} for m in json.loads(reponse.read()).get("data") or []]
            return {"etat": "prete", "charges": [m.get("model") for m in en_cours], "modeles": modeles}
        except Exception:  # noqa: BLE001
            return {"etat": "arretee", "charges": [], "modeles": []}
    return _memo("ia", 10, lire)


# ---------- Serveur OpenCode en cours ----------

def session_opencode():
    if not chemins.SESSION.exists():
        return None
    try:
        session = json.loads(chemins.SESSION.read_text(encoding="utf-8"))
        urllib.request.urlopen(session["url"] + "/", timeout=2).close()
        return session
    except Exception:  # noqa: BLE001
        return None


def recharger_opencode():
    """Fait relire la config à l'agent ouvert, sans le fermer. Renvoie un message pour l'interface."""
    session = session_opencode()
    if not session:
        return {"recharge": False, "message": "Agent fermé : la modification sera prise en compte à son prochain lancement."}
    auth = "Basic " + base64.b64encode(f"opencode:{session['mot_de_passe']}".encode()).decode()
    try:
        requete = urllib.request.Request(session["url"] + "/api/location/reload", method="POST", data=b"",
                                         headers={"Authorization": auth})
        urllib.request.urlopen(requete, timeout=60).close()
        return {"recharge": True, "message": "Agent rechargé : la modification est déjà active."}
    except Exception as erreur:  # noqa: BLE001
        return {"recharge": False, "message": f"Écrit, mais le rechargement de l'agent a échoué ({erreur}). Relancez l'agent."}


# ---------- MCP ----------

def _vrai_profil(env):
    profil = os.environ.get("VRAI_USERPROFILE") or str(Path.home())
    env.setdefault("USERPROFILE", profil)
    env.setdefault("HOME", profil)
    return env


def catalogue_mcp(installes):
    """Vos MCP de C:\\MCP qu'on peut ajouter, avec la commande trouvée dans la config de Claude Code."""
    try:
        descriptions = json.loads(chemins.CATALOGUE_MCP.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        descriptions = {}
    try:
        claude = json.loads(chemins.CLAUDE_JSON.read_text(encoding="utf-8")).get("mcpServers") or {}
    except Exception:  # noqa: BLE001
        claude = {}
    liste = []
    for nom, info in descriptions.items():
        if nom.startswith("_") or not isinstance(info, dict) or info.get("pas_mcp"):
            continue
        source = "claude" if nom in claude else ("lancement" if info.get("lancement") else None)
        liste.append({"nom": nom, "categorie": info.get("categorie", ""), "description": info.get("description", ""),
                      "ajoutable": source is not None, "installe": nom in installes,
                      "variables": list(((claude.get(nom) or {}).get("env") or {}).keys())})
    return liste


def config_depuis_catalogue(nom):
    """Config OpenCode d'un MCP du catalogue (valeurs des variables incluses : ne jamais renvoyer au navigateur)."""
    claude = json.loads(chemins.CLAUDE_JSON.read_text(encoding="utf-8")).get("mcpServers") or {}
    if nom in claude:
        source = claude[nom]
        if source.get("type") in ("http", "sse") or source.get("url"):
            conf = {"type": "remote", "url": source["url"]}
            if source.get("headers"):
                conf["headers"] = dict(source["headers"])
            return conf
        conf = {"type": "local", "command": [source["command"], *(source.get("args") or [])]}
        conf["environment"] = _vrai_profil(dict(source.get("env") or {}))
        return conf
    info = json.loads(chemins.CATALOGUE_MCP.read_text(encoding="utf-8")).get(nom) or {}
    if info.get("lancement"):
        return {"type": "local", "command": shlex.split(info["lancement"], posix=False), "environment": _vrai_profil({})}
    raise ValueError(f"Pas de commande connue pour « {nom} ».")


def masquer_mcp(conf):
    """Version affichable : variables et en-têtes sans leurs valeurs."""
    vue = {k: v for k, v in conf.items() if k not in ("environment", "headers")}
    vue["variables"] = list((conf.get("environment") or {}).keys())
    vue["entetes"] = list((conf.get("headers") or {}).keys())
    return vue


def tester_mcp(conf, delai=None):
    """Démarre le MCP, fait la poignée de main MCP et compte ses outils. Rien n'est gardé ensuite."""
    if conf.get("type") != "local":
        return {"ok": None, "message": "Test automatique disponible seulement pour les MCP locaux."}
    delai = delai or max(15, ((conf.get("timeout") or {}).get("startup") or 60000) // 1000)
    env = dict(os.environ)
    env.update(conf.get("environment") or {})
    try:
        processus = subprocess.Popen(conf["command"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, env=env, cwd=conf.get("cwd") or None,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as erreur:  # noqa: BLE001
        return {"ok": False, "message": f"Impossible de démarrer : {erreur}"}
    reponses = {}

    def lire():
        for brut in processus.stdout:
            try:
                message = json.loads(brut.decode("utf-8", "replace"))
            except ValueError:
                continue
            if isinstance(message, dict) and "id" in message:
                reponses[message["id"]] = message

    def envoyer(message):
        processus.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
        processus.stdin.flush()

    threading.Thread(target=lire, daemon=True).start()
    try:
        envoyer({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "atelier", "version": "1.0"}}})
        fin = time.time() + delai
        while 1 not in reponses and time.time() < fin and processus.poll() is None:
            time.sleep(0.1)
        if 1 not in reponses:
            return {"ok": False, "message": "Le MCP n'a pas répondu (démarrage trop long ou commande incorrecte)."}
        nom = ((reponses[1].get("result") or {}).get("serverInfo") or {}).get("name", "")
        envoyer({"jsonrpc": "2.0", "method": "notifications/initialized"})
        envoyer({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        while 2 not in reponses and time.time() < fin and processus.poll() is None:
            time.sleep(0.1)
        outils = ((reponses.get(2) or {}).get("result") or {}).get("tools") or []
        return {"ok": True, "message": f"Connecté{' (' + nom + ')' if nom else ''} : {len(outils)} outil(s).",
                "outils": [o.get("name") for o in outils][:300]}
    except Exception as erreur:  # noqa: BLE001
        return {"ok": False, "message": f"Échec du test : {erreur}"}
    finally:
        try:
            processus.kill()
        except Exception:  # noqa: BLE001
            pass
