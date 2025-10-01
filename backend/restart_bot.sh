#!/bin/bash
# Quick script to restart the TWAP bot

echo "🔄 Restarting TWAP Bot..."
pkill -f "python3 main.py" 2>/dev/null || true
sleep 1

cd /home/windd/foundry-projects/korede/koredeRepo/packages/twap-bot/backend
source venv/bin/activate
python3 main.py

