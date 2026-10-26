// Atelier de l'agent : interface. Les données viennent de /api/tout ; chaque modification passe par le serveur,
// qui la fait vérifier par OpenCode, sauvegarde l'ancienne config, écrit, puis recharge l'agent ouvert.
(function () {
  "use strict";
  var JETON = document.querySelector('meta[name="atelier-jeton"]').content;
  var principal = document.getElementById("principal");
  var etat = null; // réponse de /api/tout
  var services = null;
  var ecran = "accueil", detail = "";

  // ---------- Outils ----------
  function e(texte) {
    return String(texte == null ? "" : texte).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function $(sel, racine) { return (racine || document).querySelector(sel); }
  function $$(sel, racine) { return Array.prototype.slice.call((racine || document).querySelectorAll(sel)); }

  function appel(methode, chemin, corps) {
    var options = { method: methode, headers: { "X-Atelier-Jeton": JETON } };
    if (corps) { options.headers["Content-Type"] = "application/json"; options.body = JSON.stringify(corps); }
    return fetch(chemin, options).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (donnees) {
        if (!r.ok) { var err = new Error(donnees.erreur || ("Erreur " + r.status)); err.erreurs = donnees.erreurs || []; throw err; }
        return donnees;
      });
    });
  }

  function toast(message, erreur) {
    var div = document.createElement("div");
    if (erreur) div.className = "err";
    div.textContent = message;
    $("#toast").appendChild(div);
    setTimeout(function () { div.remove(); }, erreur ? 9000 : 5000);
  }

  var voile = $("#voile"), boite = $("#voile-boite");
  function attente(texte) { boite.innerHTML = '<span class="roue"></span>' + e(texte); voile.classList.add("actif"); }
  function fermerVoile() { voile.classList.remove("actif"); }
  function fenetre(html) {
    boite.innerHTML = html + '<div class="ligne" style="margin-top:14px"><span class="espace"></span><button class="btn" data-action="fermer-voile">Fermer</button></div>';
    voile.classList.add("actif");
  }
  function confirmer(question) { return window.confirm(question); }

  var TRADUCTIONS = {
    "skipped malformed recognized value": "valeur non reconnue (format incorrect)",
    "agent refusé par OpenCode": "agent refusé par OpenCode",
    "rejected malformed JSON or JSONC document": "fichier JSON mal formé"
  };
  function erreursHtml(erreurs) {
    if (!erreurs || !erreurs.length) return "";
    return '<div class="erreurs"><b>Ce qu\'OpenCode a refusé :</b><ul>' + erreurs.map(function (x) {
      return "<li><code>" + e(x.chemin) + "</code> : " + e(TRADUCTIONS[x.message] || x.message) + "</li>";
    }).join("") + "</ul></div>";
  }

  // Envoie une modification : vérification par OpenCode, puis rechargement de l'état.
  function modifier(chemin, corps, texteAttente) {
    corps = corps || {};
    if (etat && corps.version === undefined) corps.version = etat.version;
    attente(texteAttente || "Vérification par OpenCode, sauvegarde, enregistrement…");
    return appel("POST", chemin, corps).then(function (r) {
      fermerVoile();
      toast(r.message || "Enregistré.");
      return charger().then(function () { return r; });
    }).catch(function (err) {
      fenetre("<h2 style='margin-top:0'>Rien n'a été modifié</h2><p>" + e(err.message) + "</p>" + erreursHtml(err.erreurs));
      throw err;
    });
  }

  function charger() {
    return appel("GET", "/api/tout").then(function (d) { etat = d; compteurs(); afficher(); });
  }

  function compteurs() {
    var vous = etat.agents.filter(function (a) { return a.origine !== "interne"; });
    $("#nb-agents").textContent = vous.length;
    $("#nb-equipes").textContent = equipes().length;
    $("#nb-biblio").textContent = (window.BIBLIO || []).length;
    $("#nb-mcp").textContent = etat.mcp.length;
    $("#nb-commandes").textContent = etat.commandes.length;
    $("#nb-skills").textContent = etat.skills.length;
    $("#nb-sauvegardes").textContent = etat.sauvegardes.length;
    var bandeau = $("#bandeau-test");
    bandeau.hidden = !etat.test;
    bandeau.textContent = "Mode test : vous modifiez la copie de " + etat.base + ", pas votre agent réel.";
  }

  function agent(id) { return etat.agents.find(function (a) { return a.id === id; }); }
  function equipes() {
    return etat.agents.filter(function (a) { return a.droits && a.droits.sousagents && a.droits.sousagents.valeur === "liste"; });
  }
  function modeTexte(mode) { return { primary: "Principal", subagent: "Sous-agent", all: "Principal et sous-agent" }[mode] || mode; }
  function origineTexte(o) { return { opencode: "OpenCode", "opencode-modifie": "OpenCode, modifié par vous", vous: "vous", interne: "OpenCode (interne)" }[o] || o; }
  function nomModele(id) {
    var m = etat.modeles.find(function (x) { return x.id === id; });
    return m ? m.nom : (id || "");
  }
  function optionsModeles(choisi, avecDefaut) {
    return (avecDefaut ? '<option value="">Celui par défaut (' + e(nomModele(etat.modele)) + ")</option>" : "") +
      etat.modeles.map(function (m) {
        return '<option value="' + e(m.id) + '"' + (m.id === choisi ? " selected" : "") + ">" + e(m.nom) + " — " + e(m.fournisseur) + "</option>";
      }).join("");
  }

  // ---------- Navigation ----------
  function aller(nom, sous) {
    location.hash = nom + (sous ? "/" + sous : "");
  }
  function lireHash() {
    var parts = (location.hash || "#accueil").slice(1).split("/");
    ecran = parts[0] || "accueil"; detail = decodeURIComponent(parts.slice(1).join("/") || "");
    $$(".nav").forEach(function (n) {
      if (n.dataset.ecran === ecran) n.setAttribute("aria-current", "page"); else n.removeAttribute("aria-current");
    });
    if (etat) afficher();
    principal.scrollTop = 0;
  }
  window.addEventListener("hashchange", lireHash);
  $$(".nav").forEach(function (n) { n.addEventListener("click", function () { aller(n.dataset.ecran); }); });

  function afficher() {
    var rendu = ECRANS[ecran] || ECRANS.accueil;
    principal.innerHTML = '<section class="ecran actif">' + rendu() + "</section>";
    if (APRES[ecran]) APRES[ecran]();
  }

  // ---------- Écrans ----------
  var ECRANS = {}, APRES = {};

  ECRANS.accueil = function () {
    var actifs = etat.mcp.filter(function (m) { return m.actif; });
    var principaux = etat.agents.filter(function (a) { return a.mode !== "subagent" && a.origine !== "interne" && !a.disabled; });
    var sous = etat.agents.filter(function (a) { return a.mode === "subagent" && !a.disabled; });
    var defaut = agent(etat.defaut);
    return "<h1>Vue d'ensemble</h1><p class='sous'>Tout ce que votre agent sait faire, et ce qui tourne en ce moment.</p>" +
      "<div class='grille'>" +
      "<div class='carte'><div class='etiq'>Agent par défaut</div><div class='chiffre'>" + e(defaut ? defaut.nom : etat.defaut) + "</div><div class='etiq'>à l'ouverture d'une session</div></div>" +
      "<div class='carte'><div class='etiq'>Agents</div><div class='chiffre'>" + principaux.length + " + " + sous.length + "</div><div class='etiq'>principaux + sous-agents</div></div>" +
      "<div class='carte'><div class='etiq'>MCP actifs</div><div class='chiffre'>" + actifs.length + "</div><div class='etiq'>" + e(actifs.map(function (m) { return m.nom; }).join(" · ") || "aucun") + "</div></div>" +
      "<div class='carte'><div class='etiq'>Modèle par défaut</div><div class='chiffre' style='font-size:16px'>" + e(nomModele(etat.modele)) + "</div><div class='etiq'>" + e(etat.modele) + "</div></div>" +
      "</div><h2>Accès rapides</h2><div class='ligne' style='flex-wrap:wrap'>" +
      "<button class='btn prim' data-aller='agents/+'>+ Nouvel agent</button>" +
      "<button class='btn' data-aller='equipes'>+ Créer une équipe</button>" +
      "<button class='btn' data-aller='biblio'>Bibliothèque de modèles</button>" +
      "<button class='btn' data-aller='mcp'>+ Ajouter un MCP</button>" +
      "<button class='btn' data-aller='commandes/+'>+ Nouvelle commande /</button>" +
      "<button class='btn' data-aller='sauvegardes'>Revenir à une version précédente</button></div>" +
      "<h2>Dernières modifications</h2><div class='carte'>" + (etat.sauvegardes.length ? "<table><tr><th>Quand</th><th>Quoi</th></tr>" +
        etat.sauvegardes.slice(0, 6).map(function (s) { return "<tr><td>" + e(s.date) + "</td><td>" + e(s.resume) + "</td></tr>"; }).join("") + "</table>"
        : "<div class='vide'>Aucune modification faite avec l'Atelier pour l'instant.</div>") + "</div>";
  };

  // --- Mes agents ---
  var GROUPES = [
    ["Agents principaux (dans le menu)", function (a) { return a.origine !== "interne" && a.mode !== "subagent" && !(a.origine !== "vous" && ["general", "explore"].indexOf(a.id) >= 0); }],
    ["Sous-agents", function (a) { return a.origine === "vous" && a.mode === "subagent"; }],
    ["Sous-agents fournis par OpenCode", function (a) { return a.origine !== "vous" && a.origine !== "interne" && a.mode === "subagent"; }],
    ["Internes (OpenCode s'en sert seul)", function (a) { return a.origine === "interne"; }]
  ];
  ECRANS.agents = function () {
    var choisi = detail || etat.defaut;
    var liste = GROUPES.map(function (g) {
      var membres = etat.agents.filter(g[1]);
      if (!membres.length) return "";
      return "<h3>" + e(g[0]) + "</h3>" + membres.map(function (a) {
        return "<button class='item' data-agent='" + e(a.id) + "' aria-current='" + (a.id === choisi) + "'>" +
          "<span class='puce' style='background:" + e(a.color || "var(--faible)") + "'></span><span>" + e(a.nom) + (a.disabled ? " <span class='badge'>désactivé</span>" : "") +
          "<small>" + e(a.description || a.resume) + "</small></span></button>";
      }).join("");
    }).join("");
    return "<div class='ligne'><div><h1>Mes agents</h1><p class='sous'>Cliquez sur un agent pour voir ce qu'il fait et le régler.</p></div><span class='espace'></span>" +
      "<button class='btn prim' data-aller='agents/+'>+ Nouvel agent</button></div>" +
      "<div class='deux'><div class='liste'>" + liste + "</div><div class='carte' id='fiche'>" + ficheAgent(choisi) + "</div></div>";
  };

  function segm(droit, valeur, propre) {
    var v = [["oui", "Toujours", "v-oui"], ["dem", "Sur demande", "v-dem"], ["non", "Jamais", "v-non"]];
    return "<span class='segm' data-droit='" + droit + "'>" + v.map(function (x) {
      return "<button type='button' class='" + x[2] + "' data-valeur='" + x[0] + "' aria-pressed='" + (x[0] === valeur) + "'>" + x[1] + "</button>";
    }).join("") + "</span>" + (propre ? "" : " <span class='aide' title=\"Cet agent n'a pas de règle à lui pour ce droit : la valeur vient des règles générales (écran Sécurité) ou d'OpenCode.\">hérité</span>");
  }

  function ficheAgent(id) {
    var nouveau = id === "+";
    var a = nouveau ? { id: "", nom: "", origine: "vous", mode: "subagent", description: "", system: "", model: "", color: "", permissions: [],
      droits: { fichiers: { valeur: "oui" }, commandes: { valeur: "dem" }, internet: { valeur: "dem" }, sousagents: { valeur: "non" } } } : agent(id);
    if (!a) return "<div class='vide'>Agent introuvable.</div>";
    var interne = a.origine === "interne", vous = a.origine === "vous";
    var entete = "<div class='ligne'><span class='puce' style='background:" + e(a.color || "var(--faible)") + ";width:14px;height:14px'></span><h1 style='margin:0'>" +
      (nouveau ? "Nouvel agent" : e(a.nom)) + "</h1>" + (nouveau ? "" : "<span class='badge acc'>" + e(modeTexte(a.mode)) + "</span><span class='badge'>créé par : " + e(origineTexte(a.origine)) + "</span>") +
      (a.id === etat.defaut ? "<span class='badge ok'>par défaut</span>" : "") + "</div>" +
      (a.resume && !nouveau ? "<p style='margin:10px 0 4px'><b>À quoi il sert.</b> " + e(a.resume) + "</p>" : "") +
      (a.explication ? "<p class='etiq' style='margin:0 0 14px'>" + e(a.explication) + "</p>" : "");
    if (interne) return entete;
    var droits = etat.droits.map(function (d) {
      var etatDroit = a.droits[d.id] || { valeur: "dem" };
      var controle;
      if (etatDroit.valeur === "liste") {
        controle = "<span class='puces'>" + etatDroit.liste.map(function (m) { return "<span class='badge acc'>" + e(m) + "</span>"; }).join("") +
          "</span> <span class='aide'>seulement ces sous-agents (réglé par l'équipe)</span>";
      } else if (etatDroit.valeur === "perso") {
        controle = "<span class='badge att'>personnalisé</span> <span class='aide'>règles détaillées : voir le mode expert</span>";
      } else {
        controle = segm(d.id, etatDroit.valeur, nouveau || etatDroit.propre);
      }
      return "<div class='droit'><div>" + e(d.nom) + "<small>" + e(d.aide) + "</small></div>" + controle + "</div>";
    }).join("");
    return entete +
      "<form id='form-agent' data-id='" + e(a.id) + "' data-nouveau='" + nouveau + "'>" +
      "<div class='champs2'><div class='champ'><label>Nom (identifiant)</label><input name='id' value='" + e(a.id) + "'" + (vous ? "" : " readonly") + " placeholder='ex. relecteur-web'></div>" +
      "<div class='champ'><label>Rôle</label><select name='mode'>" + ["primary", "subagent", "all"].map(function (m) {
        return "<option value='" + m + "'" + (a.mode === m ? " selected" : "") + ">" + modeTexte(m) + "</option>"; }).join("") + "</select></div></div>" +
      "<div class='champ'><label>Description (affichée dans le menu des agents, et lue par un chef d'équipe pour choisir)</label><input name='description' value='" + e(a.description) + "'></div>" +
      "<div class='champ'><label>Consignes (ce que l'agent lit avant chaque tâche)</label><textarea name='system' style='min-height:150px' placeholder='" +
      e(vous ? "Ex. Tu relis le code sans le modifier…" : "Vide = consignes d'origine d'OpenCode. Ce que vous écrivez ici les remplace.") + "'>" + e(a.system) + "</textarea></div>" +
      "<div class='champs2'><div class='champ'><label>Modèle</label><select name='model'>" + optionsModeles(a.model, true) + "</select></div>" +
      "<div class='champ'><label>Couleur</label><div class='ligne'><input type='color' name='color' value='" + e(a.color || "#4f8cff") + "' style='height:34px;width:60px;padding:2px'>" +
      "<label class='aide'><input type='checkbox' name='sans_couleur'" + (a.color ? "" : " checked") + "> aucune</label></div></div></div>" +
      "<h2>Ses droits</h2><div class='droits'>" + droits + "</div>" +
      "<details><summary>Mode expert : les règles exactes de cet agent dans opencode.json</summary>" +
      "<p class='aide'>Une règle par objet : action (edit, shell, read, webfetch, subagent…), ressource (motif avec *), effet (allow, ask, deny). La dernière règle qui correspond gagne.</p>" +
      "<textarea name='expert' class='mono' style='width:100%;min-height:140px'>" + e(JSON.stringify(a.permissions || [], null, 2)) + "</textarea>" +
      "<label class='aide'><input type='checkbox' name='utiliser_expert'> utiliser ces règles à la place des interrupteurs</label></details>" +
      "<label class='aide' style='display:block;margin-top:10px'><input type='checkbox' name='disabled'" + (a.disabled ? " checked" : "") + "> désactiver cet agent (il disparaît du menu, sans être supprimé)</label>" +
      "<div class='ligne' style='margin-top:16px;flex-wrap:wrap'>" +
      (nouveau ? "" : "<button type='button' class='btn' data-action='dupliquer'>Dupliquer</button>") +
      (!nouveau && a.mode !== "subagent" && a.id !== etat.defaut ? "<button type='button' class='btn' data-action='par-defaut'>Mettre par défaut</button>" : "") +
      (vous && !nouveau ? "<button type='button' class='btn dang' data-action='supprimer-agent'>Supprimer</button>" : "") +
      "<span class='espace'></span><button type='submit' class='btn prim'>Enregistrer</button></div>" +
      "<div class='statut'>✓ Enregistrer = sauvegarde de la config, vérification par OpenCode, puis rechargement de l'agent ouvert.</div></form>";
  }

  APRES.agents = function () {
    $$("[data-agent]").forEach(function (b) { b.addEventListener("click", function () { aller("agents", b.dataset.agent); }); });
    var form = $("#form-agent");
    if (!form) return;
    var modifies = {};
    $$(".segm", form).forEach(function (s) {
      $$("button", s).forEach(function (b) {
        b.addEventListener("click", function () {
          $$("button", s).forEach(function (x) { x.setAttribute("aria-pressed", x === b); });
          modifies[s.dataset.droit] = b.dataset.valeur;
        });
      });
    });
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var f = form.elements, nouveau = form.dataset.nouveau === "true";
      var corps = { id: f.id.value.trim(), mode: f.mode.value, description: f.description.value, system: f.system.value,
        model: f.model.value, color: f.sans_couleur.checked ? "" : f.color.value, disabled: f.disabled.checked };
      if (!nouveau && form.dataset.id !== corps.id) corps.ancien_id = form.dataset.id;
      if (f.utiliser_expert.checked) {
        try { corps.permissions_expert = JSON.parse(f.expert.value || "[]"); } catch (err) { return toast("Mode expert : JSON invalide (" + err.message + ")", true); }
      } else if (nouveau) {
        corps.droits = {};
        $$(".segm", form).forEach(function (s) { var b = $("button[aria-pressed='true']", s); if (b) corps.droits[s.dataset.droit] = b.dataset.valeur; });
      } else if (Object.keys(modifies).length) {
        corps.droits = modifies;
      }
      modifier("/api/agent", corps).then(function () { aller("agents", corps.id); });
    });
    form.addEventListener("click", function (ev) {
      var action = ev.target.dataset.action, id = form.dataset.id;
      if (action === "supprimer-agent" && confirmer("Supprimer l'agent « " + id + " » ? (La config d'avant est sauvegardée.)")) {
        modifier("/api/agent/supprimer", { id: id }).then(function () { aller("agents"); });
      }
      if (action === "par-defaut") modifier("/api/regler", { defaut: id });
      if (action === "dupliquer") {
        var a = agent(id), copie = prompt("Nom de la copie (lettres minuscules, chiffres, tirets) :", id + "-copie");
        if (!copie) return;
        modifier("/api/agent", { id: copie.trim(), mode: a.mode === "primary" || a.mode === "all" ? a.mode : "subagent", description: a.description, system: a.system,
          model: a.model, color: a.color, permissions_expert: a.permissions || [] }).then(function () { aller("agents", copie.trim()); });
      }
    });
  };

  // --- Équipes ---
  var choixEquipe = { nouveaux: [] };
  ECRANS.equipes = function () {
    var candidats = etat.agents.filter(function (a) { return a.mode !== "primary" && a.origine !== "interne" && !a.disabled; });
    var existantes = equipes();
    return "<h1>Créer une équipe</h1><p class='sous'>Un agent « chef » reçoit votre demande, la découpe et confie chaque morceau à ses sous-agents, en parallèle quand c'est possible. Il ne pourra appeler que les sous-agents cochés.</p>" +
      "<form id='form-equipe' class='carte'>" +
      "<div class='champs2'><div class='champ'><label>Nom du chef d'équipe (identifiant)</label><input name='chef' placeholder='ex. equipe-web'></div>" +
      "<div class='champ'><label>Sa mission en une phrase</label><input name='mission' placeholder='ex. analyser un site, corriger son code et vérifier le résultat'></div></div>" +
      "<div class='champ'><label>Sous-agents de l'équipe</label></div><div class='choix'>" +
      candidats.map(function (a) {
        return "<label><input type='checkbox' name='membre' value='" + e(a.id) + "'><span><b>" + e(a.nom) + "</b><br><small>" + e(a.description || a.resume) + "</small></span></label>";
      }).join("") +
      choixEquipe.nouveaux.map(function (m, i) {
        return "<label><input type='checkbox' checked data-nouveau='" + i + "'><span><b>" + e(m.nom) + "</b> <span class='badge acc'>nouveau</span><br><small>" + e(m.desc) + "</small></span></label>";
      }).join("") + "</div>" +
      "<div class='ligne' style='margin-top:10px'><select id='ajout-modele' class='mini'><option value=''>+ Ajouter un rôle depuis la bibliothèque…</option>" +
      (window.BIBLIO || []).map(function (m, i) { return "<option value='" + i + "'>" + e(m.cat + " — " + m.nom) + "</option>"; }).join("") + "</select></div>" +
      "<h2>Ce que l'Atelier va écrire</h2><pre id='apercu-equipe'></pre>" +
      "<div class='ligne' style='margin-top:12px'><span class='espace'></span><button class='btn prim' type='submit'>Créer l'équipe</button></div>" +
      "<div class='statut'>✓ Avant d'écrire : sauvegarde, puis vérification par OpenCode. Si OpenCode refuse, rien n'est modifié.</div></form>" +
      "<h2>Équipes existantes</h2>" + (existantes.length ? existantes.map(function (a) {
        return "<div class='carte ligne' style='margin-bottom:8px'><span class='puce' style='background:" + e(a.color || "var(--violet)") + "'></span><div><b>" + e(a.nom) +
          "</b><br><small class='etiq'>" + e(a.droits.sousagents.liste.join(" · ")) + "</small></div><span class='espace'></span><button class='btn' data-aller='agents/" + e(a.id) + "'>Ouvrir</button></div>";
      }).join("") : "<div class='carte vide'>Aucune équipe pour l'instant.</div>");
  };
  APRES.equipes = function () {
    var form = $("#form-equipe");
    function membres() {
      return $$("input[name='membre']:checked", form).map(function (i) { return i.value; })
        .concat($$("input[data-nouveau]:checked", form).map(function (i) { return choixEquipe.nouveaux[+i.dataset.nouveau].nom; }));
    }
    function apercu() {
      var m = membres(), mission = form.elements.mission.value || "(sa mission)";
      $("#apercu-equipe").textContent = "Consignes du chef (modifiables ensuite) :\n« Tu diriges une équipe de " + m.length + " sous-agent(s). Ta mission : " + mission +
        "\n" + m.map(function (x) { return "- " + x; }).join("\n") + "\nDécoupe chaque demande, confie chaque tâche au bon sous-agent, puis fais une synthèse. »\n\n" +
        "Droits du chef : appeler " + (m.join(", ") || "(personne)") + " → Toujours · tout autre sous-agent → Jamais";
    }
    form.addEventListener("input", apercu);
    form.addEventListener("change", apercu);
    apercu();
    $("#ajout-modele").addEventListener("change", function (ev) {
      if (ev.target.value === "") return;
      choixEquipe.nouveaux.push(window.BIBLIO[+ev.target.value]);
      afficher();
    });
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var nouveaux = $$("input[data-nouveau]:checked", form).map(function (i) { return choixEquipe.nouveaux[+i.dataset.nouveau]; });
      modifier("/api/equipe", { chef: form.elements.chef.value.trim(), mission: form.elements.mission.value.trim(),
        membres: $$("input[name='membre']:checked", form).map(function (i) { return i.value; }), nouveaux: nouveaux })
        .then(function (r) { choixEquipe.nouveaux = []; aller("agents", r.id); });
    });
  };

  // --- Bibliothèque ---
  var filtreBiblio = { cat: "Tout", q: "" };
  var BADGES = { lecture: "<span class='badge ok'>lecture seule</span>", modif: "<span class='badge att'>modifie des fichiers</span>",
    shell: "<span class='badge att'>commandes</span>", web: "<span class='badge acc'>internet</span>", sous: "<span class='badge acc'>sous-agents</span>" };
  ECRANS.biblio = function () {
    var biblio = window.BIBLIO || [];
    var cats = ["Tout"].concat(biblio.map(function (m) { return m.cat; }).filter(function (c, i, l) { return l.indexOf(c) === i; }));
    return "<h1>Bibliothèque de modèles d'agents</h1><p class='sous'>" + biblio.length + " agents prêts à l'emploi. « Ajouter » en crée une copie dans Mes agents (comme sous-agent), que vous pouvez ensuite modifier ou mettre dans une équipe.</p>" +
      "<input class='recherche' id='cherche-biblio' placeholder='Chercher un rôle (ex. sécurité, documentation, SQL)…' value='" + e(filtreBiblio.q) + "'>" +
      "<div class='filtres'>" + cats.map(function (c) { return "<button data-cat='" + e(c) + "' aria-pressed='" + (c === filtreBiblio.cat) + "'>" + e(c) + "</button>"; }).join("") + "</div>" +
      "<div class='grille' id='grille-biblio'></div>";
  };
  APRES.biblio = function () {
    function dessiner() {
      var q = filtreBiblio.q.toLowerCase();
      $("#grille-biblio").innerHTML = (window.BIBLIO || []).map(function (m, i) {
        if ((filtreBiblio.cat !== "Tout" && m.cat !== filtreBiblio.cat) || (q && (m.nom + m.desc + m.cat).toLowerCase().indexOf(q) < 0)) return "";
        return "<div class='carte modele'><div class='ligne'><h4>" + e(m.nom) + "</h4><span class='espace'></span><span class='etiq'>" + e(m.cat) + "</span></div><p>" + e(m.desc) +
          "</p><div class='ligne'>" + m.droits.map(function (x) { return BADGES[x] || ""; }).join("") + "<span class='espace'></span><button class='btn' data-modele='" + i + "'>+ Ajouter</button></div></div>";
      }).join("") || "<div class='vide'>Aucun modèle ne correspond.</div>";
    }
    dessiner();
    $("#cherche-biblio").addEventListener("input", function (ev) { filtreBiblio.q = ev.target.value; dessiner(); });
    $$("[data-cat]").forEach(function (b) { b.addEventListener("click", function () { filtreBiblio.cat = b.dataset.cat; afficher(); }); });
    $("#grille-biblio").addEventListener("click", function (ev) {
      var i = ev.target.dataset.modele;
      if (i === undefined) return;
      modifier("/api/agent/depuis-modele", { modele: window.BIBLIO[+i] }).then(function (r) { toast("Agent « " + r.id + " » ajouté : ouvrez Mes agents pour le régler."); });
    });
  };

  // --- Outils de base ---
  var OUTILS = [
    ["read", "Lire un fichier, ou lister le contenu d'un dossier.", "read"],
    ["write", "Créer un fichier, ou le remplacer entièrement.", "edit"],
    ["edit", "Modifier un passage précis d'un fichier.", "edit"],
    ["patch", "Faire plusieurs modifications d'un coup (ajouter, changer, supprimer des fichiers).", "edit"],
    ["glob", "Trouver des fichiers par leur nom (ex. src/**/*.ts).", "glob"],
    ["grep", "Chercher un texte dans le contenu des fichiers.", "grep"],
    ["shell", "Lancer une commande (PowerShell, cmd, git, python…).", "shell"],
    ["webfetch", "Lire une page web à une adresse précise.", "webfetch"],
    ["websearch", "Faire une recherche sur internet.", "websearch"],
    ["subagent", "Confier une tâche à un sous-agent, qui travaille dans sa propre conversation.", "subagent"],
    ["skill", "Charger une fiche de méthode (skill).", "skill"],
    ["question", "Vous poser une question à choix pendant le travail.", "question"],
    ["ressources MCP", "Lister et lire les documents fournis par un MCP.", "opencode_read_mcp_resource"],
    ["outils des MCP", "Chaque MCP ajoute ses propres outils (ex. les 207 outils de REA).", "nom du MCP"]
  ];
  ECRANS.outils = function () {
    return "<h1>Outils de base</h1><p class='sous'>Les « mains » de l'agent : ce qu'il peut faire, au-delà de répondre. Les droits de chaque agent (Mes agents) et les règles générales (Sécurité) disent lesquels il a le droit d'utiliser.</p>" +
      "<div class='carte'><table><tr><th>Outil</th><th>Ce qu'il fait</th><th>Réglé par le droit</th></tr>" +
      OUTILS.map(function (o) { return "<tr><td><code>" + e(o[0]) + "</code></td><td>" + e(o[1]) + "</td><td><code>" + e(o[2]) + "</code></td></tr>"; }).join("") + "</table></div>";
  };

  // --- MCP ---
  var catalogue = null, mcpEdite = null;
  ECRANS.mcp = function () {
    var lignes = etat.mcp.map(function (m) {
      return "<tr><td><button class='inter' data-mcp-actif='" + e(m.nom) + "' aria-pressed='" + m.actif + "' aria-label='Activer " + e(m.nom) + "'></button></td><td><b>" + e(m.nom) + "</b></td>" +
        "<td class='mono'>" + e((m.command || [m.url]).join(" ")) + "</td><td><span id='test-" + e(m.nom) + "' class='etiq'>" + (m.actif ? "" : "désactivé") + "</span></td>" +
        "<td style='white-space:nowrap'><button class='btn petit' data-mcp-tester='" + e(m.nom) + "'>Tester</button> <button class='btn petit' data-mcp-modifier='" + e(m.nom) + "'>Modifier</button> " +
        "<button class='btn petit dang' data-mcp-retirer='" + e(m.nom) + "'>Retirer</button></td></tr>";
    }).join("");
    return "<div class='ligne'><div><h1>MCP</h1><p class='sous'>Des modules qui ajoutent des outils à l'agent (analyse, navigateur, recherche web…). Les valeurs secrètes ne s'affichent jamais.</p></div><span class='espace'></span>" +
      "<button class='btn prim' data-action='mcp-nouveau'>+ Ajouter à la main</button></div>" +
      "<div class='carte'>" + (lignes ? "<table><tr><th></th><th>MCP</th><th>Commande</th><th>État</th><th></th></tr>" + lignes + "</table>" : "<div class='vide'>Aucun MCP.</div>") + "</div>" +
      "<div id='form-mcp-zone'>" + (mcpEdite ? formMcp(mcpEdite) : "") + "</div>" +
      "<h2>Ajouter depuis vos MCP de C:\\MCP</h2><div class='grille' id='catalogue'><div class='vide'>Lecture du catalogue…</div></div>";
  };
  function formMcp(m) {
    var variables = (m.variables || []).map(function (v) {
      return "<div class='ligne'><input class='mono' value='" + e(v) + "' data-var-nom readonly><input type='password' placeholder='•••••• (valeur gardée)' data-var-valeur><label class='aide'><input type='checkbox' data-var-retirer> retirer</label></div>";
    }).join("");
    return "<form id='form-mcp' class='carte' data-ancien='" + e(m.nom || "") + "' style='margin-top:14px'><h2 style='margin-top:0'>" + (m.nom ? "Modifier « " + e(m.nom) + " »" : "Nouveau MCP") + "</h2>" +
      "<div class='champs2'><div class='champ'><label>Nom</label><input name='nom' value='" + e(m.nom || "") + "' placeholder='ex. mon-mcp'></div>" +
      "<div class='champ'><label>Type</label><select name='type'><option value='local'" + (m.type !== "remote" ? " selected" : "") + ">Local (un programme sur ce PC)</option><option value='remote'" + (m.type === "remote" ? " selected" : "") + ">Distant (une adresse web)</option></select></div></div>" +
      "<div class='champ'><label>Commande : le programme sur la 1re ligne, puis un argument par ligne (ou l'adresse pour un MCP distant)</label><textarea name='commande' class='mono'>" +
      e((m.command || (m.url ? [m.url] : [])).join("\n")) + "</textarea></div>" +
      "<div class='champs2'><div class='champ'><label>Dossier de travail (facultatif)</label><input name='cwd' class='mono' value='" + e(m.cwd || "") + "'></div>" +
      "<div class='champ'><label>Délai de démarrage (secondes)</label><input name='delai' type='number' min='5' value='" + e(((m.timeout || {}).startup || 30000) / 1000) + "'></div></div>" +
      "<div class='champ'><label>Variables d'environnement</label><div class='lignes-var' id='vars'>" + variables + "</div>" +
      "<button type='button' class='btn petit' data-action='ajout-var' style='margin-top:6px'>+ Variable</button></div>" +
      "<div class='ligne'><span class='aide'>Une valeur laissée vide garde la valeur actuelle.</span><span class='espace'></span><button type='button' class='btn' data-action='mcp-annuler'>Annuler</button><button class='btn prim' type='submit'>Enregistrer</button></div></form>";
  }
  APRES.mcp = function () {
    $$("[data-mcp-actif]").forEach(function (b) {
      b.addEventListener("click", function () { modifier("/api/mcp/actif", { nom: b.dataset.mcpActif, actif: b.getAttribute("aria-pressed") !== "true" }); });
    });
    $$("[data-mcp-tester]").forEach(function (b) {
      b.addEventListener("click", function () {
        var zone = document.getElementById("test-" + b.dataset.mcpTester);
        zone.innerHTML = "<span class='roue'></span>test…";
        appel("POST", "/api/mcp/tester", { nom: b.dataset.mcpTester }).then(function (r) {
          zone.innerHTML = "<span class='badge " + (r.ok ? "ok" : r.ok === false ? "non" : "") + "'>" + e(r.message) + "</span>";
        }).catch(function (err) { zone.innerHTML = "<span class='badge non'>" + e(err.message) + "</span>"; });
      });
    });
    $$("[data-mcp-modifier]").forEach(function (b) {
      b.addEventListener("click", function () { mcpEdite = etat.mcp.find(function (m) { return m.nom === b.dataset.mcpModifier; }); afficher(); });
    });
    $$("[data-mcp-retirer]").forEach(function (b) {
      b.addEventListener("click", function () {
        if (confirmer("Retirer le MCP « " + b.dataset.mcpRetirer + " » de la config ? (Sauvegardé avant.)")) modifier("/api/mcp/supprimer", { nom: b.dataset.mcpRetirer });
      });
    });
    var form = $("#form-mcp");
    if (form) {
      form.addEventListener("click", function (ev) {
        if (ev.target.dataset.action === "ajout-var") {
          var div = document.createElement("div");
          div.className = "ligne";
          div.innerHTML = "<input class='mono' placeholder='NOM_VARIABLE' data-var-nom><input type='password' placeholder='valeur' data-var-valeur>";
          $("#vars").appendChild(div);
        }
        if (ev.target.dataset.action === "mcp-annuler") { mcpEdite = null; afficher(); }
      });
      form.addEventListener("submit", function (ev) {
        ev.preventDefault();
        var f = form.elements, lignes = f.commande.value.split(/\r?\n/).map(function (x) { return x.trim(); }).filter(Boolean);
        var conf = { type: f.type.value };
        if (conf.type === "remote") conf.url = lignes[0] || ""; else conf.command = lignes;
        if (f.cwd.value.trim()) conf.cwd = f.cwd.value.trim();
        conf.timeout = { startup: Math.round(+f.delai.value * 1000) || 30000 };
        var env = {};
        $$("#vars .ligne").forEach(function (l) {
          var nom = $("[data-var-nom]", l).value.trim(), valeur = $("[data-var-valeur]", l).value, retirer = $("[data-var-retirer]", l);
          if (!nom) return;
          env[nom] = retirer && retirer.checked ? "" : (valeur === "" ? null : valeur);
        });
        conf[conf.type === "remote" ? "headers" : "environment"] = env;
        modifier("/api/mcp", { nom: f.nom.value.trim(), ancien_nom: form.dataset.ancien || undefined, conf: conf }).then(function () { mcpEdite = null; afficher(); });
      });
    }
    var actionNouveau = $("[data-action='mcp-nouveau']");
    actionNouveau.addEventListener("click", function () { mcpEdite = { nom: "", type: "local", variables: [] }; afficher(); });
    (catalogue ? Promise.resolve(catalogue) : appel("GET", "/api/catalogue")).then(function (liste) {
      catalogue = liste;
      $("#catalogue").innerHTML = liste.map(function (m) {
        return "<div class='carte modele'><div class='ligne'><h4>" + e(m.nom) + "</h4><span class='espace'></span><span class='etiq'>" + e(m.categorie) + "</span></div><p class='court' title='" + e(m.description) + "'>" + e(m.description) + "</p>" +
          (m.variables.length ? "<p class='aide'>Variables recopiées (sans les afficher) : " + e(m.variables.join(", ")) + "</p>" : "") +
          "<div class='ligne'>" + (m.installe ? "<span class='badge ok'>déjà branché</span>" : m.ajoutable ?
            "<button class='btn petit' data-cat-tester='" + e(m.nom) + "'>Tester</button><span class='espace'></span><button class='btn' data-cat-ajouter='" + e(m.nom) + "'>+ Ajouter</button>"
            : "<span class='badge'>commande inconnue : ajout à la main</span>") + "<span class='etiq' id='cat-" + e(m.nom) + "'></span></div></div>";
      }).join("");
      $$("[data-cat-ajouter]").forEach(function (b) {
        b.addEventListener("click", function () { modifier("/api/mcp/catalogue", { nom: b.dataset.catAjouter }).then(function () { catalogue = null; afficher(); }); });
      });
      $$("[data-cat-tester]").forEach(function (b) {
        b.addEventListener("click", function () {
          var zone = document.getElementById("cat-" + b.dataset.catTester);
          zone.innerHTML = " <span class='roue'></span>";
          appel("POST", "/api/mcp/tester", { nom: b.dataset.catTester, catalogue: true }).then(function (r) { zone.textContent = " " + r.message; })
            .catch(function (err) { zone.textContent = " " + err.message; });
        });
      });
    }).catch(function (err) { $("#catalogue").innerHTML = "<div class='vide'>" + e(err.message) + "</div>"; });
  };

  // --- Modèles et GPU ---
  ECRANS.modeles = function () {
    var gpu = services && services.gpu, ia = services && services.ia_locale;
    var parAgent = etat.agents.filter(function (a) { return a.origine !== "interne"; }).map(function (a) {
      return "<tr><td>" + e(a.nom) + "</td><td><select class='mini' data-modele-agent='" + e(a.id) + "'>" + optionsModeles(a.model, true) + "</select></td></tr>";
    }).join("");
    var pods = gpu ? (gpu.pods || []).map(function (p) {
      return "<div class='ligne' style='margin:4px 0'><span class='pastille " + (p.allume ? "ok" : "") + "'>" + e(p.nom) + "</span><span class='etiq'>" + e(p.gpu) + (p.prix ? " · " + e(p.prix) + " $/h" : "") + "</span></div>";
    }).join("") : "";
    return "<h1>Modèles et GPU</h1><p class='sous'>Quel « cerveau » utilise chaque agent, et ce qui tourne (et coûte) en ce moment.</p><div class='grille'>" +
      "<div class='carte'><div class='ligne'><b>GPU loué RunPod</b><span class='espace'></span>" + (gpu ? "<span class='badge " + (gpu.etat === "allume" ? "ok" : gpu.etat === "eteint" ? "" : "att") + "'>" +
        e({ allume: "allumé" + (gpu.prix_heure ? " · " + gpu.prix_heure + " $/h" : ""), eteint: "éteint", inconnu: "état inconnu" }[gpu.etat]) + "</span>" : "<span class='roue'></span>") + "</div>" +
      pods + (gpu && gpu.detail ? "<p class='aide'>" + e(gpu.detail) + "</p>" : "") +
      "<div class='ligne' style='margin-top:10px'><button class='btn' data-action='gpu-actualiser'>Actualiser</button><span class='espace'></span>" +
      (gpu && gpu.etat === "allume" ? "<button class='btn dang' data-action='gpu-arreter'>Arrêter le GPU</button>" : "") + "</div></div>" +
      "<div class='carte'><div class='ligne'><b>IA locale (RTX 5090)</b><span class='espace'></span>" + (ia ? "<span class='badge " + (ia.etat === "prete" ? "ok" : "") + "'>" + (ia.etat === "prete" ? "prête" : "arrêtée") + "</span>" : "") + "</div>" +
      "<p class='etiq'>llama-swap 127.0.0.1:8090 · " + (ia && ia.charges.length ? "en mémoire : " + e(ia.charges.join(", ")) : "aucun modèle chargé (il se charge à la demande)") + "</p></div></div>" +
      "<h2>Modèle par défaut</h2><div class='carte champ'><select id='modele-defaut'>" + optionsModeles(etat.modele, false) + "</select></div>" +
      "<h2>Modèle de chaque agent</h2><div class='carte'><table><tr><th>Agent</th><th>Modèle</th></tr>" + parAgent + "</table></div>";
  };
  APRES.modeles = function () {
    $("#modele-defaut").addEventListener("change", function (ev) { modifier("/api/regler", { modele: ev.target.value }); });
    $$("[data-modele-agent]").forEach(function (s) {
      s.addEventListener("change", function () { modifier("/api/agent", { id: s.dataset.modeleAgent, model: s.value }); });
    });
    var actu = $("[data-action='gpu-actualiser']");
    if (actu) actu.addEventListener("click", function () { lireServices(true); });
    var arret = $("[data-action='gpu-arreter']");
    if (arret) arret.addEventListener("click", function () {
      if (!confirmer("Arrêter le GPU loué ? Le compteur s'arrête ; vous pourrez le relancer depuis RunPod.")) return;
      attente("Arrêt du GPU…");
      appel("POST", "/api/gpu/arreter", {}).then(function (r) {
        fermerVoile();
        toast(r.pods.map(function (p) { return p.nom + (p.ok ? " : arrêté" : " : échec (" + p.detail + ")"); }).join(" · ") || "Aucun GPU allumé.");
        lireServices(true);
      }).catch(function (err) { fermerVoile(); toast(err.message, true); });
    });
  };

  // --- Commandes / ---
  ECRANS.commandes = function () {
    var choisie = detail === "+" ? { nom: "", template: "", description: "", agent: "", model: "" } : etat.commandes.find(function (c) { return c.nom === detail; });
    var liste = etat.commandes.map(function (c) {
      return "<button class='item' data-commande='" + e(c.nom) + "' aria-current='" + (c.nom === detail) + "'><span class='puce' style='background:var(--acc)'></span><span>/" + e(c.nom) + "<small>" + e(c.description || c.template.slice(0, 80)) + "</small></span></button>";
    }).join("");
    var agentsMenu = etat.agents.filter(function (a) { return a.origine !== "interne"; });
    return "<div class='ligne'><div><h1>Commandes /</h1><p class='sous'>Des raccourcis que <b>vous</b> tapez dans la discussion : ils envoient un message préparé à l'agent choisi.</p></div><span class='espace'></span>" +
      "<button class='btn prim' data-aller='commandes/+'>+ Nouvelle commande</button></div>" +
      "<div class='note'><b>Commande / ou skill ?</b> Une <b>commande /</b>, c'est vous qui la lancez (<code>/audit-site exemple.com</code>). Une <b>skill</b>, c'est une fiche de méthode que <b>l'agent</b> charge tout seul quand la tâche s'y prête — l'équivalent des skills de Claude Code (écran Skills).</div>" +
      "<div class='deux'><div class='liste'>" + (liste || "<div class='vide'>Aucune commande.</div>") + "</div><div class='carte'>" +
      (choisie ? "<form id='form-commande' data-ancien='" + e(choisie.nom) + "'>" +
        "<div class='champs2'><div class='champ'><label>Nom (tapé après /)</label><input name='nom' class='mono' value='" + e(choisie.nom) + "' placeholder='audit-site'></div>" +
        "<div class='champ'><label>Agent qui la reçoit</label><select name='agent'><option value=''>L'agent en cours</option>" + agentsMenu.map(function (a) {
          return "<option value='" + e(a.id) + "'" + (a.id === choisie.agent ? " selected" : "") + ">" + e(a.nom) + "</option>"; }).join("") + "</select></div></div>" +
        "<div class='champ'><label>Description (affichée dans la liste « / »)</label><input name='description' value='" + e(choisie.description || "") + "'></div>" +
        "<div class='champ'><label>Message envoyé (<code>$ARGUMENTS</code> = ce que vous tapez après la commande)</label><textarea name='template' style='min-height:140px'>" + e(choisie.template) + "</textarea></div>" +
        "<div class='champs2'><div class='champ'><label>Modèle (facultatif)</label><select name='model'>" + optionsModeles(choisie.model, true) + "</select></div>" +
        "<div class='champ'><label>&nbsp;</label><label class='aide'><input type='checkbox' name='subagent'" + (choisie.subagent ? " checked" : "") + "> lancer en sous-agent (dans une conversation à part)</label></div></div>" +
        "<div class='ligne'>" + (choisie.nom ? "<button type='button' class='btn dang' data-action='supprimer-commande'>Supprimer</button>" : "") + "<span class='espace'></span><button class='btn prim' type='submit'>Enregistrer</button></div></form>"
        : "<div class='vide'>Choisissez une commande, ou créez-en une.</div>") + "</div></div>";
  };
  APRES.commandes = function () {
    $$("[data-commande]").forEach(function (b) { b.addEventListener("click", function () { aller("commandes", b.dataset.commande); }); });
    var form = $("#form-commande");
    if (!form) return;
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var f = form.elements;
      modifier("/api/commande", { nom: f.nom.value.trim(), ancien_nom: form.dataset.ancien || undefined, agent: f.agent.value, description: f.description.value,
        template: f.template.value, model: f.model.value, subagent: f.subagent.checked }).then(function () { aller("commandes", f.nom.value.trim().replace(/^\//, "")); });
    });
    form.addEventListener("click", function (ev) {
      if (ev.target.dataset.action === "supprimer-commande" && confirmer("Supprimer la commande /" + form.dataset.ancien + " ?")) {
        modifier("/api/commande/supprimer", { nom: form.dataset.ancien }).then(function () { aller("commandes"); });
      }
    });
  };

  // --- Skills ---
  ECRANS.skills = function () {
    var choisie = detail === "+" ? { nom: "", description: "", contenu: "", autorisee: true } : etat.skills.find(function (s) { return s.nom === detail; });
    var liste = etat.skills.map(function (s) {
      return "<button class='item' data-skill='" + e(s.nom) + "' aria-current='" + (s.nom === detail) + "'><span class='puce' style='background:" + (s.autorisee ? "var(--ok)" : "var(--faible)") + "'></span><span>" + e(s.nom) +
        (s.autorisee ? "" : " <span class='badge'>non autorisée</span>") + "<small>" + e(s.description) + "</small></span></button>";
    }).join("");
    return "<div class='ligne'><div><h1>Skills</h1><p class='sous'>Les fiches de méthode que l'agent charge tout seul quand la tâche s'y prête. Comme les skills de Claude Code.</p></div><span class='espace'></span>" +
      "<button class='btn prim' data-aller='skills/+'>+ Nouvelle skill</button></div>" +
      "<div class='deux'><div class='liste'>" + (liste || "<div class='vide'>Aucune skill.</div>") + "</div><div class='carte'>" +
      (choisie ? "<form id='form-skill' data-ancien='" + e(choisie.nom) + "'>" +
        "<div class='champ'><label>Nom</label><input name='nom' class='mono' value='" + e(choisie.nom) + "' placeholder='audit-site'></div>" +
        "<div class='champ'><label>Quand l'agent doit la charger (description, lue par l'agent pour décider)</label><input name='description' value='" + e(choisie.description) + "'></div>" +
        "<div class='champ'><label>Contenu de la fiche (Markdown)</label><textarea name='contenu' class='mono' style='min-height:260px'>" + e(choisie.contenu) + "</textarea></div>" +
        "<label class='aide'><input type='checkbox' name='autoriser'" + (choisie.autorisee ? " checked" : "") + "> autoriser tous les agents à la charger (sinon vos règles la bloquent)</label>" +
        "<div class='ligne' style='margin-top:12px'>" + (choisie.nom ? "<button type='button' class='btn dang' data-action='supprimer-skill'>Mettre de côté</button>" : "") +
        "<span class='espace'></span><button class='btn prim' type='submit'>Enregistrer</button></div></form>"
        : "<div class='vide'>Choisissez une skill, ou créez-en une.</div>") + "</div></div>";
  };
  APRES.skills = function () {
    $$("[data-skill]").forEach(function (b) { b.addEventListener("click", function () { aller("skills", b.dataset.skill); }); });
    var form = $("#form-skill");
    if (!form) return;
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var f = form.elements;
      modifier("/api/skill", { nom: f.nom.value.trim(), ancien_nom: form.dataset.ancien || undefined, description: f.description.value,
        contenu: f.contenu.value, autoriser: f.autoriser.checked }).then(function () { aller("skills", f.nom.value.trim()); });
    });
    form.addEventListener("click", function (ev) {
      if (ev.target.dataset.action === "supprimer-skill" && confirmer("Mettre la skill « " + form.dataset.ancien + " » de côté ? Elle est rangée dans les sauvegardes, pas effacée.")) {
        modifier("/api/skill/supprimer", { nom: form.dataset.ancien }).then(function () { aller("skills"); });
      }
    });
  };

  // --- Consignes communes ---
  ECRANS.consignes = function () {
    return "<h1>Consignes communes</h1><p class='sous'>Lues par tous les agents au début de chaque session (fichier <code>AGENTS.md</code>).</p>" +
      "<form id='form-consignes' class='carte champ'><textarea name='texte' class='mono' style='min-height:440px'>" + e(etat.consignes) + "</textarea>" +
      "<div class='ligne' style='margin-top:10px'><span class='aide'>Une sauvegarde est faite avant chaque enregistrement.</span><span class='espace'></span><button class='btn prim' type='submit'>Enregistrer</button></div></form>";
  };
  APRES.consignes = function () {
    $("#form-consignes").addEventListener("submit", function (ev) {
      ev.preventDefault();
      modifier("/api/consignes", { texte: ev.target.elements.texte.value }, "Enregistrement…");
    });
  };

  // --- Sécurité ---
  var EFFET_TEXTE = { allow: "Toujours", ask: "Sur demande", deny: "Jamais" };
  var ACTIONS = ["shell", "edit", "read", "webfetch", "websearch", "subagent", "skill", "external_directory", "glob", "grep", "question", "*"];
  function decrire(r) {
    var a = { shell: "Lancer la commande", edit: "Modifier", read: "Lire", webfetch: "Lire la page web", websearch: "Chercher sur internet", subagent: "Appeler le sous-agent",
      skill: "Charger la skill", external_directory: "Sortir du dossier de l'agent vers", glob: "Chercher des fichiers", grep: "Chercher du texte", question: "Vous poser une question" }[r.action] || r.action;
    return a + " <code>" + e(r.resource) + "</code>";
  }
  ECRANS.securite = function () {
    var lignes = etat.securite.map(function (r, i) {
      if (r.protegee) return "<tr><td>🔒 " + decrire(r) + "</td><td><span class='badge non'>" + EFFET_TEXTE[r.effect] + "</span></td><td class='aide'>protège l'installation</td></tr>";
      return "<tr data-regle='" + i + "'><td><select class='mini' data-champ='action'>" + ACTIONS.map(function (a) { return "<option" + (a === r.action ? " selected" : "") + ">" + a + "</option>"; }).join("") +
        "</select> <input class='mini mono' data-champ='resource' value='" + e(r.resource) + "' style='width:240px'></td><td><select class='mini' data-champ='effect'>" +
        ["allow", "ask", "deny"].map(function (x) { return "<option value='" + x + "'" + (x === r.effect ? " selected" : "") + ">" + EFFET_TEXTE[x] + "</option>"; }).join("") +
        "</select></td><td><button class='btn petit dang' data-retirer-regle='" + i + "'>Retirer</button></td></tr>";
    }).join("");
    var politiques = etat.politiques.map(function (p) { return "<tr><td>" + e(p.action) + " <code>" + e(p.resource) + "</code></td><td>" + EFFET_TEXTE[p.effect] + "</td></tr>"; }).join("");
    return "<h1>Sécurité</h1><p class='sous'>Règles valables pour tous les agents (sauf réglage contraire dans un agent). La dernière règle qui correspond gagne. Les lignes 🔒 protègent l'installation et ne peuvent pas être retirées ici.</p>" +
      "<div class='carte'><table id='table-regles'><tr><th>Règle</th><th>Effet</th><th></th></tr>" + lignes + "</table>" +
      "<div class='ligne' style='margin-top:10px'><button class='btn' data-action='ajout-regle'>+ Ajouter une règle</button><span class='espace'></span><button class='btn prim' data-action='enregistrer-regles'>Enregistrer les règles</button></div></div>" +
      (politiques ? "<h2>Fournisseurs de modèles autorisés</h2><div class='carte'><table>" + politiques + "</table></div>" : "");
  };
  APRES.securite = function () {
    var regles = etat.securite.map(function (r) { return { action: r.action, resource: r.resource, effect: r.effect, protegee: r.protegee }; });
    function lire() {
      $$("tr[data-regle]").forEach(function (tr) {
        var r = regles[+tr.dataset.regle];
        $$("[data-champ]", tr).forEach(function (c) { r[c.dataset.champ] = c.value; });
      });
    }
    $$("[data-retirer-regle]").forEach(function (b) {
      b.addEventListener("click", function () { lire(); regles[+b.dataset.retirerRegle].retiree = true; b.closest("tr").remove(); });
    });
    $("[data-action='ajout-regle']").addEventListener("click", function () {
      lire();
      regles.push({ action: "shell", resource: "", effect: "ask" });
      var i = regles.length - 1, tr = document.createElement("tr");
      tr.dataset.regle = i;
      tr.innerHTML = "<td><select class='mini' data-champ='action'>" + ACTIONS.map(function (a) { return "<option>" + a + "</option>"; }).join("") +
        "</select> <input class='mini mono' data-champ='resource' placeholder='ex. npm install *' style='width:240px'></td><td><select class='mini' data-champ='effect'><option value='allow'>Toujours</option><option value='ask' selected>Sur demande</option><option value='deny'>Jamais</option></select></td><td></td>";
      $("#table-regles").appendChild(tr);
    });
    $("[data-action='enregistrer-regles']").addEventListener("click", function () {
      lire();
      modifier("/api/securite", { regles: regles.filter(function (r) { return !r.protegee && !r.retiree && r.resource; }) });
    });
  };

  // --- Sauvegardes ---
  var GENRES = { config: "config", consignes: "consignes" };
  ECRANS.sauvegardes = function () {
    return "<h1>Sauvegardes</h1><p class='sous'>Une copie est faite avant chaque enregistrement. Les 20 dernières versions de chaque fichier sont gardées. Restaurer refait une sauvegarde avant.</p>" +
      "<div class='carte'>" + (etat.sauvegardes.length ? "<table><tr><th>Date</th><th>Fichier</th><th>Changement</th><th></th></tr>" + etat.sauvegardes.map(function (s) {
        return "<tr><td style='white-space:nowrap'>" + e(s.date) + "</td><td><span class='badge'>" + e(GENRES[s.genre] || s.genre) + "</span></td><td>" + e(s.resume) + "</td><td style='white-space:nowrap'>" +
          (s.dossier ? "" : "<button class='btn petit' data-comparer='" + e(s.id) + "'>Comparer</button> ") + "<button class='btn petit' data-restaurer='" + e(s.id) + "'>Restaurer</button></td></tr>";
      }).join("") + "</table>" : "<div class='vide'>Aucune sauvegarde pour l'instant : elles se créent à la première modification.</div>") + "</div>";
  };
  APRES.sauvegardes = function () {
    $$("[data-comparer]").forEach(function (b) {
      b.addEventListener("click", function () {
        appel("GET", "/api/comparer?id=" + encodeURIComponent(b.dataset.comparer)).then(function (r) {
          var html = (r.diff || "Aucune différence avec la version actuelle.").split("\n").map(function (l) {
            var c = l.startsWith("+") && !l.startsWith("+++") ? "plus" : l.startsWith("-") && !l.startsWith("---") ? "moins" : l.startsWith("@@") ? "info" : "";
            return "<span class='" + c + "'>" + e(l) + "</span>";
          }).join("\n");
          fenetre("<h2 style='margin-top:0'>Différences avec la version actuelle</h2><p class='aide'>En rouge : ce qui était dans la sauvegarde. En vert : ce qui est là maintenant.</p><div class='diff'>" + html + "</div>");
        }).catch(function (err) { toast(err.message, true); });
      });
    });
    $$("[data-restaurer]").forEach(function (b) {
      b.addEventListener("click", function () {
        if (confirmer("Revenir à cette version ? La version actuelle est sauvegardée avant.")) modifier("/api/restaurer", { id: b.dataset.restaurer });
      });
    });
  };

  // --- Guide ---
  ECRANS.guide = function () {
    return "<h1>Guide</h1><p class='sous'>Le mode d'emploi complet, écran par écran, avec des captures.</p>" +
      "<div class='carte ligne'><div><b>Ouvrir le guide</b><br><span class='etiq'>Premiers pas, agents, équipes, MCP, commandes et skills, que faire si quelque chose casse.</span></div><span class='espace'></span>" +
      "<a class='btn prim' href='/guide/index.html' target='_blank' rel='noopener'>Ouvrir</a></div>";
  };

  // ---------- Délégations globales ----------
  document.addEventListener("click", function (ev) {
    var cible = ev.target.closest("[data-aller]");
    if (cible) { var p = cible.dataset.aller.split("/"); aller(p[0], p[1]); }
    if (ev.target.dataset && ev.target.dataset.action === "fermer-voile") fermerVoile();
  });

  // ---------- État des services (pastilles) ----------
  function lireServices(forcer) {
    return appel("GET", "/api/services" + (forcer ? "?forcer" : "")).then(function (s) {
      services = s;
      var gpu = $("#p-gpu"), ia = $("#p-ia"), ag = $("#p-agent");
      gpu.className = "pastille " + (s.gpu.etat === "allume" ? "att" : s.gpu.etat === "eteint" ? "ok" : "");
      gpu.textContent = "GPU RunPod : " + ({ allume: "allumé" + (s.gpu.prix_heure ? " (" + s.gpu.prix_heure + " $/h)" : ""), eteint: "éteint", inconnu: "inconnu" }[s.gpu.etat]);
      ia.className = "pastille " + (s.ia_locale.etat === "prete" ? "ok" : "");
      ia.textContent = "IA locale : " + (s.ia_locale.etat === "prete" ? "prête" : "arrêtée");
      ag.className = "pastille " + (s.opencode ? "ok" : "");
      ag.textContent = "Agent : " + (s.opencode ? "ouvert" : "fermé");
      if (ecran === "modeles") afficher();
    }).catch(function () { /* pastilles laissées telles quelles */ });
  }

  // ---------- Démarrage ----------
  lireHash();
  charger().then(function () { lireServices(); }).catch(function (err) { principal.innerHTML = "<div class='vide'>Impossible de lire la config : " + e(err.message) + "</div>"; });
  setInterval(lireServices, 60000);
  setInterval(function () { appel("GET", "/api/battement").catch(function () {}); }, 30000);
})();
