# Guide de compatibilité avec logrotate

## Exécution en tant que root

**Le service auditd-monitor s'exécute en tant que root**, tout comme :

- `auditd` lui-même (le service à surveiller)
- `logrotate` (rotation des logs système)
- `rsyslog` / `syslog-ng` (démons de logs)

### Pourquoi root est nécessaire ?

1. **Redémarrage de services** : Seul root peut exécuter `systemctl restart auditd`
2. **Lecture des logs système** : Les fichiers `/var/log/syslog` et `/var/log/messages` sont protégés (permissions 640, propriétaire root:adm)
3. **Écriture dans /var/log** : Le monitoring écrit ses propres logs dans `/var/log/auditd-monitor.log`
4. **Cohérence système** : Tous les outils de gestion de logs système (logrotate, auditd, rsyslog) s'exécutent en root

### Sécurité

Le fichier de service systemd inclut des mesures de sécurité appropriées :

```ini
[Service]
User=root
Group=root
NoNewPrivileges=false     # Nécessaire pour redémarrer des services
PrivateTmp=true           # Isolation du /tmp
ProtectSystem=strict      # Protection du système de fichiers
ProtectHome=true          # Protection des répertoires utilisateurs
ReadWritePaths=/var/log   # Accès en écriture uniquement à /var/log
```

## Compatibilité avec logrotate

Le script de monitoring d'auditd est conçu pour être totalement compatible avec `logrotate` et ne pas interférer avec sa rotation des logs.

### Mécanisme de lecture non-bloquant

Le monitoring utilise la commande `tail` pour lire les logs, ce qui garantit :

1. **Pas de verrouillage de fichier** : `tail` ouvre le fichier en lecture seule sans verrouillage exclusif
2. **Rotation libre** : `logrotate` peut renommer, déplacer ou compresser les fichiers sans problème
3. **Efficacité** : Seules les dernières lignes sont lues, pas tout le fichier

### Configuration de logrotate

Exemple de configuration pour `/var/log/auditd-monitor.log` :

```bash
/var/log/auditd-monitor.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root adm
    sharedscripts
    postrotate
        systemctl reload auditd-monitor 2>/dev/null || true
    endscript
}
```

### Détection des logs auditd

Le script utilise une détection précise basée sur les signatures natives d'auditd :

**Signatures reconnues :**

- `type=EXECVE` - Exécution de commandes
- `type=SYSCALL` - Appels système
- `type=PATH` - Chemins de fichiers
- `type=CWD` - Répertoire de travail
- `type=USER_AUTH` - Authentification utilisateur
- `type=USER_CMD` - Commandes utilisateur
- `type=CRED_ACQ` - Acquisition de credentials
- `type=LOGIN` - Connexions
- `type=SERVICE_START/STOP` - Démarrage/arrêt de services
- Et bien d'autres...

Cette approche garantit une détection fiable des entrées auditd même dans des fichiers syslog mixtes.

### Gestion de la rotation en cours

Si une rotation se produit pendant que le monitoring lit les logs :

1. Le script lit les dernières 1000 lignes du fichier actuel
2. Si le fichier est roté pendant la lecture, aucune erreur n'est générée
3. À la prochaine vérification (intervalle configuré), le nouveau fichier est lu
4. Aucune perte de détection d'inactivité

### Test de compatibilité

Pour tester la compatibilité avec logrotate :

```bash
# Forcer une rotation manuelle
sudo logrotate -f /etc/logrotate.d/rsyslog

# Vérifier que le monitoring continue de fonctionner
sudo systemctl status auditd-monitor
sudo journalctl -u auditd-monitor -n 20
```

Le monitoring devrait continuer à fonctionner normalement sans erreurs.
