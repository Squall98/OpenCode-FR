"""Agents : agents d'origine d'OpenCode, calcul des droits réels, droits en langage clair, équipes, modèles."""
import re

# Règles qu'OpenCode donne à tout agent avant les vôtres (relevées sur OpenCode v2.0.29).
BASE = [
    {"action": "*", "resource": "*", "effect": "allow"},
    {"action": "read", "resource": "*.env", "effect": "ask"},
    {"action": "read", "resource": "*.env.*", "effect": "ask"},
    {"action": "read", "resource": "*.env.example", "effect": "allow"},
]

# Agents fournis par OpenCode : nom affiché, explication en français, règles propres (après BASE).
ORIGINE = {
    "build": {
        "nom": "Build", "mode": "primary",
        "resume": "L'agent par défaut : il lit, écrit, lance des commandes et utilise les MCP, dans les limites de vos droits.",
        "explication": "C'est l'agent « tout-terrain » d'OpenCode. Il n'a pas de consignes particulières : il suit vos "
                       "consignes communes et vos règles de sécurité. À choisir pour le développement courant.",
        "regles": [{"action": "question", "resource": "*", "effect": "allow"}],
    },
    "plan": {
        "nom": "Plan", "mode": "primary",
        "resume": "Lecture seule : explore le code et propose un plan avant de commencer, sans rien modifier.",
        "explication": "Il peut lire, chercher et vous poser des questions, mais ne peut écrire que ses propres plans. "
                       "À utiliser avant un gros chantier, puis passer à Build ou à une équipe pour l'exécution.",
        "regles": [{"action": "question", "resource": "*", "effect": "allow"},
                   {"action": "edit", "resource": "*", "effect": "deny"}],
    },
    "general": {
        "nom": "General", "mode": "subagent",
        "resume": "Sous-agent polyvalent : recherches complexes et tâches en plusieurs étapes, lancées en parallèle.",
        "explication": "Un agent principal s'en sert quand il veut faire plusieurs choses à la fois. Il ne peut ni "
                       "vous poser de questions ni appeler d'autres sous-agents.",
        "regles": [{"action": "question", "resource": "*", "effect": "deny"},
                   {"action": "subagent", "resource": "*", "effect": "deny"}],
    },
    "explore": {
        "nom": "Explore", "mode": "subagent",
        "resume": "Sous-agent rapide qui fouille le code : trouver des fichiers, chercher des mots-clés, répondre à « où est… ? ».",
        "explication": "Lecture seule : il lit, cherche et peut lancer des commandes de recherche, mais ne modifie rien.",
        "regles": [{"action": "*", "resource": "*", "effect": "deny"},
                   {"action": "shell", "resource": "*", "effect": "allow"},
                   {"action": "grep", "resource": "*", "effect": "allow"},
                   {"action": "glob", "resource": "*", "effect": "allow"},
                   {"action": "webfetch", "resource": "*", "effect": "allow"},
                   {"action": "websearch", "resource": "*", "effect": "allow"},
                   {"action": "read", "resource": "*", "effect": "allow"},
                   {"action": "subagent", "resource": "*", "effect": "deny"}],
    },
}
INTERNES = {
    "compaction": "Résume une longue conversation quand la mémoire du modèle est presque pleine.",
    "title": "Donne un titre à chaque conversation.",
    "summary": "Résume une session terminée.",
}

# Les 4 droits en langage clair : action(s) OpenCode réglées, ressource testée pour lire l'état.
DROITS = [
    {"id": "fichiers", "nom": "Modifier des fichiers", "aide": "créer, modifier, supprimer des fichiers dans projets\\",
     "actions": ["edit"], "test": "projets/exemple.txt"},
    {"id": "commandes", "nom": "Lancer des commandes", "aide": "PowerShell, cmd, git, python… (sauf les commandes sans risque, toujours permises)",
     "actions": ["shell"], "test": "python script.py"},
    {"id": "internet", "nom": "Aller sur internet", "aide": "lire des pages web, faire des recherches",
     "actions": ["webfetch", "websearch"], "test": "https://exemple.com"},
    {"id": "sousagents", "nom": "Appeler des sous-agents", "aide": "confier une partie du travail à un autre agent",
     "actions": ["subagent"], "test": "un-sous-agent"},
]
EFFETS = {"allow": "oui", "ask": "dem", "deny": "non"}
VERS_EFFET = {"oui": "allow", "dem": "ask", "non": "deny"}


def _joker(texte, motif):
    exp = re.escape(motif.replace("\\", "/")).replace(r"\*", ".*").replace(r"\?", ".")
    return re.fullmatch(exp, texte.replace("\\", "/"), re.S | re.I) is not None


def evaluer(action, ressource, regles):
    """Même logique qu'OpenCode : la dernière règle qui correspond gagne ; rien ne correspond = demander."""
    for regle in reversed(regles):
        if _joker(action, regle["action"]) and _joker(ressource, regle["resource"]):
            return regle["effect"]
    return "ask"


def regles_completes(ident, agent_conf, globales):
    propres = ORIGINE.get(ident, {}).get("regles", [])
    return BASE + propres + list(globales or []) + list((agent_conf or {}).get("permissions") or [])


def etat_droits(ident, agent_conf, globales):
    """Pour chaque droit : valeur réelle (oui/dem/non), et si l'agent a sa propre règle « simple » ou non."""
    regles = regles_completes(ident, agent_conf, globales)
    propres = list((agent_conf or {}).get("permissions") or [])
    etat = {}
    for droit in DROITS:
        effets = {evaluer(a, droit["test"], regles) for a in droit["actions"]}
        valeur = EFFETS.get(effets.pop(), "dem") if len(effets) == 1 else "perso"
        concernees = [r for r in propres if r["action"] in droit["actions"]]
        simple = all(r["resource"] == "*" for r in concernees)
        etat[droit["id"]] = {"valeur": valeur if simple else "perso", "propre": bool(concernees)}
    autorises = [r["resource"] for r in propres if r["action"] == "subagent" and r["effect"] == "allow" and r["resource"] != "*"]
    if autorises:
        etat["sousagents"] = {"valeur": "liste", "propre": True, "liste": autorises}
    return etat


def appliquer_droits(agent_conf, droits):
    """Remplace les règles simples des droits réglés. « herite » = retirer la règle propre (réglage général)."""
    regles = list(agent_conf.get("permissions") or [])
    for droit in DROITS:
        valeur = droits.get(droit["id"])
        if valeur is None or valeur in ("perso", "liste"):
            continue
        regles = [r for r in regles if not (r["action"] in droit["actions"] and (r["resource"] == "*" or droit["id"] == "sousagents"))]
        if valeur in VERS_EFFET:
            regles += [{"action": a, "resource": "*", "effect": VERS_EFFET[valeur]} for a in droit["actions"]]
    if regles:
        agent_conf["permissions"] = regles
    else:
        agent_conf.pop("permissions", None)
    return agent_conf


def regles_equipe(membres):
    return ([{"action": "subagent", "resource": "*", "effect": "deny"}]
            + [{"action": "subagent", "resource": m, "effect": "allow"} for m in membres])


def consignes_equipe(mission, membres, descriptions):
    lignes = [f"- {m} : {descriptions.get(m) or 'sous-agent'}" for m in membres]
    return (f"Tu diriges une équipe de {len(membres)} sous-agent{'s' if len(membres) > 1 else ''}. Ta mission : {mission}\n\n"
            "Ton équipe :\n" + "\n".join(lignes) + "\n\n"
            "Découpe chaque demande en tâches précises, confie chaque tâche au sous-agent le plus adapté (en parallèle "
            "quand les tâches sont indépendantes), vérifie leurs résultats, puis fais une synthèse courte et claire. "
            "Ne fais pas toi-même le travail d'un sous-agent.")


def depuis_modele(modele):
    """Agent créé depuis la bibliothèque : consignes et droits tirés du modèle."""
    droits = set(modele.get("droits") or [])
    consignes = [f"Tu es « {modele['nom']} ». {modele['desc']}"]
    if "lecture" in droits and "modif" not in droits:
        consignes.append("Tu ne modifies aucun fichier : tu lis, tu analyses et tu rends un compte rendu précis "
                         "(fichiers, lignes, preuves).")
    if "modif" in droits:
        consignes.append("Fais la plus petite modification correcte, respecte le style existant, et termine par la "
                         "liste des fichiers modifiés.")
    consignes.append("Réponds en français, de façon courte et vérifiable.")
    conf = {"description": modele["desc"], "mode": "subagent", "system": " ".join(consignes)}
    regles = []
    if "modif" not in droits:
        regles.append({"action": "edit", "resource": "*", "effect": "deny"})
    if "shell" not in droits:
        regles += [{"action": "shell", "resource": "*", "effect": "deny"},
                   {"action": "shell", "resource": "ls *", "effect": "allow"},
                   {"action": "shell", "resource": "dir *", "effect": "allow"}]
    if "web" not in droits:
        regles += [{"action": "webfetch", "resource": "*", "effect": "deny"},
                   {"action": "websearch", "resource": "*", "effect": "deny"}]
    if "sous" not in droits:
        regles.append({"action": "subagent", "resource": "*", "effect": "deny"})
    if regles:
        conf["permissions"] = regles
    return conf


def nom_valide(nom):
    return re.fullmatch(r"[a-z0-9][a-z0-9-]{0,40}", nom or "") is not None


def identifiant(nom):
    """« Relecteur de code » → « relecteur-de-code »."""
    import unicodedata
    texte = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", texte).strip("-")[:40] or "agent"


def vue_agents(config):
    """Liste complète pour l'interface : agents d'origine (même non réglés), les vôtres, les internes."""
    confs = config.get("agents") or {}
    globales = config.get("permissions") or []
    liste = []
    for ident, info in ORIGINE.items():
        conf = confs.get(ident) or {}
        liste.append({
            "id": ident, "nom": info["nom"], "origine": "opencode-modifie" if ident in confs else "opencode",
            "mode": conf.get("mode", info["mode"]), "description": conf.get("description") or info["resume"],
            "resume": info["resume"], "explication": info["explication"], "system": conf.get("system", ""),
            "model": conf.get("model", ""), "color": conf.get("color", ""), "disabled": conf.get("disabled", False),
            "permissions": conf.get("permissions") or [], "droits": etat_droits(ident, conf, globales),
        })
    for ident, conf in confs.items():
        if ident in ORIGINE or ident in INTERNES:
            continue
        liste.append({
            "id": ident, "nom": ident, "origine": "vous", "mode": conf.get("mode", "all"),
            "description": conf.get("description", ""), "resume": conf.get("description", ""), "explication": "",
            "system": conf.get("system", ""), "model": conf.get("model", ""), "color": conf.get("color", ""),
            "disabled": conf.get("disabled", False), "permissions": conf.get("permissions") or [],
            "droits": etat_droits(ident, conf, globales),
        })
    for ident, texte in INTERNES.items():
        liste.append({"id": ident, "nom": ident.capitalize(), "origine": "interne", "mode": "primary",
                      "description": texte, "resume": texte, "explication": "Agent technique : OpenCode s'en sert tout seul. "
                      "Il n'a aucun outil et n'apparaît jamais dans le menu.", "droits": {}, "permissions": []})
    return liste
