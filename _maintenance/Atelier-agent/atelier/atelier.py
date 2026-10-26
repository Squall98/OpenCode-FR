"""Atelier de l'agent : serveur local (127.0.0.1) qui lit et modifie la config d'OpenCode pour l'interface.

Lancement : "C:\\Program Files\\Python314\\pythonw.exe" atelier.py   (fait par « Atelier.vbs » ou la fenêtre de l'agent)
Sécurité : toute modification exige le jeton glissé dans la page servie ; l'en-tête Host doit être 127.0.0.1.
Le serveur s'arrête seul après quelques minutes sans aucune page ouverte (ni Atelier, ni fenêtre de l'agent).
"""
import json
import mimetypes
import re
import secrets
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agents  # noqa: E402
import chemins  # noqa: E402
import config_io  # noqa: E402
import services  # noqa: E402
from config_io import Refus  # noqa: E402

JETON = secrets.token_urlsafe(24)
DERNIERE_ACTIVITE = [time.time()]
INACTIVITE_MAX = 300  # secondes
ORIGINES_OPENCODE = {"http://127.0.0.1:4096", "http://127.0.0.1:4097"}
PROTEGE = [r"(D:/IA LOCAL/)?(_maintenance/OpenCode-web-test/)?(config|opencode|\.donnees|_maintenance)/\*"]


def _protegee(regle):
    if regle.get("action") == "external_directory" and regle.get("resource") == "*" and regle.get("effect") == "deny":
        return True
    return (regle.get("action") in ("edit", "read") and regle.get("effect") == "deny"
            and any(re.fullmatch(m, regle.get("resource", "")) for m in PROTEGE))


# ---------- Lecture de tout l'état pour l'interface ----------

def _modeles_disponibles(config):
    liste = []
    for fournisseur, info in (config.get("providers") or {}).items():
        for ident, modele in (info.get("models") or {}).items():
            liste.append({"id": f"{fournisseur}/{ident}", "nom": modele.get("name") or ident,
                          "fournisseur": info.get("name") or fournisseur,
                          "contexte": (modele.get("limit") or {}).get("context")})
    return liste


def _lire_skill(dossier: Path):
    fichier = dossier / "SKILL.md"
    texte = fichier.read_text(encoding="utf-8-sig") if fichier.exists() else ""
    description, contenu = "", texte
    entete = re.match(r"---\r?\n(.*?)\r?\n---\r?\n?(.*)", texte, re.S)
    if entete:
        contenu = entete.group(2).lstrip("\r\n")
        trouve = re.search(r"^description:\s*(.*)$", entete.group(1), re.M)
        description = trouve.group(1).strip() if trouve else ""
    return {"nom": dossier.name, "description": description, "contenu": contenu}


def tout():
    config, version, _ = config_io.lire_config()
    globales = config.get("permissions") or []
    skills = sorted((_lire_skill(d) for d in chemins.SKILLS.iterdir() if d.is_dir()), key=lambda s: s["nom"]) \
        if chemins.SKILLS.exists() else []
    autorisees = {r["resource"] for r in globales if r.get("action") == "skill" and r.get("effect") == "allow"}
    for skill in skills:
        skill["autorisee"] = skill["nom"] in autorisees or "*" in autorisees
    mcp = (config.get("mcp") or {}).get("servers") or {}
    return {
        "version": version, "test": chemins.TEST, "base": str(chemins.BASE),
        "defaut": config.get("default_agent", "build"),
        "modele": config.get("model") if isinstance(config.get("model"), str)
        else "/".join(filter(None, [(config.get("model") or {}).get("providerID"), (config.get("model") or {}).get("model")])),
        "modeles": _modeles_disponibles(config),
        "agents": agents.vue_agents(config), "droits": agents.DROITS,
        "mcp": [{"nom": n, "actif": not s.get("disabled"), **services.masquer_mcp(s)} for n, s in mcp.items()],
        "commandes": [{"nom": n, **c} for n, c in (config.get("commands") or {}).items()],
        "skills": skills,
        "consignes": chemins.CONSIGNES.read_text(encoding="utf-8-sig") if chemins.CONSIGNES.exists() else "",
        "securite": [{**r, "protegee": _protegee(r)} for r in globales],
        "politiques": config.get("policies") or [],
        "sauvegardes": config_io.liste_sauvegardes(),
    }


# ---------- Modifications ----------

def _apres(resultat):
    """Après une écriture réussie : recharger l'agent ouvert et dire ce qu'il en est."""
    if resultat.get("inchange"):
        return {**resultat, "message": "Rien n'a changé."}
    return {**resultat, **services.recharger_opencode()}


def enregistrer_agent(corps):
    ident, ancien = corps["id"].strip(), (corps.get("ancien_id") or corps["id"]).strip()
    if ident in agents.INTERNES:
        raise Refus("Les agents internes d'OpenCode ne se modifient pas.")
    if ident not in agents.ORIGINE and not agents.nom_valide(ident):
        raise Refus("Nom d'agent : lettres minuscules, chiffres et tirets seulement (ex. relecteur-web).")

    def changement(config):
        confs = config.setdefault("agents", {})
        if ancien != ident:
            if ident in confs or ident in agents.ORIGINE:
                raise Refus(f"Un agent « {ident} » existe déjà.")
            _renommer(config, ancien, ident)
        conf = dict(confs.get(ident) or {})
        for champ in ("description", "system", "model", "color", "mode"):
            if champ in corps:
                valeur = (corps[champ] or "").strip() if isinstance(corps[champ], str) else corps[champ]
                if valeur:
                    conf[champ] = valeur
                else:
                    conf.pop(champ, None)
        if ident in agents.ORIGINE and conf.get("mode") == agents.ORIGINE[ident]["mode"]:
            conf.pop("mode")
        if ident in agents.ORIGINE and conf.get("description") == agents.ORIGINE[ident]["resume"]:
            conf.pop("description")
        if corps.get("disabled"):
            conf["disabled"] = True
        else:
            conf.pop("disabled", None)
        if "permissions_expert" in corps:
            conf["permissions"] = corps["permissions_expert"]
            if not conf["permissions"]:
                conf.pop("permissions")
        elif "droits" in corps:
            agents.appliquer_droits(conf, corps["droits"])
        if conf:
            confs[ident] = conf
        else:
            confs.pop(ident, None)
    return _apres(config_io.modifier_config(changement, f"Agent « {ident} » enregistré", corps.get("version")))


def _renommer(config, ancien, nouveau):
    confs = config["agents"]
    confs[nouveau] = confs.pop(ancien)
    if config.get("default_agent") == ancien:
        config["default_agent"] = nouveau
    for commande in (config.get("commands") or {}).values():
        if commande.get("agent") == ancien:
            commande["agent"] = nouveau
    for conf in confs.values():
        for regle in conf.get("permissions") or []:
            if regle.get("action") == "subagent" and regle.get("resource") == ancien:
                regle["resource"] = nouveau


def supprimer_agent(corps):
    ident = corps["id"]
    if ident in agents.ORIGINE or ident in agents.INTERNES:
        raise Refus("Les agents d'OpenCode ne se suppriment pas ; vous pouvez seulement les désactiver.")

    def changement(config):
        confs = config.get("agents") or {}
        if ident not in confs:
            raise Refus("Agent introuvable.", statut=404)
        confs.pop(ident)
        if config.get("default_agent") == ident:
            config["default_agent"] = "build"
        for commande in (config.get("commands") or {}).values():
            if commande.get("agent") == ident:
                commande.pop("agent")
        for conf in confs.values():
            if conf.get("permissions"):
                conf["permissions"] = [r for r in conf["permissions"] if not (r.get("action") == "subagent" and r.get("resource") == ident)]
    return _apres(config_io.modifier_config(changement, f"Agent « {ident} » supprimé", corps.get("version")))


def _nouvel_identifiant(config, nom):
    base = agents.identifiant(nom)
    existants = set(config.get("agents") or {}) | set(agents.ORIGINE) | set(agents.INTERNES)
    ident, n = base, 2
    while ident in existants:
        ident, n = f"{base}-{n}", n + 1
    return ident


def depuis_modele(corps):
    resultat = {}

    def changement(config):
        ident = _nouvel_identifiant(config, corps.get("id") or corps["modele"]["nom"])
        config.setdefault("agents", {})[ident] = agents.depuis_modele(corps["modele"])
        resultat["id"] = ident
    sortie = config_io.modifier_config(changement, f"Agent ajouté depuis la bibliothèque : {corps['modele']['nom']}", corps.get("version"))
    return {**_apres(sortie), **resultat}


def creer_equipe(corps):
    chef = corps["chef"].strip()
    if not agents.nom_valide(chef):
        raise Refus("Nom du chef : lettres minuscules, chiffres et tirets seulement (ex. equipe-web).")
    resultat = {}

    def changement(config):
        confs = config.setdefault("agents", {})
        if chef in confs or chef in agents.ORIGINE:
            raise Refus(f"Un agent « {chef} » existe déjà.")
        membres = list(corps.get("membres") or [])
        for modele in corps.get("nouveaux") or []:  # rôles pris dans la bibliothèque, créés au passage
            ident = _nouvel_identifiant(config, modele["nom"])
            confs[ident] = agents.depuis_modele(modele)
            membres.append(ident)
        if not membres:
            raise Refus("Choisissez au moins un sous-agent.")
        descriptions = {m: (confs.get(m) or {}).get("description") or agents.ORIGINE.get(m, {}).get("resume", "") for m in membres}
        confs[chef] = {"description": corps.get("description") or f"Chef d'équipe : {corps['mission']}",
                       "mode": "primary", "system": agents.consignes_equipe(corps["mission"], membres, descriptions),
                       "permissions": agents.regles_equipe(membres)}
        resultat["membres"] = membres
    sortie = config_io.modifier_config(changement, f"Équipe « {chef} » créée", corps.get("version"))
    return {**_apres(sortie), **resultat, "id": chef}


def regler(corps):
    """Petits réglages : agent par défaut, modèle par défaut."""
    def changement(config):
        if "defaut" in corps:
            config["default_agent"] = corps["defaut"]
        if "modele" in corps:
            config["model"] = corps["modele"]
    return _apres(config_io.modifier_config(changement, "Réglage : " + ", ".join(k for k in corps if k != "version"), corps.get("version")))


def enregistrer_mcp(corps):
    nom = corps["nom"].strip()
    if not agents.nom_valide(nom):
        raise Refus("Nom du MCP : lettres minuscules, chiffres et tirets seulement.")

    def changement(config):
        serveurs = config.setdefault("mcp", {}).setdefault("servers", {})
        ancien = serveurs.get(corps.get("ancien_nom") or nom) or {}
        conf = {k: v for k, v in corps["conf"].items() if k not in ("variables", "entetes", "environment", "headers")}
        # Variables : null = garder la valeur actuelle (jamais renvoyée au navigateur), "" = retirer.
        for champ in ("environment", "headers"):
            nouvelles = corps["conf"].get(champ)
            if nouvelles is None:
                if ancien.get(champ):
                    conf[champ] = ancien[champ]
                continue
            fusion = {}
            for cle, valeur in nouvelles.items():
                if valeur is None and cle in (ancien.get(champ) or {}):
                    fusion[cle] = ancien[champ][cle]
                elif valeur:
                    fusion[cle] = valeur
            if fusion:
                conf[champ] = fusion
        if corps.get("ancien_nom") and corps["ancien_nom"] != nom:
            serveurs.pop(corps["ancien_nom"], None)
        serveurs[nom] = conf
    return _apres(config_io.modifier_config(changement, f"MCP « {nom} » enregistré", corps.get("version")))


def mcp_actif(corps):
    def changement(config):
        serveur = ((config.get("mcp") or {}).get("servers") or {}).get(corps["nom"])
        if serveur is None:
            raise Refus("MCP introuvable.", statut=404)
        if corps["actif"]:
            serveur.pop("disabled", None)
        else:
            serveur["disabled"] = True
    return _apres(config_io.modifier_config(changement, f"MCP « {corps['nom']} » {'activé' if corps['actif'] else 'désactivé'}", corps.get("version")))


def mcp_supprimer(corps):
    def changement(config):
        ((config.get("mcp") or {}).get("servers") or {}).pop(corps["nom"], None)
    return _apres(config_io.modifier_config(changement, f"MCP « {corps['nom']} » retiré", corps.get("version")))


def mcp_catalogue(corps):
    conf = services.config_depuis_catalogue(corps["nom"])

    def changement(config):
        config.setdefault("mcp", {}).setdefault("servers", {})[corps["nom"]] = conf
    return _apres(config_io.modifier_config(changement, f"MCP « {corps['nom']} » ajouté depuis C:\\MCP", corps.get("version")))


def mcp_tester(corps):
    config, _, _ = config_io.lire_config()
    if corps.get("catalogue"):
        conf = services.config_depuis_catalogue(corps["nom"])
    else:
        conf = ((config.get("mcp") or {}).get("servers") or {}).get(corps["nom"])
    if not conf:
        raise Refus("MCP introuvable.", statut=404)
    return services.tester_mcp(conf)


def enregistrer_commande(corps):
    nom = corps["nom"].strip().lstrip("/")
    if not agents.nom_valide(nom):
        raise Refus("Nom de commande : lettres minuscules, chiffres et tirets seulement (ex. audit-site).")
    if not (corps.get("template") or "").strip():
        raise Refus("Le message de la commande est vide.")

    def changement(config):
        commandes = config.setdefault("commands", {})
        if corps.get("ancien_nom") and corps["ancien_nom"] != nom:
            commandes.pop(corps["ancien_nom"], None)
        conf = {"template": corps["template"]}
        for champ in ("description", "agent", "model"):
            if (corps.get(champ) or "").strip():
                conf[champ] = corps[champ].strip()
        if corps.get("subagent"):
            conf["subagent"] = True
        commandes[nom] = conf
    return _apres(config_io.modifier_config(changement, f"Commande /{nom} enregistrée", corps.get("version")))


def supprimer_commande(corps):
    def changement(config):
        (config.get("commands") or {}).pop(corps["nom"], None)
        if not config.get("commands"):
            config.pop("commands", None)
    return _apres(config_io.modifier_config(changement, f"Commande /{corps['nom']} supprimée", corps.get("version")))


def enregistrer_skill(corps):
    nom = corps["nom"].strip()
    if not agents.nom_valide(nom):
        raise Refus("Nom de skill : lettres minuscules, chiffres et tirets seulement (ex. audit-site).")
    description = " ".join((corps.get("description") or "").split())
    if not description:
        raise Refus("La description dit à l'agent quand charger la skill : elle est obligatoire.")
    ancien = (corps.get("ancien_nom") or nom).strip()
    if ancien != nom:
        if (chemins.SKILLS / nom).exists():
            raise Refus(f"Une skill « {nom} » existe déjà.")
        (chemins.SKILLS / ancien).rename(chemins.SKILLS / nom)
    texte = f"---\nname: {nom}\ndescription: {description}\n---\n\n{corps.get('contenu', '').strip()}\n"
    config_io.ecrire_texte(chemins.SKILLS / nom / "SKILL.md", texte, f"skill:{nom}", f"Skill « {nom} » enregistrée")
    autoriser = corps.get("autoriser", True)

    def changement(config):
        regles = config.setdefault("permissions", [])
        regles[:] = [r for r in regles if not (r.get("action") == "skill" and r.get("resource") in (ancien, nom) and r.get("effect") == "allow")]
        if autoriser:
            regles.append({"action": "skill", "resource": nom, "effect": "allow"})
    return _apres(config_io.modifier_config(changement, f"Skill « {nom} » : {'autorisée' if autoriser else 'non autorisée'}"))


def supprimer_skill(corps):
    dossier = chemins.SKILLS / corps["nom"]
    if not dossier.exists():
        raise Refus("Skill introuvable.", statut=404)
    config_io.mettre_de_cote(dossier, f"skill:{corps['nom']}", f"Skill « {corps['nom']} » mise de côté")

    def changement(config):
        config["permissions"] = [r for r in config.get("permissions") or []
                                 if not (r.get("action") == "skill" and r.get("resource") == corps["nom"])]
    return _apres(config_io.modifier_config(changement, f"Skill « {corps['nom']} » retirée des autorisations"))


def enregistrer_consignes(corps):
    return {**config_io.ecrire_texte(chemins.CONSIGNES, corps["texte"], "consignes", "Consignes communes modifiées"),
            "message": "Enregistré : les agents liront ces consignes à leur prochaine session."}


def enregistrer_securite(corps):
    def changement(config):
        actuelles = config.get("permissions") or []
        protegees = [r for r in actuelles if _protegee(r)]
        nouvelles = [{"action": r["action"].strip(), "resource": r["resource"].strip(), "effect": r["effect"]}
                     for r in corps["regles"] if not _protegee(r) and r.get("action") and r.get("resource")]
        if any(r["effect"] not in ("allow", "ask", "deny") for r in nouvelles):
            raise Refus("Effet inconnu dans une règle.")
        config["permissions"] = protegees + nouvelles
    return _apres(config_io.modifier_config(changement, "Règles de sécurité modifiées", corps.get("version")))


# ---------- Fenêtre ----------

def ouvrir_fenetre(page=""):
    if not chemins.EDGE:
        return {"ok": False, "message": "Microsoft Edge introuvable."}
    chemins.PROFIL_FENETRE.mkdir(parents=True, exist_ok=True)
    adresse = f"http://127.0.0.1:{chemins.PORT}/" + (f"#{page}" if page else "")
    subprocess.Popen([str(chemins.EDGE), f"--user-data-dir={chemins.PROFIL_FENETRE}", f"--app={adresse}",
                      "--no-first-run", "--no-default-browser-check", "--disable-sync",
                      "--disable-features=Translate", "--window-size=1320,900"],
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return {"ok": True}


# ---------- Serveur HTTP ----------

ROUTES = {
    "/api/agent": enregistrer_agent, "/api/agent/supprimer": supprimer_agent,
    "/api/agent/depuis-modele": depuis_modele, "/api/equipe": creer_equipe, "/api/regler": regler,
    "/api/mcp": enregistrer_mcp, "/api/mcp/actif": mcp_actif, "/api/mcp/supprimer": mcp_supprimer,
    "/api/mcp/catalogue": mcp_catalogue, "/api/mcp/tester": mcp_tester,
    "/api/commande": enregistrer_commande, "/api/commande/supprimer": supprimer_commande,
    "/api/skill": enregistrer_skill, "/api/skill/supprimer": supprimer_skill,
    "/api/consignes": enregistrer_consignes, "/api/securite": enregistrer_securite,
    "/api/restaurer": lambda c: _apres(config_io.restaurer(c["id"])),
    "/api/gpu/arreter": lambda c: {"ok": True, "pods": services.arreter_gpu()},
    "/api/ouvrir": lambda c: ouvrir_fenetre(c.get("page", "")),
}


class Gestion(BaseHTTPRequestHandler):
    server_version = "Atelier/1.0"

    def log_message(self, *args):  # pas de journal console (pythonw)
        pass

    def _hote_ok(self):
        return self.headers.get("Host", "") in (f"127.0.0.1:{chemins.PORT}", f"localhost:{chemins.PORT}")

    def _envoyer(self, code, corps, type_="application/json; charset=utf-8", cors=None):
        donnees = corps if isinstance(corps, bytes) else json.dumps(corps, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(donnees)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cors:
            self.send_header("Access-Control-Allow-Origin", cors)
        else:
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(donnees)

    def do_GET(self):
        DERNIERE_ACTIVITE[0] = time.time()
        if not self._hote_ok():
            return self._envoyer(403, {"erreur": "hôte refusé"})
        url = urlparse(self.path)
        origine = self.headers.get("Origin")
        cors = origine if origine in ORIGINES_OPENCODE else None
        if url.path == "/api/etat-court":  # pastille de la fenêtre de l'agent : aucune donnée sensible
            gpu = services.etat_gpu()
            return self._envoyer(200, {"gpu": gpu["etat"], "prix_heure": gpu.get("prix_heure"),
                                       "ia_locale": services.etat_ia_locale()["etat"]}, cors=cors)
        if url.path == "/ouvrir":  # bouton « Atelier » et « ? » de la fenêtre de l'agent
            # Seulement la fenêtre de l'agent, ou un programme local (pas d'en-têtes de navigateur) : jamais un site web.
            programme_local = origine is None and "Sec-Fetch-Site" not in self.headers
            if not (cors or programme_local):
                return self._envoyer(403, {"erreur": "origine refusée"})
            page = (parse_qs(url.query).get("page") or [""])[0]
            return self._envoyer(200, ouvrir_fenetre(re.sub(r"[^a-z0-9/_-]", "", page)), cors=cors)
        if url.path.startswith("/api/"):
            if self.headers.get("X-Atelier-Jeton") != JETON:
                return self._envoyer(403, {"erreur": "jeton manquant"})
            try:
                if url.path == "/api/tout":
                    return self._envoyer(200, tout())
                if url.path == "/api/services":
                    forcer = "forcer" in url.query
                    return self._envoyer(200, {"gpu": services.etat_gpu(forcer), "ia_locale": services.etat_ia_locale(),
                                               "opencode": bool(services.session_opencode())})
                if url.path == "/api/comparer":
                    return self._envoyer(200, {"diff": config_io.comparer(parse_qs(url.query)["id"][0])})
                if url.path == "/api/catalogue":
                    config, _, _ = config_io.lire_config()
                    return self._envoyer(200, services.catalogue_mcp(set(((config.get("mcp") or {}).get("servers") or {}))))
                if url.path == "/api/battement":
                    return self._envoyer(200, {"ok": True})
            except Refus as refus:
                return self._envoyer(refus.statut, {"erreur": str(refus), "erreurs": refus.erreurs})
            return self._envoyer(404, {"erreur": "inconnu"})
        # Fichiers de l'interface
        nom = "index.html" if url.path in ("/", "") else url.path.lstrip("/")
        racine = chemins.WEB
        if nom.startswith("guide/"):  # le guide (wiki avec captures)
            racine, nom = chemins.ATELIER / "guide", nom[len("guide/"):] or "index.html"
        fichier = (racine / nom).resolve()
        if racine.resolve() not in fichier.parents or not fichier.is_file():
            return self._envoyer(404, b"introuvable", "text/plain; charset=utf-8")
        contenu = fichier.read_bytes()
        if racine == chemins.WEB and nom == "index.html":
            contenu = contenu.replace(b"__JETON__", JETON.encode())
        types = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml",
                 ".png": "image/png", ".ico": "image/x-icon"}
        type_ = types.get(fichier.suffix.lower()) or mimetypes.guess_type(fichier.name)[0] or "application/octet-stream"
        if type_.startswith("text/"):
            type_ += "; charset=utf-8"
        return self._envoyer(200, contenu, type_)

    def do_POST(self):
        DERNIERE_ACTIVITE[0] = time.time()
        if not self._hote_ok() or self.headers.get("X-Atelier-Jeton") != JETON:
            return self._envoyer(403, {"erreur": "accès refusé"})
        route = ROUTES.get(urlparse(self.path).path)
        if not route:
            return self._envoyer(404, {"erreur": "inconnu"})
        try:
            longueur = int(self.headers.get("Content-Length") or 0)
            corps = json.loads(self.rfile.read(longueur) or b"{}")
            return self._envoyer(200, route(corps))
        except Refus as refus:
            return self._envoyer(refus.statut, {"erreur": str(refus), "erreurs": refus.erreurs})
        except (KeyError, ValueError, TypeError) as erreur:
            return self._envoyer(400, {"erreur": f"Demande incomplète : {erreur}"})
        except Exception as erreur:  # noqa: BLE001
            return self._envoyer(500, {"erreur": f"Erreur inattendue : {erreur}"})


def surveiller(serveur):
    while True:
        time.sleep(30)
        if time.time() - DERNIERE_ACTIVITE[0] > INACTIVITE_MAX and not services.session_opencode():
            serveur.shutdown()
            return


def main():
    try:
        serveur = ThreadingHTTPServer(("127.0.0.1", chemins.PORT), Gestion)
    except OSError:
        # Déjà lancé : on ouvre seulement une fenêtre si demandé.
        if "--fenetre" in sys.argv:
            import urllib.request
            urllib.request.urlopen(f"http://127.0.0.1:{chemins.PORT}/ouvrir", timeout=5).close()
        return
    if "--fenetre" in sys.argv:
        threading.Timer(0.3, ouvrir_fenetre).start()
    threading.Thread(target=surveiller, args=(serveur,), daemon=True).start()
    serveur.serve_forever()


if __name__ == "__main__":
    main()
