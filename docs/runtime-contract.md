# Contrat `pantavisor-k0s-v1`

Le descripteur est [`runtime/contract.json`](../runtime/contract.json) ; le template
[`runtime/lxc.conf.in`](../runtime/lxc.conf.in) définit le conteneur sans adresses
physiques de disque ni valeurs de RAM propres à une carte.

## Prérequis fournis par System

- Linux ARM64 et les fonctionnalités Kubernetes/containerd nécessaires.
- Réseau hôte, cgroups v2 délégués, limite mémoire numérique et propagation des
  montages compatible avec les pods.
- Modules réseau/netfilter, OverlayFS et configuration du noyau accessibles.
- Volumes persistants sur `/var/lib/k0s`, `/data`, `/var/log` et `/access`.
  Le contrat initial exige ext4 ; d'autres formats restent à qualifier.
- Heure fiable et marqueur `/clock-status/time-ready` avant la création de PKI.

Les cgroups, capacités et accès aux périphériques en font un conteneur système
privilégié. Le rôle Pantavisor `nobody` ne signifie pas que k0s est un processus
Linux non privilégié. L'image OCI doit être exécutée avec ce contrat.

## Configuration du service

Le fichier `/etc/pantavisor/k0s.env` est injecté au déploiement. Voir
[`config/k0s.env.example`](../config/k0s.env.example).

- `K0S_NODE_NAME`, `K0S_CLUSTER_NAME` : identités configurables.
- `K0S_NODE_ADDRESS` : adresse explicite, ou adresse de la route IPv4 par défaut.
- `K0S_DNS_SERVERS` : résolveurs explicites ; aucun cas particulier QEMU.
- `K0S_POD_CIDR`, `K0S_SERVICE_CIDR`, `K0S_MAX_PODS` : réseau et capacité.
- `K0S_HOST_RESERVE_MIB`, `K0S_KUBE_RESERVE_MIB`, `K0S_EVICTION_MIB` : réserves
  traduites en configuration kubelet à partir du plafond cgroup fourni.
- `K0S_DISABLED_COMPONENTS` : liste séparée par des virgules.

System choisit les budgets et les montages. Le service k0s possède la génération
de `k0s.yaml`, du worker profile et le lancement de containerd/kubelet via k0s.

## Observabilité et arrêt

Le service publie son état et ses logs dans `/access`. Son kubeconfig est copié
atomiquement dans `/access/admin.conf` avec permissions 0600. L'hôte peut exposer
ce répertoire en lecture seule au Core de gestion.

Un échec du service reste inspectable. L'objectif Pantavisor `STARTED` est distinct
du statut Kubernetes `Ready`, qui doit être vérifié par le consommateur.
SIGTERM arrête le processus enfant et synchronise les données.
