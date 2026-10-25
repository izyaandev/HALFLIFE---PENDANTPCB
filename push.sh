#!/bin/bash
# Run from inside this folder. Needs git logged in to GitHub (gh auth login, or a personal access token).
# It copies these files into your repo without touching JOURNAL.md or BOM.md.
set -e
git clone https://github.com/izyaandev/HALFLIFE---PENDANTPCB.git /tmp/pendantpcb
rsync -a --exclude push.sh --exclude .git ./ /tmp/pendantpcb/
cd /tmp/pendantpcb
git add .
git commit -m "Add README, KiCad design files, BOM, Gerbers, firmware, 3D enclosure, backend and simulator"
git push origin main
