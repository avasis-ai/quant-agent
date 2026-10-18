# T-L1 Sniff hackathon promo: result

Verdict: GO. The final video is done and was checked frame by frame and by loudness measurement. It still needs one listen by a person (see "Not verified").

## Deliverables
- `~/Downloads/sniff-hackathon-promo.mp4`: 95.0 s, 1920×1080, 30 fps, H.264 CRF 17 + AAC 256k, 41.1 MB (41,142,253 B). Loudness −14.3 LUFS integrated, true peak −1.3 dBFS, no clipped samples.
- `~/Downloads/sniff-hackathon-promo-small.mp4`: 1280×720, two-pass 735 kb/s + AAC 96k, 9.9 MB (9,918,366 B, under 10 MiB). −14.3 LUFS, peak −0.2 dBFS (the AAC 96k encode adds this; it does not clip).
- Project: `~/dev/sniff-promo-v2`. Nothing was committed or pushed and nothing was uploaded.

## Approach (from the skill)
I followed the awesome-opus5-5-videos method. The film is one HTML file (`index.html`), and all drawing happens inside `seek(t)`: no CSS transitions, timers or carried state, and springs are closed form. `plan/render.mjs` seeks every frame in headless Chromium using 6 parallel pages, then screenshots it. I rendered still frames first and fixed problems before the full render. I did not use HyperFrames; the skill's single-file approach was enough.

Pipeline (each step runs again on its own):
1. `plan/tts.py`: Deepgram Aura-2 Orion, 48 kHz. The key is read at runtime from `~/.config/celesticlabs/deepgram.env` and never printed.
2. `plan/stt.py`: Deepgram nova-3 word timings, used to sync the graph scene to the voice.
3. `plan/record.mjs`: CDP screencast of the 4 public pages. `plan/assemble.py` turns it into 30 fps CFR MP4s.
4. `plan/images.py`: 3 cinematic stills with gpt-image-2.5-flare. The key is read at runtime from `~/.codex/auth.json` and never printed.
5. `plan/audio.py`: every sound is synthesised in numpy/scipy, so all of it is license-free. Music bed: 80 BPM, Dm9 → Bbmaj7 → Fmaj7 → C6, detuned-saw pads that open up with intensity, sub bass, a pluck arpeggio, soft kick and hats in the build sections, plus a synthetic reverb. Sound design: whooshes on scene changes, two risers into boom hits (title and close), tick runs on the counters, pops for graph nodes and evidence tags, chimes. The music ducks −9 dB under the voice (120 ms attack, 450 ms release). Master is two-pass loudnorm to −14 LUFS / −1.5 dBTP.
6. `plan/render.mjs frames` and then `plan/encode.sh`.

## Scene list
| # | Time | Scene | Visuals |
|---|------|-------|---------|
| 1 | 0–8.5 | Hook | AI still of a plain of glowing coins, slow push, rising ember particles. A counter ticks to 25,000, then "Who's behind them?" in Instrument Serif italic. |
| 2 | 8.3–12.1 | Title | "Sniff" wordmark resolves (boom hit), "by Quant Agent", "from a pixel dog to an agent, 14 → 18 October". |
| 3 | 11.7–19.9 | 14 Oct · the first Sniff | Live recording of sniff.quantbase.live/waitlist (the pixel dachshund) in a 3D-tilted browser window. A journey rail appears with a running pixel-dog sprite. |
| 4 | 19.5–34.5 | 15–17 Oct · the hackathon build | AI still of a glowing network. "We gave it a memory. one graph, on FalkorDB". Counters 632,339 coins / 424,007 wallets / 6,556 funding rings. |
| 5 | 34.1–44.0 | The agent answering | Recording of sniff.quantbase.live: METHU example, steps streaming, the answer with E-tags, then E1 clicked and the map zooming. Callouts: "Every sentence carries an evidence tag", "The map lights up…". |
| 6 | 43.6–57.6 | 18 Oct · Sniff joins QuantBase | quantbase.live cinematic hero recording, then the landing's race recording. Side text: "By hand · typical 55 s" vs "Sniff · measured 1.08 s, ~1 s to hear a graduation, 76 ms median to send", with the footnote "1 s across 1,371 graduations; 76 ms across 92 sends. The by-hand timeline is illustrative." |
| 7 | 57.2–65.0 | The Sniff app | Astra's final designs as floating windows: demo answer, paper chat, life of a coin. "Ask in plain words. / Try ideas on paper first. / Every answer comes with its proof." |
| 8 | 64.6–85.6 | How the graph works | Animated SVG synced word by word to the voice: funder → creators → coins, a fan of dozens of creators, the funding ring ("72 creators · 0 graduated", the METHU example), the exchange-like hub with "trail stops here", Sniff's answer card, E-tags lighting on the edges, "History, not a prediction." |
| 9 | 85.2–95.0 | Close | AI still of a dachshund on a ridge at dawn. "Sniff any coin / before you buy.", "sniff.quantbase.live · quantbase.live", "Built by Quant Agent on FalkorDB · WeMakeDevs × FalkorDB Graph Hacks". Fade to black. |

## VO script (Deepgram Aura-2 Orion, 75.7 s of voice)
- S01 @0.8: Every day, twenty-five thousand new meme coins appear. Who's behind them?
- S02 @12.0: On October fourteenth, Sniff was just a coming-soon page, and a pixel dog with a very good nose.
- S03 @20.0: Over the hackathon, we gave it a memory. A FalkorDB graph of six hundred thirty-two thousand coins, four hundred twenty-four thousand wallets, and six thousand, five hundred fifty-six funding rings.
- S04 @34.4: Ask about any coin, and the agent walks the graph. Every sentence carries an evidence tag, and the map lights up to show you where it came from.
- S05 @44.2: Today, Sniff became the agent inside QuantBase. A person checking a new coin by hand takes about a minute. Sniff hears a graduation in about a second, and sends in seventy-six milliseconds.
- S06 @57.6: Ask in plain words. Try ideas on paper first. Every answer comes with its proof.
- S07 @65.0: Here's how the graph works. Funders pay creators. Creators launch coins. When one wallet funds dozens of creators, that's a ring. Exchanges are hubs, so the trail stops there, and Sniff tells you so. Every claim has proof. History, not a prediction.
- S08 @86.2: Sniff any coin before you buy. Built by Quant Agent, on FalkorDB.

The script makes no profit claims. On screen, the hook's 25,000 is the brief's own line; the live landing showed "24,606 new coins in 24 h" on capture day.

## Facts check
- The 632,339 / 424,007 / 6,556 figures are from the brief. The METHU "72 creators, 72 coins, 0 graduated" figure is from the live sniff app answer.
- ~1 s hear / 76 ms median send: the brief points to `specs/SNIFF-EVIDENCE.md`, but that file does not contain these numbers. I found them in `reviews/sniff-DESIGN.md:27,105` ("76 ms median, measured on 92 sends") and in HANDOVER ("1 s hear across 1,371 graduations … → 1.08 s"). The race footnote uses those.
- I left out on purpose: the live dashboard screenshots (they show "LIVE · REAL MONEY", wallet balance and Stop) and the landing's "one selected winner" trade section. Both read as trading or profit material.

## Skipped / deviations
- **The public demo answer could not be recorded.** app.quantbase.live/demo returned "Your free answer has been used. This connection already had today's free demo answer." (one per connection per day). The first recording attempt used that answer behind a sign-up modal. In its place, the film shows Astra's `1440-demo-answer.png` design, plus the live demo's empty state in the recordings. If you want the real demo flow, record it from a fresh connection.
- `~/Downloads/sniff-demo.mp4` and `~/dev/quant-agent/docs/shots` were not used. Fresh live recordings of the same app were sharper.
- `/app` on sniff.quantbase.live now redirects to `/`. I recorded `/`.
- I did not use HyperFrames (see Approach).

## Checks run
- Stills at about 30 timestamps before the full render. I fixed: heading/window collisions (S3), the journey rail overlapping windows (it now shows only at the date jumps), the S5 zoom showing black past the image edge, graph camera framing and label overlap (S8), the empty 2 s at the start of S8 (added the "Here's how the graph works." caption and a faint network background), a messy hero/race crossfade overlap, and the hook/title overlap.
- Full contact sheet every 2 s, plus a 0.25 s-step strip around all 9 transitions, read from the encoded MP4.
- Audio (`ffmpeg ebur128` / `astats`): −14.3 LUFS, LRA 4.2 LU, true peak −1.3 dBFS, flat factor 0, so no clipping. Music sits about 13 dB under the voice while ducked. I also checked the spectrogram and the waveform.
- Commands: `python3 plan/tts.py`, `python3 plan/stt.py …`, `node plan/record.mjs`, `python3 plan/assemble.py`, `python3 plan/images.py`, `python3 plan/audio.py`, `node plan/render.mjs frames` (2850 frames in 900 s), `bash plan/encode.sh`.

## Not verified
- I could not listen to the mix. Levels, ducking and peaks are confirmed only by measurement, so a person should do one pass with headphones, especially for the synth music's taste and the "FalkorDB" pronunciation (STT heard "Falker DB" / "Falcor d").
- To rebuild: `node plan/render.mjs frames && bash plan/encode.sh` (about 17 min). The rendered PNG frames (5 GB) were deleted after encoding.

---

# T-L1b: promo fixes (18 Oct, re-rendered 20:21 IST)

Verdict: GO. All 5 items are done and both files have been re-rendered to the same paths. Nothing was committed, pushed or uploaded.

## Outputs
- `~/Downloads/sniff-hackathon-promo.mp4`: 107.4 s (was 95.0 s), 1920×1080, 30 fps, 45,790,440 B. −14.3 LUFS, true peak −1.3 dBFS.
- `~/Downloads/sniff-hackathon-promo-small.mp4`: 1280×720, 107.4 s, 9,956,372 B (under 10 MiB). −14.4 LUFS, true peak −1.0 dBFS.

## Changes
1. Team name. Every "Quant Agent" is now "QuantBase": the title card `index.html:103` ("by QuantBase"), the end card `index.html:227` ("Built by QuantBase on FalkorDB · WeMakeDevs × FalkorDB Graph Hacks") and the page `<title>`. The spoken VO line S08 was regenerated as "Built by QuantBase, on Falcor D B." A grep for "quant agent" in index.html, vo.json and plan/* now finds 0 matches.
2. Wallet count. The code already ended on 424,007, but the counter counted up from 0, so a paused frame showed an in-between number. 400,398 was one of those (about 0.7 s into the count). The three figures now appear already final (632,339 / 424,007 / 6,556) with a rise, so no frame can show a wrong number. I added a small line "~1.5M links between them", and the counter tick runs in the audio were replaced by one pop per figure.
3. Tracks 02 + 03. New scene `s8b`, 85.2–98.0 s, placed after "Every claim has proof. History, not a prediction." and before the close. The close moved +12.4 s.
   - Track 02 · Memory: memory-1440.png, then memory-session-1440.png, each scrolling down to the memory graph. Text: "Sniff remembers what it found. Other agents can build on it." VO S09 at 86.0 s: "Sniff remembers what it found, and other agents can build on it." (4.5 s)
   - Track 03 · Company brain: brain-1440.png, scrolling from the cited answer to the knowledge graph. Text: "Ask the company. Every answer cites its source." VO S10 at 92.0 s (3.1 s).
   - The 15–17 Oct app scene (S5) now uses the new UI in place of the old recording: home-hero-1440.png (ask box), which crossfades to app-evidence-1440.png. The camera moves to Sniff's findings with the E-tags (under the "evidence tag" pill), then to the connection map (under "the map lights up").
   - I used the screenshots and did not record the pages, so I made no network calls to the site. The screenshots were copied into `assets/img/`.
4. Pronunciation. The TTS text only now says "Falcor D B" (S03 and S08). On screen it is still "FalkorDB". Deepgram STT now hears it as "Falcore DB" in both lines; before the change it heard "Falker DB".
5. Audio. `plan/audio.py` now uses DUR 107.4 with an `SH = 12.4` shift for the close: intensity, arpeggio, kick and hats, the riser and hit, and the URL ticks all moved. I added a whoosh, a chip tick, card whooshes and a chime for the new scene. Ducking (−9 dB, 120/450 ms) and the two-pass loudnorm are unchanged.
   - The 96k AAC in the small file measured a true peak of −0.5 dBFS (+0.7 when encoded from the 256k AAC). `plan/encode.sh` now uses 128k AAC taken from `mix.wav`, which gives −1.0 dBFS and keeps the file under 10 MiB.
   - Note: I made the final small file by muxing the 2-pass video (598 kb/s) with 128k audio from `mix.wav`. That is the same result the edited `encode.sh` produces, but I did not re-run the edited script from start to finish.

## Commands run (real output)
- `python3 plan/tts.py S03 S08 S09 S10`: S03 12.28 s, S09 4.48 s, S10 3.12 s, S08 5.36 s. The key was read from `~/.config/celesticlabs/deepgram.env` and never printed.
- `python3 plan/stt.py S03 S08 S09 S10`: "A Falcore DB graph…", "Built by Quantbase on Falcore DB.", "SNF remembers what it found…" (STT spelled "Sniff" as "SNF" here; the audio itself is unchecked), "Ask the company. Every answer cites its source."
- `python3 plan/audio.py`: premix −20.67 LUFS / −2.30 dBTP, then mix.wav at −14.3 LUFS, true peak −1.5 dBFS, 107.4 s. The WavFileWarnings come from Deepgram's streamed WAV headers and were there before.
- `node plan/render.mjs stills …` (18 stills), then fixes: text that wrapped to an orphan word in s8b (serif reduced to 50 px), and a near-black dip between s8b and the close (they now overlap, s8b to 98.0 and s9 from 97.2).
- `node plan/render.mjs frames`: 3222 frames in 962 s, 0 pageerrors. Then `bash plan/encode.sh`.
- `ffmpeg ebur128=peak=true` on both MP4s: the figures above.

## Frame checks
- Contact sheet of the encoded MP4 every 2 s across the full 107 s, plus a 0.5 s strip over 83.5–98.5 s (S8 → Tracks → close).
- Full-res crops checked: title "BY QUANTBASE", end card "BUILT BY QUANTBASE ON FALKORDB · …", the 89.5 s memory frame and the 29–32 s stats.
- No overlaps, no black gaps and no wrong numbers seen.

## Not verified
- I could not listen to the result. Someone needs to do one headphone pass of S08 to check "Falcor D B" and QuantBase, and of S09 to check that "Sniff" is clear.
- The screenshots are from 18 Oct 19:45. I did not compare them against the live pages.
- PNG frames (about 5 GB) were deleted after encoding. Rebuild: `node plan/render.mjs frames && bash plan/encode.sh` (about 20 min).
