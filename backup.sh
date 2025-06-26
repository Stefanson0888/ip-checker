#!/bin/bash

# Backup script for checkip.app before VPN integration
echo "🔒 Creating backup before VPN integration..."

# Create backup directory with timestamp
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup all important files
echo "📁 Backing up main files..."
cp main.py "$BACKUP_DIR/"
cp requirements.txt "$BACKUP_DIR/"
cp render.yaml "$BACKUP_DIR/"
cp run.py "$BACKUP_DIR/"

# Backup directories
echo "📂 Backing up directories..."
cp -r templates/ "$BACKUP_DIR/"
cp -r utils/ "$BACKUP_DIR/"
cp -r static/ "$BACKUP_DIR/"
cp -r locales/ "$BACKUP_DIR/"

# Create backup info file
echo "📝 Creating backup info..."
cat > "$BACKUP_DIR/backup_info.txt" << EOF
Backup created: $(date)
Purpose: Before NordVPN affiliate integration
Original structure preserved

Files backed up:
- main.py
- templates/ (all HTML files)
- utils/ (i18n.py, ip.py, etc)
- static/ (sitemap.xml, robots.txt, etc)
- locales/ (translation files)
- requirements.txt
- render.yaml
- run.py

Next step: Add NordVPN affiliate configuration
EOF

echo "✅ Backup completed in: $BACKUP_DIR"
echo "🔍 Backup contents:"
ls -la "$BACKUP_DIR"