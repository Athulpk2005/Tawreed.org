#!/bin/zsh
cd -- "${0:A:h}"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
for twd_python in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$twd_python" >/dev/null 2>&1 && "$twd_python" -c 'import sys;sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
    "$twd_python" backend/start_portal.py
    twd_status=$?
    if [ "$twd_status" -ne 0 ]; then read '?Press Return to close this window.'; fi
    exit "$twd_status"
  fi
done
print 'Install Python 3.10 or newer from https://www.python.org/downloads/, then run this launcher again.'
read '?Press Return to close this window.'
