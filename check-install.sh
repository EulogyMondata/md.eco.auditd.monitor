#!/bin/bash
# Script de test pour vérifier la structure du projet avant installation

echo "=== Vérification de la structure du projet ==="

ERRORS=0

# Liste des fichiers/dossiers requis
REQUIRED_FILES=(
    "auditd_monitor/__init__.py"
    "auditd_monitor/monitor.py"
    "auditd_monitor/config.py"
    "auditd_monitor/service_manager.py"
    "pyproject.toml"
    "config.example.yaml"
    "auditd-monitor.service"
    "install.sh"
    "README.md"
)

echo "Vérification des fichiers requis..."
for file in "${REQUIRED_FILES[@]}"; do
    if [ -e "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (MANQUANT)"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ Tous les fichiers requis sont présents"
    echo "Vous pouvez exécuter: sudo ./install.sh"
    exit 0
else
    echo "❌ $ERRORS fichier(s) manquant(s)"
    echo "Assurez-vous d'être dans le répertoire racine du projet"
    exit 1
fi
