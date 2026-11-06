# Fizzo Facts — daily episode runbook

Channel: Fizzo Facts (YouTube Shorts, English). Two original robot characters:
- **Fizzo** (`fizzo`): hyper, fast-talking host who tells the facts. Voice `am_puck`.
- **Gizmo Jr.** (`gizmo`): posh know-it-all sidekick with glasses and a propeller cap; brags, gets proven wrong, glitches. Voice `bm_george`.

Each episode: ~20–30 s, 9–12 beats. Gizmo brags → Fizzo drops 3 true "sounds fake" facts → Gizmo reacts (shock) after each → Gizmo glitches ("ERROR") → Fizzo ends with "Follow for more…" plus a joke about Gizmo.

## Steps
1. `bash tools/setup.sh` (downloads the voice model to ~/kokoro if missing; must print `setup ok`).
2. Pick 3 surprising facts **not used before** (check `facts_checked` in every file under `episodes/`). Verify every fact with a web search; only use facts confirmed by reliable sources. Avoid anything about real people's private lives, politics, religion, violence, health advice, or anything scary for kids. Avoid numbers you are not sure of.
3. Write `episodes/YYYY-MM-DD.json` (date = the publish day, Europe/Budapest), copying the structure of an existing episode:
   - `caption`: what is shown on screen. Words in CAPS get a yellow highlight; use 1–3 per line.
   - `phonemes`: the same sentence in American English IPA, Kokoro/misaki style (stress marks ˈ ˌ, `ɹ` for r, `ɾ` for flap t, `ʤ`/`ʧ`, `ɚ`). The script stops if a character is not in `tools/vocab.json`.
   - `gizmo_mood` / `fizzo_mood`: `idle`, `talk`, `smug`, `shock`, `glitch`, `happy`, `laugh`. Use `"flash": true` on Gizmo's shocked reactions and the glitch.
   - Keep captions under ~60 characters.
4. `python3 tools/make_episode.py episodes/YYYY-MM-DD.json` → writes `videos/YYYY-MM-DD.mp4` and a preview sheet. Look at the preview sheet; fix overlaps or wrong text before going on.
5. Commit both files and push to `main`.
6. Public video URL: `https://raw.githubusercontent.com/botikagaming201308-png/fizzo-facts/main/videos/YYYY-MM-DD.mp4`
7. Schedule it with Metricool `createScheduledPost`: blogId `7916703`, 17:00 Europe/Budapest on the publish day, provider `youtube`, `youtubeData`: type `short`, privacy `public`, `madeForKids` false, category `ENTERTAINMENT`, the episode's title and tags; `text` = the episode's description; media = the raw URL above; autoPublish true. Before scheduling, call `getScheduledPosts` for that day and skip if a post is already there.
