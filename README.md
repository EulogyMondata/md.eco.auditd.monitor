# Audit Log Monitor

Un système de monitoring pour surveiller les logs d'audit Linux et redémarrer automatiquement le service auditd s'il cesse d'écrire dans les fichiers de log.

## Fonctionnalités

- Surveille les fichiers de logs système pour détecter l'inactivité d'auditd
- Redémarre automatiquement le service audit si nécessaire
- Configuration flexible pour différentes distributions Linux
- Compatible avec systemd
- Gestion des dépendances avec `uv`

## Prérequis

- Python 3.13+
- Accès root/sudo (requis pour redémarrer les services système)
- systemd (pour l'installation en tant que service)

**Note importante sur les permissions :**
Le service doit s'exécuter en tant que root pour :

- Pouvoir redémarrer le service auditd
- Lire les fichiers de logs système (/var/log/syslog, /var/log/messages, etc.)
- Écrire dans /var/log pour ses propres logs

Ceci est cohérent avec l'exécution standard de logrotate et auditd qui s'exécutent également en tant que root.

## Installation rapide

```bash
# Télécharger et installer en une commande
curl -sSL https://raw.githubusercontent.com/EulogyMondata/md.eco.auditd.monitor/main/quick-install.sh | sudo bash
```

Ce script télécharge automatiquement le projet depuis GitHub et lance l'installation.

## Installation manuelle

1. Cloner le repository :

```bash
git clone https://github.com/EulogyMondata/md.eco.auditd.monitor.git
cd md.eco.auditd.monitor
```

1. Vérifier que tous les fichiers nécessaires sont présents :

```bash
./check-install.sh
```

1. Lancer l'installation (installe automatiquement uv et les dépendances) :

```bash
sudo ./install.sh
```

1. (Optionnel) Personnaliser la configuration :

```bash
sudo nano /etc/auditd-monitor/config.yaml
sudo systemctl restart auditd-monitor
```

## Configuration

Le fichier de configuration `/etc/auditd-monitor/config.yaml` permet de personnaliser :

```yaml
# Fichier de log à surveiller
log_file: /var/log/syslog

# Nom du service audit à redémarrer
audit_service: auditd

# Intervalle de vérification (secondes)
check_interval: 60

# Temps d'inactivité avant redémarrage (secondes)
inactivity_threshold: 300

# Motif regex pour détecter les entrées auditd
audit_pattern: "type=.*audit"

# Fichier de log pour le monitoring
monitor_log_file: /var/log/auditd-monitor.log
```

## Utilisation

### En tant que service systemd (recommandé)

```bash
# Démarrer le service
sudo systemctl start auditd-monitor

# Activer au démarrage
sudo systemctl enable auditd-monitor

# Vérifier le statut
sudo systemctl status auditd-monitor

# Voir les logs
sudo journalctl -u auditd-monitor -f

# Voir uniquement les événements importants (WARNING et ERROR)
sudo journalctl -u auditd-monitor -p warning

# Rechercher les événements de redémarrage
sudo journalctl -u auditd-monitor | grep "RESTART"
```

Pour plus d'exemples de logs, voir [LOGGING_EXAMPLES.md](LOGGING_EXAMPLES.md).

### Manuellement

```bash
sudo uv run python -m auditd_monitor.monitor
```

## Architecture

```text
md.eco.auditd.monitor/
├── auditd_monitor/
│   ├── __init__.py
│   ├── monitor.py          # Script principal de monitoring
│   ├── config.py           # Gestion de la configuration
│   └── service_manager.py  # Gestion des services système
├── config.example.yaml     # Exemple de configuration
├── pyproject.toml          # Configuration du projet uv
├── install.sh              # Script d'installation
├── auditd-monitor.service  # Fichier service systemd
└── README.md
```

## Compatibilité

Testé sur :

- Ubuntu 20.04, 22.04, 24.04
- Debian 11, 12
- RHEL/CentOS 8, 9
- Rocky Linux 8, 9
- Fedora 38+

## Dépannage

### Le service ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u auditd-monitor -n 50

# Vérifier la configuration
sudo python3 -m auditd_monitor.config --check

# Vérifier les permissions des fichiers
ls -l /var/log/syslog /var/log/auditd-monitor.log

# Vérifier que uv est accessible
which uv
ls -l /root/.local/bin/uv
```

**Erreur "code=exited, status=203/EXEC"** : Cela signifie que systemd ne trouve pas l'exécutable `uv`.

Solution temporaire (en attendant que GitHub soit à jour) : Créer le fichier service manuellement

```bash
sudo tee /etc/systemd/system/auditd-monitor.service > /dev/null << 'EOF'
[Unit]
Description=Auditd Log Monitor Service
After=network.target auditd.service
Wants=auditd.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/auditd-monitor
Environment="PATH=/root/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/root/.local/bin/uv run --project /opt/auditd-monitor python -m auditd_monitor.monitor
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=false
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart auditd-monitor
sudo systemctl status auditd-monitor
```

Ou télécharger depuis GitHub (une fois les changements poussés) :

```bash
sudo curl -sSL https://raw.githubusercontent.com/EulogyMondata/md.eco.auditd.monitor/main/auditd-monitor.service -o /etc/systemd/system/auditd-monitor.service
sudo systemctl daemon-reload
sudo systemctl restart auditd-monitor
```

### Permissions insuffisantes

**Le service DOIT s'exécuter en tant que root.** Ceci est normal et nécessaire pour :

- Redémarrer le service auditd (`systemctl restart auditd` nécessite root)
- Lire les logs système (`/var/log/syslog` est en 640 root:adm)
- Écrire ses propres logs dans `/var/log`

Si vous voyez des erreurs de permission, vérifiez que :

1. Le service systemd est configuré avec `User=root` (déjà fait par défaut)
2. Les fichiers de configuration sont accessibles : `sudo chmod 644 /etc/auditd-monitor/config.yaml`
3. Le répertoire de logs existe : `sudo mkdir -p /var/log`

**Note** : L'exécution en root est cohérente avec les autres services système comme `auditd`, `logrotate` et `rsyslog` qui s'exécutent également en tant que root.

### Le service audit n'est pas redémarré

Vérifiez que le nom du service dans la configuration correspond à votre système :

- Debian/Ubuntu : `auditd`
- RHEL/CentOS : `auditd`
- Certains systèmes : `audit`

## Désinstallation

Pour désinstaller complètement Auditd Monitor :

```bash
# Méthode 1 : Si installé manuellement depuis le repository cloné
cd md.eco.auditd.monitor
sudo ./uninstall.sh

# Méthode 2 : Télécharger puis exécuter (recommandé)
curl -sSL https://raw.githubusercontent.com/EulogyMondata/md.eco.auditd.monitor/main/uninstall.sh -o /tmp/uninstall.sh
sudo bash /tmp/uninstall.sh
```

Le script de désinstallation :

- Arrête et désactive le service
- Supprime le service systemd
- Supprime les fichiers d'installation dans `/opt/auditd-monitor`
- Demande si vous voulez conserver les fichiers de configuration (`/etc/auditd-monitor`)
- Demande si vous voulez conserver les logs (`/var/log/auditd-monitor.log`)

## Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## Licence

MIT License
