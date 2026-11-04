# Migration vers les Docker Actions

Activer après publication d'une release du catalogue contenant toutes les actions.
Depuis le checkout `github-actions`, avec Python, `gh` et ORAS :

```sh
python3 scripts/pantavisor_consumers.py --project k0s \
  --catalogue-tag "$CATALOGUE_TAG" --directory ../pantavisor-k0s
```

Le tag doit être réellement publié. L'outil vérifie les images par digest,
génère le workflow `main` à six jobs, conserve les anciens workflows dans
`.github/legacy-workflows/` et enregistre le tag dans `.github/pantavisor-ci.json`.
Relire, committer puis pousser les changements du consommateur.

## Parcours

Les branches de travail sont fusionnées vers `main`. Les push déclenchent les
contrôles sélectionnés ; les modifications documentaires ne construisent pas
Yocto. Il n'y a pas de trigger `pull_request`.

La préparation manuelle sur `main` calcule VERSION et changelog à partir des
Conventional Commits. Elle crée un commit candidat, transféré par Git bundle aux
jobs de build/test. KAS utilise `kas/ci.yml` sur `ubuntu-24.04`, avec deux tâches.
L'image ARM64 est assemblée depuis le rootfs, sans exécution ni moteur imbriqué.

Le job `test` sur `ubuntu-24.04-arm` vérifie les archives, exécute `k0s version`,
génère les SBOM et applique Grype au seuil `high`. Après réussite, l'App pousse
atomiquement le commit candidat et son tag annoté `v<VERSION>`. Le workflow du
tag récupère les sorties qualifiées, les publie par digest, signe/vérifie les
objets OCI/ORAS et crée la GitHub Release. Aucun rebuild implicite de release.

Le cluster complet est qualifié par le profil k0s de System, qui consomme la
référence immuable publiée. Le smoke test producteur ne signifie pas nœud Ready.

## Prérequis et suivi

Configurer la variable `RELEASE_APP_ID`, le secret `RELEASE_APP_PRIVATE_KEY` et
l'installation de l'App avec les droits nécessaires. Son accès est testé avant
le build de préparation. Le token GitHub ordinaire n'est pas utilisé pour pousser
le tag de préparation.

Configurer un `RENOVATE_TOKEN` dédié et éviter une seconde instance de Renovate
hébergée. Les managers actions/Containerfiles sont configurés ; les recettes
k0s et leurs checksums restent à mettre à jour conjointement.

Surveiller les artefacts `build-diagnostics-k0s`, `test-reports-k0s`, les reçus
liés au commit, les signatures et la GitHub Release. Les artefacts qualifiés
restent disponibles 30 jours. Une reprise après expiration échoue explicitement.
Les alertes de scan ne sont pas masquées ; la maintenance rescane sans rebuild.
