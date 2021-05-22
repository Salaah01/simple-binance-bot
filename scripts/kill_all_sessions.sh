#!/usr/bin/bash
# Kills all sessions where the controller has been called.
while IFS= read -r pid; do
  kill $pid
done <<<$(ps -aux | grep "python controller" | grep -v "grep" | awk '{print $2}' | cut -d ' ' -f 1)
