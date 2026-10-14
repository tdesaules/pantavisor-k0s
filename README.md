# Pantavisor k0s

Intégration de k0s comme conteneur système Pantavisor. Version de l'intégration :
**0.1.0**. Version du logiciel amont embarqué : **v1.36.4+k0s.1**.

Le build ARM64/musl est autonome : aucun checkout Core ou System n'est nécessaire.
Le dépôt produit l'image, les paramètres du service et son contrat runtime.
System fournit le noyau, les cgroups, le réseau et les volumes physiques.

## Structure

- `services/k0s-init` : prérequis, configuration Kubernetes, démarrage et arrêt.
- `config/k0s.env.example` : entrées du service, noms, DNS, CIDR et ressources.
- `runtime/` : contrat et template LXC paramétrable exportés avec le composant.
- `build/meta-k0s/` : recette du binaire vérifié et de l'image système.
- `kas/base.yml` : sources amont épinglées, cible userspace ARM64 uniquement.
- `build/package.py` : export public et inventaire d'empreintes.
- `build/Containerfile` : production de l'image OCI depuis le rootfs Yocto.
- `build/smoke.py` et `tests/` : vérifications locales.

## Construction locale

Prérequis : Linux, Git, Python ≥3.11, [Task](https://taskfile.dev/) v3 et Podman rootless.
`task --list` affiche les tâches disponibles. Sans argument, `task` lance `build`.

```sh
task check
task build
task package
task oci
```

L'export public est dans `dist/base/` ; l'image locale est
`localhost/pantavisor-k0s:base`, avec le label de version `0.1.0`.
Les répertoires d'export doivent être nouveaux ; `build/package.py --output`
permet de conserver plusieurs résultats locaux.

Les variables facultatives `DOWNLOAD_CACHE` et `SSTATE_CACHE` permettent de
réutiliser des caches publics. Sans cache, les dépendances sont téléchargées.

Avec SquashFS et QEMU utilisateur installés :

```sh
python3 build/smoke.py dist/base
```

Le composant exporte le rootfs en SquashFS et tar, `component.json`, le SBOM,
le manifeste des paquets et le contrat runtime. Il ne contient ni noyau, ni
identifiants de disque, ni PKI, ni kubeconfig précréé.

## Intégration

Le nom du nœud, le nom du cluster, l'adresse et les DNS sont configurables.
Le composant ne recherche pas de NVMe ni de partition particulière.
Il reste volontairement limité au mode single-node et au contrat initial ext4
avec cgroups v2. Voir [le contrat](docs/runtime-contract.md).

kubectl, k0sctl et k9s destinés à l'administrateur sont produits par le dépôt Core,
pas par ce composant. L'intégration GitOps et les workloads d'infrastructure sont
hors du périmètre de cette image.

## État de l'extraction

Projet neuf, sans reprise d'historique Git. Build local, packaging, image OCI et
exécution ARM64 de `k0s version` vérifiés. System sait composer et rendre l'état
privé avec cet artefact. Le cluster complet n'a pas été requalifié sur matériel
après ce découpage ; la CI sera traitée ultérieurement.
