# Fizzo Facts — daily episode runbook

Channel: Fizzo Facts (YouTube Shorts, English). Two original robot characters:
- **Fizzo** (`fizzo`): hyper, fast-talking host who tells the facts. Voice `am_puck`.
- **Gizmo Jr.** (`gizmo`): posh know-it-all sidekick with glasses and a propeller cap; brags, gets proven wrong, glitches. Voice `bm_george`.

Each episode: ~20–30 s, 9–12 beats. Gizmo brags → Fizzo drops 3 true "sounds fake" facts → Gizmo reacts (shock) after each → Gizmo glitches ("ERROR") → Fizzo ends with a comment question ("Which one got YOU? Comment!") then "Follow for more…" plus a joke about Gizmo.

What works (from channel stats): the octopus episode (2026-11-08) got ~7x the views of earlier ones. Its title led with the single most surprising ANIMAL fact plus an emoji, and it had a silly kid-friendly gross-out beat (wombat poop cubes). So:
- Put the strongest, most visual animal fact FIRST, and build the title around it ("<Animal> <does X>?! <emoji> #shorts").
- Include one silly/funny beat kids will want to repeat to friends (keep it harmless).
- The final 2 beats must ask viewers to comment (the earlier episodes got 0 comments).
- Thumbnails: YouTube was showing the LAST frame (outro / ERROR face) as the cover, which sells nothing. The video maker now ends with a 1.5 s silent end card showing the hook (the title without hashtags/emoji, CAPS words highlighted). Write the title so it reads well on that card, or set an optional `"cover"` field in the episode JSON to override the card text (CAPS = highlight, no emoji). Check the end card in the preview sheet (last panel).

## Steps
1. `bash tools/setup.sh` (downloads the voice model to ~/kokoro if missing; must print `setup ok`).
2. Pick 3 surprising facts **not used before** (check `facts_checked` in every file under `episodes/`). Verify every fact with a web search; only use facts confirmed by reliable sources. Avoid anything about real people's private lives, politics, religion, violence, health advice, or anything scary for kids. Avoid numbers you are not sure of.
3. Write `episodes/YYYY-MM-DD.json` (date = the publish day, Europe/Budapest), copying the structure of an existing episode:
   - `caption`: what is shown on screen. Words in CAPS get a yellow highlight; use 1–3 per line.
   - `phonemes`: the same sentence in American English IPA, Kokoro/misaki style (stress marks ˈ ˌ, `ɹ` for r, `ɾ` for flap t, `ʤ`/`ʧ`, `ɚ`). The script stops if a character is not in `tools/vocab.json`.
   - `gizmo_mood` / `fizzo_mood`: `idle`, `talk`, `smug`, `shock`, `glitch`, `happy`, `laugh`. Use `"flash": true` on Gizmo's shocked reactions and the glitch.
   - Keep captions under ~60 characters.
4. `python3 tools/make_episode.py episodes/YYYY-MM-DD.json` → writes `videos/YYYY-MM-DD.mp4` and a preview sheet, and prints `cover_ms` (the middle of the end card). Look at the preview sheet; fix overlaps or wrong text before going on.
5. Commit both files and push to `main`.
6. Public video URL: `https://raw.githubusercontent.com/botikagaming201308-png/fizzo-facts/main/videos/YYYY-MM-DD.mp4`
7. Schedule it with Metricool `createScheduledPost`: blogId `7916703`, 17:00 Europe/Budapest on the publish day, provider `youtube`, `youtubeData`: type `short`, privacy `public`, `madeForKids` false, category `ENTERTAINMENT`, the episode's title and tags; `text` = the episode's description; media = the raw URL above; `videoCoverMilliseconds` = the printed `cover_ms`; autoPublish true. (If Metricool rejects the cover field, schedule again without it; the end card still makes the last frame a good cover.) Before scheduling, call `getScheduledPosts` for that day and skip if a post is already there.
