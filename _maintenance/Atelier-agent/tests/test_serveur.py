"""Tests des opérations de l'Atelier, sur l'environnement de test uniquement.

Lancer : set ATELIER_BASE=D:\\IA LOCAL\\_maintenance\\OpenCode-web-test
         "C:\\Program Files\\Python314\\python.exe" tests\\test_serveur.py
"""
import json
import os
import shutil
import sys
from pathlib import Path

assert "OpenCode-web-test" in os.environ.get("ATELIER_BASE", ""), "Ces tests ne tournent que sur l'environnement de test."
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "atelier"))
import agents  # noqa: E402
import atelier  # noqa: E402
import chemins  # noqa: E402
import config_io  # noqa: E402
from config_io import Refus  # noqa: E402

if chemins.SAUVEGARDES.exists():
    shutil.rmtree(chemins.SAUVEGARDES)
resultats = []


def verif(nom, condition, detail=""):
    resultats.append((nom, bool(condition)))
    print(("OK   " if condition else "ÉCHEC"), nom, detail if not condition else "")


def conf():
    return json.loads(chemins.CONFIG.read_text(encoding="utf-8"))


def refuse(fonction, corps):
    try:
        fonction(corps)
        return None
    except Refus as refus:
        return refus


# 1. Lecture
t = atelier.tout()
ids = [a["id"] for a in t["agents"]]
verif("lecture : agents d'origine + les vôtres + internes", {"build", "plan", "general", "explore", "equipe", "analyste", "compaction"} <= set(ids))
verif("lecture : aucune clé dans la réponse", "CLE-DE-TEST" not in json.dumps(t) and "VALEUR-DE-TEST" not in json.dumps(t))
analyste = next(a for a in t["agents"] if a["id"] == "analyste")
verif("droits : analyste ne modifie pas", analyste["droits"]["fichiers"]["valeur"] == "non")
build = next(a for a in t["agents"] if a["id"] == "build")
verif("droits : build modifie, commandes sur demande", build["droits"]["fichiers"]["valeur"] == "oui" and build["droits"]["commandes"]["valeur"] == "dem")
equipe = next(a for a in t["agents"] if a["id"] == "equipe")
verif("droits : equipe = liste de sous-agents", equipe["droits"]["sousagents"]["valeur"] == "liste")
verif("modèles disponibles lus", any(m["id"] == "runpod/heretic" for m in t["modeles"]))
v = t["version"]

# 2. Créer, renommer, supprimer un agent
r = atelier.enregistrer_agent({"id": "essai", "description": "Agent d'essai", "mode": "subagent", "system": "Tu testes.",
                               "droits": {"fichiers": "non", "commandes": "non", "internet": "dem", "sousagents": "non"}, "version": v})
c = conf()
verif("agent créé", c["agents"]["essai"]["mode"] == "subagent" and {"action": "edit", "resource": "*", "effect": "deny"} in c["agents"]["essai"]["permissions"])
verif("message de rechargement (agent fermé)", "prochain lancement" in r.get("message", ""))
verif("sauvegarde faite", len(config_io.liste_sauvegardes()) == 1)
verif("conflit de version détecté", (refuse(atelier.enregistrer_agent, {"id": "essai", "description": "x", "version": v}) or Refus("", statut=0)).statut == 409)
atelier.enregistrer_agent({"id": "essai-2", "ancien_id": "essai", "description": "Agent d'essai renommé"})
c = conf()
verif("agent renommé", "essai-2" in c["agents"] and "essai" not in c["agents"])
erreur = refuse(atelier.enregistrer_agent, {"id": "essai-2", "model": "pas-un-modele"})
verif("modèle invalide refusé par OpenCode", erreur is not None and erreur.erreurs, str(erreur.erreurs if erreur else ""))
verif("config intacte après refus", conf()["agents"]["essai-2"].get("model") is None)
atelier.enregistrer_agent({"id": "essai-2", "permissions_expert": [{"action": "shell", "resource": "git *", "effect": "allow"}]})
verif("mode expert", conf()["agents"]["essai-2"]["permissions"] == [{"action": "shell", "resource": "git *", "effect": "allow"}])
atelier.enregistrer_agent({"id": "build", "description": "Mon build", "color": "#ff8800"})
verif("agent d'origine modifié", conf()["agents"]["build"] == {"description": "Mon build", "color": "#ff8800"})
verif("agent d'origine non supprimable", refuse(atelier.supprimer_agent, {"id": "plan"}) is not None)

# 3. Bibliothèque et équipe
r = atelier.depuis_modele({"modele": {"nom": "Relecteur de code", "desc": "Relit un changement.", "droits": ["lecture"]}})
verif("agent depuis la bibliothèque", r["id"] == "relecteur-de-code" and conf()["agents"]["relecteur-de-code"]["mode"] == "subagent")
r = atelier.creer_equipe({"chef": "equipe-essai", "mission": "tester l'Atelier", "membres": ["analyste", "essai-2"],
                          "nouveaux": [{"nom": "Testeur d'interface", "desc": "Parcourt l'appli.", "droits": ["lecture", "shell"]}]})
c = conf()
chef = c["agents"]["equipe-essai"]
verif("équipe créée avec 3 membres", r["membres"] == ["analyste", "essai-2", "testeur-d-interface"])
verif("droits du chef = seulement ses membres", agents.evaluer("subagent", "codeur", agents.regles_completes("equipe-essai", chef, c["permissions"])) == "deny"
      and agents.evaluer("subagent", "analyste", agents.regles_completes("equipe-essai", chef, c["permissions"])) == "allow")
atelier.supprimer_agent({"id": "essai-2"})
c = conf()
verif("suppression nettoie l'équipe", "essai-2" not in c["agents"] and not any(p["resource"] == "essai-2" for p in c["agents"]["equipe-essai"]["permissions"]))

# 4. Réglages
atelier.regler({"defaut": "plan", "modele": "ia-locale/code"})
c = conf()
verif("agent et modèle par défaut", c["default_agent"] == "plan" and c["model"] == "ia-locale/code")

# 5. MCP
nb = len(conf()["mcp"]["servers"])
atelier.mcp_catalogue({"nom": "history"})
c = conf()
verif("MCP ajouté depuis C:\\MCP", "history" in c["mcp"]["servers"] and c["mcp"]["servers"]["history"]["type"] == "local")
test = atelier.mcp_tester({"nom": "history"})
verif("test de connexion d'un MCP", test.get("ok") is True, test.get("message"))
atelier.mcp_actif({"nom": "history", "actif": False})
verif("MCP désactivé", conf()["mcp"]["servers"]["history"].get("disabled") is True)
atelier.enregistrer_mcp({"nom": "rea", "conf": {"type": "local", "command": conf()["mcp"]["servers"]["rea"]["command"],
                                                "environment": {"GHIDRA_INSTALL_DIR": None, "JAVA_HOME": None, "USERPROFILE": None, "HOME": None, "NOUVELLE": "x"}}})
env = conf()["mcp"]["servers"]["rea"]["environment"]
verif("variables secrètes gardées, nouvelle ajoutée", env.get("GHIDRA_INSTALL_DIR") == "VALEUR-DE-TEST" and env.get("NOUVELLE") == "x")
atelier.mcp_supprimer({"nom": "history"})
verif("MCP retiré", len(conf()["mcp"]["servers"]) == nb)

# 6. Commandes, skills, consignes
atelier.enregistrer_commande({"nom": "audit-site", "template": "Analyse $ARGUMENTS", "agent": "reverse-web", "description": "Audit"})
verif("commande créée", conf()["commands"]["audit-site"]["agent"] == "reverse-web")
atelier.supprimer_commande({"nom": "audit-site"})
verif("commande supprimée", "commands" not in conf())
atelier.enregistrer_skill({"nom": "essai-skill", "description": "À charger pour tester.", "contenu": "# Essai\nContenu."})
verif("skill écrite", (chemins.SKILLS / "essai-skill" / "SKILL.md").read_text(encoding="utf-8").startswith("---\nname: essai-skill"))
verif("skill autorisée", {"action": "skill", "resource": "essai-skill", "effect": "allow"} in conf()["permissions"])
atelier.supprimer_skill({"nom": "essai-skill"})
verif("skill mise de côté (pas effacée)", not (chemins.SKILLS / "essai-skill").exists()
      and any(e.get("dossier") for e in config_io.liste_sauvegardes()))
mise = next(e for e in config_io.liste_sauvegardes() if e.get("dossier"))
config_io.restaurer(mise["id"])
verif("skill restaurée", (chemins.SKILLS / "essai-skill" / "SKILL.md").exists())
avant = chemins.CONSIGNES.read_text(encoding="utf-8")
atelier.enregistrer_consignes({"texte": avant + "\n- Règle d'essai.\n"})
verif("consignes modifiées et sauvegardées", "Règle d'essai" in chemins.CONSIGNES.read_text(encoding="utf-8")
      and any(e["genre"] == "consignes" for e in config_io.liste_sauvegardes()))

# 7. Sécurité : les protections ne peuvent pas être retirées
protegees_avant = [r for r in conf()["permissions"] if atelier._protegee(r)]
atelier.enregistrer_securite({"regles": [{"action": "shell", "resource": "*", "effect": "ask"}]})
c = conf()
verif("protections conservées", [r for r in c["permissions"] if atelier._protegee(r)] == protegees_avant and len(protegees_avant) >= 9,
      f"{len(protegees_avant)} protégées")

# 8. Sauvegardes : limite, comparaison, restauration
for i in range(22):
    atelier.enregistrer_agent({"id": "relecteur-de-code", "description": f"version {i}"})
verif("20 versions de config gardées au plus", sum(1 for e in config_io.liste_sauvegardes() if e["genre"] == "config") == 20)
derniere = next(e for e in config_io.liste_sauvegardes() if e["genre"] == "config")
verif("comparaison lisible", "version 21" in config_io.comparer(derniere["id"]))
atelier._apres(config_io.restaurer(derniere["id"]))
verif("restauration", conf()["agents"]["relecteur-de-code"]["description"] == "version 20")

total = len(resultats)
reussis = sum(1 for _, ok in resultats if ok)
print(f"\n{reussis}/{total} vérifications réussies")
sys.exit(0 if reussis == total else 1)
