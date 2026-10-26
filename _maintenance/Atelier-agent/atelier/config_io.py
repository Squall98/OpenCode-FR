"""Lecture, écriture vérifiée et sauvegardes des fichiers de l'agent (opencode.json, AGENTS.md, skills).

Règle d'or : on relit toujours le fichier avant de le modifier, on vérifie la config candidate avec OpenCode,
on sauvegarde l'ancienne version, puis seulement on écrit. Si OpenCode refuse, rien n'est écrit.
"""
import copy
import difflib
import hashlib
import json
import shutil
import threading
from datetime import datetime
from pathlib import Path

import chemins
import verification

VERROU = threading.Lock()
GARDER = 20  # versions gardées par fichier


class Refus(Exception):
    """Modification refusée : config changée entre-temps, ou rejetée par OpenCode."""

    def __init__(self, message, erreurs=None, statut=400):
        super().__init__(message)
        self.erreurs = erreurs or []
        self.statut = statut


def empreinte(octets):
    return hashlib.sha256(octets).hexdigest()[:16]


def lire_config():
    octets = chemins.CONFIG.read_bytes()
    texte = octets.decode("utf-8-sig")
    return json.loads(texte), empreinte(octets), "\r\n" in texte


def version_config():
    return empreinte(chemins.CONFIG.read_bytes())


def _serialiser(obj, crlf):
    texte = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    return (texte.replace("\n", "\r\n") if crlf else texte).encode("utf-8")


# ---------- Sauvegardes ----------

def _index():
    fichier = chemins.SAUVEGARDES / "index.json"
    if fichier.exists():
        return json.loads(fichier.read_text(encoding="utf-8"))
    return []


def _ecrire_index(entrees):
    chemins.SAUVEGARDES.mkdir(parents=True, exist_ok=True)
    (chemins.SAUVEGARDES / "index.json").write_text(json.dumps(entrees, ensure_ascii=False, indent=2), encoding="utf-8")


def sauvegarder(cible: Path, genre, resume):
    """Copie `cible` avant modification ; garde les GARDER dernières versions de ce genre."""
    if not cible.exists():
        return None
    chemins.SAUVEGARDES.mkdir(parents=True, exist_ok=True)
    maintenant = datetime.now()
    ident = maintenant.strftime("%Y%m%d-%H%M%S-%f")
    copie = chemins.SAUVEGARDES / f"{ident}-{cible.name}"
    shutil.copy2(cible, copie)
    if empreinte(copie.read_bytes()) != empreinte(cible.read_bytes()):
        raise Refus("La sauvegarde ne correspond pas à l'original : rien n'a été modifié.")
    entrees = _index()
    entrees.insert(0, {"id": ident, "date": maintenant.strftime("%d/%m/%Y %H:%M:%S"), "genre": genre,
                       "cible": str(cible), "fichier": copie.name, "resume": resume, "taille": copie.stat().st_size})
    meme_genre = [e for e in entrees if e["genre"] == genre]
    for vieille in meme_genre[GARDER:]:
        (chemins.SAUVEGARDES / vieille["fichier"]).unlink(missing_ok=True)
        entrees.remove(vieille)
    _ecrire_index(entrees)
    return ident


def liste_sauvegardes():
    return _index()


def comparer(ident):
    entree = next((e for e in _index() if e["id"] == ident), None)
    if not entree:
        raise Refus("Sauvegarde introuvable.", statut=404)
    ancien = (chemins.SAUVEGARDES / entree["fichier"]).read_text(encoding="utf-8-sig").splitlines()
    cible = Path(entree["cible"])
    actuel = cible.read_text(encoding="utf-8-sig").splitlines() if cible.exists() else []
    return "\n".join(difflib.unified_diff(ancien, actuel, "sauvegarde du " + entree["date"], "version actuelle", lineterm=""))


def restaurer(ident):
    entree = next((e for e in _index() if e["id"] == ident), None)
    if not entree:
        raise Refus("Sauvegarde introuvable.", statut=404)
    cible = Path(entree["cible"])
    if entree.get("dossier"):  # skill mise de côté : on la remet à sa place
        with VERROU:
            if cible.exists():
                raise Refus(f"Une skill « {cible.name} » existe déjà : renommez-la avant de restaurer celle-ci.")
            shutil.move(str(chemins.SAUVEGARDES / entree["fichier"]), str(cible))
            _ecrire_index([e for e in _index() if e["id"] != ident])
        return {"ok": True}
    contenu = (chemins.SAUVEGARDES / entree["fichier"]).read_bytes()
    if entree["genre"] == "config":
        config = json.loads(contenu.decode("utf-8-sig"))
        return modifier_config(lambda c: (c.clear(), c.update(config)), f"Retour à la version du {entree['date']}")
    with VERROU:
        sauvegarder(cible, entree["genre"], f"Avant retour à la version du {entree['date']}")
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_bytes(contenu)
    return {"ok": True}


# ---------- Écritures ----------

def modifier_config(changement, resume, version=None):
    """Applique `changement(config)` sur la config relue, la fait vérifier par OpenCode, sauvegarde, écrit."""
    with VERROU:
        config, actuelle, crlf = lire_config()
        if version and version != actuelle:
            raise Refus("La config a été modifiée ailleurs depuis l'ouverture de cette page. Rechargez la page.",
                        statut=409)
        nouvelle = copy.deepcopy(config)
        changement(nouvelle)
        if nouvelle == config:
            return {"ok": True, "inchange": True, "version": actuelle}
        resultat = verification.verifier(nouvelle, str(chemins.EXE))
        if not resultat.ok:
            raise Refus("OpenCode refuse cette modification : rien n'a été écrit.",
                        resultat.erreurs or [{"chemin": "$", "message": resultat.detail}])
        sauvegarder(chemins.CONFIG, "config", resume)
        octets = _serialiser(nouvelle, crlf)
        temporaire = chemins.CONFIG.with_suffix(".json.atelier-ecriture")
        temporaire.write_bytes(octets)
        temporaire.replace(chemins.CONFIG)
        return {"ok": True, "version": empreinte(octets)}


def ecrire_texte(cible: Path, texte, genre, resume):
    """AGENTS.md et skills : pas de vérification OpenCode (texte libre), mais toujours une sauvegarde."""
    with VERROU:
        sauvegarder(cible, genre, resume)
        cible.parent.mkdir(parents=True, exist_ok=True)
        ancien = cible.read_bytes() if cible.exists() else b""
        crlf = b"\r\n" in ancien
        texte = texte.replace("\r\n", "\n")
        cible.write_bytes((texte.replace("\n", "\r\n") if crlf else texte).encode("utf-8"))
    return {"ok": True}


def mettre_de_cote(dossier: Path, genre, resume):
    """« Supprimer » une skill = la ranger dans les sauvegardes (jamais d'effacement définitif)."""
    with VERROU:
        chemins.SAUVEGARDES.mkdir(parents=True, exist_ok=True)
        ident = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        destination = chemins.SAUVEGARDES / f"{ident}-{dossier.name}"
        shutil.move(str(dossier), str(destination))
        entrees = _index()
        entrees.insert(0, {"id": ident, "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "genre": genre,
                           "cible": str(dossier), "fichier": destination.name, "resume": resume, "taille": 0, "dossier": True})
        _ecrire_index(entrees)
