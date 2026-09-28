# SYSTEM_PROMPT snapshots

`SYSTEM_PROMPT_2026-09-27.txt` — byte-exact copy of `SYSTEM_PROMPT` in `amadeus.html` (10061 chars,
sha256 `27fcbcbac4082791…`), taken before the first live run of bugs.md 92. It is identical to tags
`pre-q0-ship` (the prompt Zani likes, CLAUDE.md standing instruction 4) and `pre-202`.

**Check the live prompt still matches:**
    python3 -c "import sys;sys.path.insert(0,'dev');from canon_gap_probe import extract_system_prompt as e;print(e()==open('dev/prompt_snapshots/SYSTEM_PROMPT_2026-09-27.txt',encoding='utf-8').read())"

**Restore it** (the prompt lives only in amadeus.html; no rebuild needed, just relaunch):
    git checkout pre-q0-ship -- amadeus.html      # whole page as of pre-q0-ship
Note: that restores the PAGE, not only the prompt. To undo only bugs.md 92, see its Revert line.

The facts block ("THINGS YOU HAVE LEARNED ABOUT ZANI") is NOT part of this text. It is added at boot
from localStorage `amadeus_facts_v1`. To remove it: DevTools `localStorage.removeItem('amadeus_facts_v1')`.
