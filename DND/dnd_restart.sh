#!/bin/bash
# Restart parsednd.py:
screen -S dnd -X quit
screen -S dnd -m -d python3.5 /opt/DND/parsednd.py
