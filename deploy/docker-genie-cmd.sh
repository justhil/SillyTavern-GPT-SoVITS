#!/bin/bash
set -e
cd /www/genie
export GENIE_DATA_DIR="${GENIE_DATA_DIR:-/www/genie/GenieData}"
if [ -x /www/genie/venv/bin/python ] && [ -f /www/genie/run_server.py ]; then
  exec /www/genie/venv/bin/python /www/genie/run_server.py
fi
pip install -q genie-tts
exec python -c "import os; os.environ.setdefault('GENIE_DATA_DIR','/www/genie/GenieData'); import genie_tts as g; g.start_server(host='0.0.0.0', port=8000, workers=1)"