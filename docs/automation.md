# CI, provenance et publication

Ce document décrit le parcours initial, conservé jusqu'à activation du catalogue.
Le nouveau workflow hébergé et son ordre de publication sont décrits dans
[la migration CI](ci-migration.md).

`check.yml` exécute les tests et la syntaxe à chaque push/PR. `release.yml` est
manuel, sur runner `[self-hosted, linux, x64, pantavisor]` avec Python ≥3.11, Git,
Podman rootless, unsquashfs et qemu-aarch64. Prévoir 16 Gio RAM et 150 Gio libres.
Le checkout est neuf par exécution ; aucun cache Yocto externe n'est réutilisé.

Le wrapper `build/provenance.py` capture les sources avant KAS puis les empreintes
des sorties après succès. Le packaging refuse les sources et sorties modifiées.
`build-provenance.json` contient la durée de build et les SHA-256. Les anciennes
sorties doivent être reconstruites.

Depuis un tag `v<VERSION>`, le workflow avec `publish=true` publie :

- image OCI : `ghcr.io/<owner>/pantavisor-k0s:<VERSION>` ;
- composant ORAS : `ghcr.io/<owner>/pantavisor-k0s/component:<VERSION>`.

Il exige les tests, le smoke ARM64, un build OCI et une provenance propre. Le
digest ORAS affiché est l'entrée de System. Le smoke ne qualifie pas Kubernetes :
System exécute API/nœud Ready, DNS, HTTP inter-pods, PVC et reboot/persistance.

Le service publie `api-configured` dès que le kubeconfig est disponible, puis
`ready` après vérification API/nœud. Ce signal initial n'est pas un monitoring
continu du cluster. Un échec reste inspectable dans `/access`.

Configurer runner et GHCR puis conserver les rapports du premier build froid.
Les workflows seuls ne prouvent ni exécution distante ni publication effective.
Nettoyer les anciens checkouts du runner après archivage.
