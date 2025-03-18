#!/bin/bash
set -e

echo "Cleaning up duplicate processes..."
echo "=================================="

# Check for multiple streamlit instances
streamlit_count=$(pgrep -f "streamlit run dashboard.py" | wc -l)
echo "Found $streamlit_count streamlit processes"

if [ "$streamlit_count" -gt 1 ]; then
  echo "Terminating duplicate streamlit processes..."
  # Keep only the newest process (highest PID)
  newest_pid=$(pgrep -f "streamlit run dashboard.py" | sort -n | tail -1)
  pgrep -f "streamlit run dashboard.py" | grep -v $newest_pid | xargs -r kill
  echo "Kept streamlit process with PID $newest_pid"
fi

# Check for multiple uvicorn instances
uvicorn_count=$(pgrep -f "uvicorn main:app" | wc -l)
echo "Found $uvicorn_count uvicorn processes"

if [ "$uvicorn_count" -gt 1 ]; then
  echo "Terminating duplicate uvicorn processes..."
  # Keep only the newest process (highest PID)
  newest_pid=$(pgrep -f "uvicorn main:app" | sort -n | tail -1)
  pgrep -f "uvicorn main:app" | grep -v $newest_pid | xargs -r kill
  echo "Kept uvicorn process with PID $newest_pid"
fi

echo "Process cleanup complete!"
echo ""
echo "Current running processes:"
ps aux | grep -E "streamlit|uvicorn" | grep -v grep
