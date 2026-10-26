"""Recrée la config de l'environnement de test : copie de la vraie config, clé RunPod remplacée, MCP désactivés,
chemins absolus adaptés. Aucune donnée de conversation n'est concernée (seulement config\\opencode)."""
import json
import pathlib
import shutil

VRAIE = pathlib.Path(r"D:\IA LOCAL\config\opencode")
TEST = pathlib.Path(r"D:\IA LOCAL\_maintenance\OpenCode-web-test\config\opencode")

config = json.loads((VRAIE / "opencode.json").read_text(encoding="utf-8"))
for fournisseur in config.get("providers", {}).values():
    if "apiKey" in fournisseur.get("settings", {}):
        fournisseur["settings"]["apiKey"] = "CLE-DE-TEST"
for serveur in config.get("mcp", {}).get("servers", {}).values():
    serveur["disabled"] = True
    for cle in list((serveur.get("environment") or {})):
        if cle not in ("USERPROFILE", "HOME"):
            serveur["environment"][cle] = "VALEUR-DE-TEST"
texte = json.dumps(config, ensure_ascii=False, indent=2).replace("D:/IA LOCAL/", "D:/IA LOCAL/_maintenance/OpenCode-web-test/")
(TEST / "opencode.json").write_text(texte.replace("\n", "\r\n") + "\r\n", encoding="utf-8")
shutil.copy2(VRAIE / "AGENTS.md", TEST / "AGENTS.md")
if (TEST / "skills").exists():
    shutil.rmtree(TEST / "skills")
shutil.copytree(VRAIE / "skills", TEST / "skills")
print("config de test recréée :", len(config["agents"]), "agents")
