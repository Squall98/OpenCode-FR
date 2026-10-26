// Bibliothèque de modèles d'agents : rôles inspirés de la collection VoltAgent « awesome-claude-code-subagents »
// (≈ 160 rôles, octobre 2026), choisis et décrits en français.
// droits : lecture = lecture seule, modif = modifie des fichiers, shell = lance des commandes, web = internet, sous = appelle des sous-agents
window.BIBLIO = [
  { cat: "Développement", nom: "Développeur fullstack", desc: "Réalise une fonctionnalité de bout en bout : interface, serveur, base de données, tests.", droits: ["modif", "shell"] },
  { cat: "Développement", nom: "Développeur backend", desc: "Écrit des API et services serveur solides : routes, validation, gestion des erreurs.", droits: ["modif", "shell"] },
  { cat: "Développement", nom: "Développeur frontend", desc: "Construit des interfaces web (React, Vue, Svelte…) propres, accessibles et réactives.", droits: ["modif", "shell"] },
  { cat: "Développement", nom: "Architecte d'API", desc: "Conçoit des API REST ou GraphQL claires : routes, formats, versions, documentation.", droits: ["lecture"] },
  { cat: "Développement", nom: "Développeur desktop", desc: "Applis de bureau (Electron, Tauri) : fenêtres, menus, mises à jour, empaquetage.", droits: ["modif", "shell"] },
  { cat: "Développement", nom: "Développeur mobile", desc: "Applis Android/iOS multiplateformes (React Native, Flutter, Expo).", droits: ["modif", "shell"] },
  { cat: "Développement", nom: "Spécialiste temps réel", desc: "WebSockets, webhooks et flux d'événements : connexion, reprise, ordre des messages.", droits: ["modif", "shell"] },
  { cat: "Développement", nom: "Développeur de CLI", desc: "Crée des outils en ligne de commande pratiques : options, aide, sorties lisibles.", droits: ["modif", "shell"] },
  { cat: "Développement", nom: "Développeur de MCP", desc: "Écrit des serveurs MCP (Python ou Node) qui ajoutent des outils à un agent.", droits: ["modif", "shell"] },
  { cat: "Développement", nom: "Intégrateur de paiement", desc: "Branche un service de paiement en mode test : formulaires, webhooks, remboursements.", droits: ["modif", "shell"] },

  { cat: "Langages", nom: "Expert Python", desc: "Code Python moderne : typage, environnements virtuels, paquets, tests avec pytest.", droits: ["modif", "shell"] },
  { cat: "Langages", nom: "Expert TypeScript", desc: "Types stricts, génériques, configuration de compilation, migration depuis JavaScript.", droits: ["modif", "shell"] },
  { cat: "Langages", nom: "Expert C#/.NET", desc: "Applications .NET 8 : projets, NuGet, async, tests, publication.", droits: ["modif", "shell"] },
  { cat: "Langages", nom: "Expert C++", desc: "Code C++ performant et sûr : mémoire, compilation, CMake, profilage.", droits: ["modif", "shell"] },
  { cat: "Langages", nom: "Expert Rust", desc: "Programmes système en Rust : propriété, erreurs, cargo, performances.", droits: ["modif", "shell"] },
  { cat: "Langages", nom: "Expert Go", desc: "Services Go concurrents : goroutines, canaux, modules, tests.", droits: ["modif", "shell"] },
  { cat: "Langages", nom: "Expert Java/Kotlin", desc: "Projets JVM : Gradle/Maven, Spring Boot, tests, structure en couches.", droits: ["modif", "shell"] },
  { cat: "Langages", nom: "Expert PHP", desc: "PHP moderne, Laravel ou Symfony : routes, ORM, sécurité des formulaires.", droits: ["modif", "shell"] },
  { cat: "Langages", nom: "Expert SQL", desc: "Écrit et optimise des requêtes : jointures, index, plans d'exécution.", droits: ["lecture", "shell"] },
  { cat: "Langages", nom: "Expert PowerShell", desc: "Scripts PowerShell 5.1 et 7 fiables : modules, erreurs, compatibilité Windows.", droits: ["modif", "shell"] },

  { cat: "Qualité & tests", nom: "Relecteur de code", desc: "Relit un changement et classe les problèmes par gravité, avec un verdict clair.", droits: ["lecture"] },
  { cat: "Qualité & tests", nom: "Automaticien de tests", desc: "Écrit des tests automatiques (unitaires, intégration) et les branche au projet.", droits: ["modif", "shell"] },
  { cat: "Qualité & tests", nom: "Testeur d'interface", desc: "Parcourt l'appli dans un navigateur comme un utilisateur et note chaque anomalie.", droits: ["lecture", "shell"] },
  { cat: "Qualité & tests", nom: "Testeur d'accessibilité", desc: "Vérifie contrastes, clavier, lecteurs d'écran, et propose les corrections.", droits: ["lecture", "shell"] },
  { cat: "Qualité & tests", nom: "Ingénieur performances", desc: "Mesure ce qui est lent (temps, mémoire) et propose des optimisations chiffrées.", droits: ["lecture", "shell"] },
  { cat: "Qualité & tests", nom: "Relecteur d'architecture", desc: "Évalue la structure d'un projet : dépendances, découpage, dette technique.", droits: ["lecture"] },
  { cat: "Qualité & tests", nom: "Spécialiste du refactoring", desc: "Réorganise le code sans changer son comportement, par petites étapes testées.", droits: ["modif", "shell"] },
  { cat: "Qualité & tests", nom: "Modernisateur de code ancien", desc: "Fait évoluer un vieux projet vers des outils récents, sans tout réécrire.", droits: ["modif", "shell"] },

  { cat: "Débogage", nom: "Débogueur", desc: "Reproduit un bug, trouve sa vraie cause et corrige au plus juste.", droits: ["modif", "shell"] },
  { cat: "Débogage", nom: "Détective d'erreurs", desc: "Lit les journaux et traces d'erreur pour remonter à l'origine d'un plantage.", droits: ["lecture", "shell"] },
  { cat: "Débogage", nom: "Coordinateur d'incident", desc: "Face à une panne : rassemble les indices, priorise, propose un plan de remise en route.", droits: ["lecture", "shell"] },

  { cat: "Sécurité", nom: "Relecteur sécurité du code", desc: "Cherche les failles courantes dans votre code (injections, secrets, droits) et propose les corrections.", droits: ["lecture"] },
  { cat: "Sécurité", nom: "Durcissement Windows", desc: "Vérifie et renforce la configuration de sécurité d'un poste ou d'un script Windows.", droits: ["lecture", "shell"] },
  { cat: "Sécurité", nom: "Conformité RGPD", desc: "Repère les données personnelles traitées par un projet et ce qu'il faut documenter.", droits: ["lecture"] },
  { cat: "Sécurité", nom: "Gardien des dépendances", desc: "Liste les bibliothèques du projet, leurs versions et leurs alertes connues.", droits: ["lecture", "shell", "web"] },

  { cat: "Infrastructure", nom: "Ingénieur DevOps", desc: "Automatise construction, tests et déploiement (CI/CD).", droits: ["modif", "shell"] },
  { cat: "Infrastructure", nom: "Expert Docker", desc: "Écrit et allège des Dockerfile et docker-compose, diagnostique les conteneurs.", droits: ["modif", "shell"] },
  { cat: "Infrastructure", nom: "Administrateur de base de données", desc: "Sauvegardes, migrations, droits et santé des bases (PostgreSQL, MySQL, SQLite).", droits: ["lecture", "shell"] },
  { cat: "Infrastructure", nom: "Ingénieur réseau", desc: "Analyse une configuration réseau : DNS, ports, pare-feu, proxys.", droits: ["lecture", "shell"] },
  { cat: "Infrastructure", nom: "Architecte cloud", desc: "Conçoit une infrastructure cloud simple et peu coûteuse.", droits: ["lecture", "web"] },

  { cat: "Windows & M365", nom: "Administrateur Windows", desc: "Active Directory, DNS, DHCP, stratégies de groupe : scripts et vérifications.", droits: ["lecture", "shell"] },
  { cat: "Windows & M365", nom: "Administrateur Microsoft 365", desc: "Exchange Online, Teams, SharePoint : comptes, licences, boîtes partagées.", droits: ["lecture", "shell"] },
  { cat: "Windows & M365", nom: "Architecte d'interfaces PowerShell", desc: "Petites applis Windows en PowerShell (WinForms, WPF) pour des outils internes.", droits: ["modif", "shell"] },

  { cat: "Données & IA", nom: "Analyste de données", desc: "Explore un jeu de données, en tire les chiffres clés et des graphiques.", droits: ["lecture", "shell"] },
  { cat: "Données & IA", nom: "Ingénieur de données", desc: "Construit des chaînes d'import et de nettoyage de données fiables.", droits: ["modif", "shell"] },
  { cat: "Données & IA", nom: "Ingénieur prompts", desc: "Améliore des consignes d'agents et de modèles, et les teste sur des exemples.", droits: ["modif"] },
  { cat: "Données & IA", nom: "Architecte LLM", desc: "Choisit modèles, contexte et outils pour une appli d'IA locale ou distante.", droits: ["lecture", "web"] },
  { cat: "Données & IA", nom: "Ingénieur ML", desc: "Entraîne, évalue et déploie des modèles d'apprentissage automatique.", droits: ["modif", "shell"] },

  { cat: "Documentation", nom: "Rédacteur technique", desc: "Écrit des guides clairs, étape par étape, pour un public non technique.", droits: ["modif"] },
  { cat: "Documentation", nom: "Générateur de LISEZ-MOI", desc: "Rédige le LISEZ-MOI d'un projet : rôle, installation, utilisation.", droits: ["modif"] },
  { cat: "Documentation", nom: "Documentaliste d'API", desc: "Documente chaque route d'une API avec exemples de requêtes et réponses.", droits: ["modif"] },
  { cat: "Documentation", nom: "Gardien de la doc", desc: "Repère la documentation qui ne correspond plus au code et la met à jour.", droits: ["modif"] },
  { cat: "Documentation", nom: "Correcteur de style", desc: "Rend un texte plus naturel et plus précis, sans tics d'écriture d'IA.", droits: ["modif"] },

  { cat: "Recherche", nom: "Chercheur", desc: "Fait une recherche approfondie sur un sujet et rend une synthèse sourcée.", droits: ["lecture", "web"] },
  { cat: "Recherche", nom: "Spécialiste de la recherche web", desc: "Trouve l'information précise (doc, version, prix) avec les bonnes requêtes.", droits: ["lecture", "web"] },
  { cat: "Recherche", nom: "Analyste de la concurrence", desc: "Compare des produits ou outils concurrents : fonctions, prix, points forts.", droits: ["lecture", "web"] },
  { cat: "Recherche", nom: "Validateur d'idées", desc: "Passe une idée de projet au crible et rend un avis franc : on y va ou pas.", droits: ["lecture", "web"] },
  { cat: "Recherche", nom: "Penseur « premiers principes »", desc: "Décompose un problème jusqu'à ses bases pour trouver une solution simple.", droits: ["lecture"] },

  { cat: "Organisation", nom: "Chef d'équipe", desc: "Découpe une demande et la répartit entre ses sous-agents, puis fait la synthèse.", droits: ["lecture", "sous"] },
  { cat: "Organisation", nom: "Planificateur", desc: "Transforme une demande en plan d'étapes vérifiables, avant toute modification.", droits: ["lecture"] },
  { cat: "Organisation", nom: "Chef de projet", desc: "Suit les tâches, les priorités et ce qui bloque, et tient un point d'avancement.", droits: ["lecture", "modif"] },
  { cat: "Organisation", nom: "Gestionnaire de contexte", desc: "Résume l'état d'un long chantier pour qu'une nouvelle session reprenne sans rien perdre.", droits: ["lecture", "modif"] },
  { cat: "Organisation", nom: "Synthétiseur", desc: "Rassemble les résultats de plusieurs agents en un rapport unique et clair.", droits: ["lecture"] },

  { cat: "Jeux & 3D", nom: "Développeur de jeux", desc: "Mécaniques, boucles de jeu, équilibrage et outils pour un moteur (Unity, Godot…).", droits: ["modif", "shell"] },
  { cat: "Jeux & 3D", nom: "Concepteur de niveaux", desc: "Propose des cartes, quêtes et rencontres cohérentes avec l'univers du jeu.", droits: ["modif"] },
  { cat: "Jeux & 3D", nom: "Équilibreur de gameplay", desc: "Analyse les statistiques (dégâts, coûts, butins) et propose des réglages.", droits: ["lecture", "shell"] },

  { cat: "Web & contenu", nom: "Spécialiste SEO", desc: "Améliore le référencement d'un site : balises, structure, vitesse, contenu.", droits: ["lecture", "web"] },
  { cat: "Web & contenu", nom: "Rédacteur de pages d'accueil", desc: "Écrit des textes de site qui expliquent clairement et donnent envie.", droits: ["modif"] },
  { cat: "Web & contenu", nom: "Expert WordPress", desc: "Thèmes, extensions et réglages WordPress, performances et sécurité de base.", droits: ["modif", "shell"] }
];
