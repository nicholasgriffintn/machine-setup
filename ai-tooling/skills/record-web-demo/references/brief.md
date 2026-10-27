# Creative brief

A demo nobody briefed ends up generic. Agree the brief **before writing the config**, in one round of questions. Use the structured question tool if your harness has one (multiple choice with a recommended first option). Otherwise ask a short numbered list. Skip anything the user already answered, and say which defaults you picked for the rest.

## Questions

- **Purpose and destination.** PR or docs, launch or social post, internal QA, or sales walkthrough. This drives every default below.
- **Fun level.** Straight, Friendly or Playful (table below). Recommend Friendly unless the destination says otherwise.
- **Look.** Browser frame or not, light or dark, any brand colours for the frame gradient.
- **Narration.** None, or captions read aloud, or a separate script. Provider: macOS voices (free, offline, robotic), OpenAI (natural, steerable tone, paid) or ElevenLabs (most natural, paid). Only offer the paid providers whose key is set (`OPENAI_API_KEY`, `ELEVENLABS_API_KEY`). Mention the cost when you offer them.
- **Music.** None, the user's own file, a royalty-free track from Jamendo (needs `JAMENDO_CLIENT_ID`; attribution required), or generated with ElevenLabs Music (paid, fits the video length exactly).

## Fun level

| | Straight | Friendly | Playful |
|---|---|---|---|
| Captions | Plain statements of what is happening | Benefit-led, conversational | Punchy, a little cheeky. One emoji at most, and only if the brand allows it |
| Narration `style` | "Calm, clear, neutral product walkthrough" | "Warm, upbeat, conversational, like showing a colleague" | "Energetic and playful, with light humour and expressive pacing" |
| Music mood | None, or minimal ambient | Light acoustic or lo-fi, unobtrusive | Upbeat electronic or funk, bright |
| `speed` | 1 | 1 | 1.15 |
| `zoom.max` | 1.5 | 1.8 | 2.2 |
| `frame` | Off, or a neutral background | Brand gradient | Bold gradient |

Playful still means accurate. Never invent features, numbers or claims the product does not back up. No memes or third-party characters: rights are unclear and they date badly.

## Offer real options before recording

Let the user hear and choose rather than describing options in the abstract:

- **Voices.** List with `voices --provider <p>` (add `--locale en_GB` for macOS). Pick 2–3 that fit the fun level and render the same line with each: `preview-voice --provider <p> --voice <v> --text "<first caption>" --style "<style>" --out .demo-recording/samples/<v>`. Share the files and let the user pick.
- **Jamendo tracks.** Run `music-search "<mood words>"` and present 3–5 results as title, artist, length, licence and page link (the `preview` URL streams in a browser). Only attribution (`by`) and share-alike (`by-sa`) licences are returned. Put the chosen `credit` line wherever the video is published.
- **Generated music.** Propose the prompt you would send, built from the mood and any brand words, and get a yes before using it. Generation is paid and happens after recording, at the final length.

Downloading a track or calling a paid API needs the user's explicit choice from these options. Put that choice in the config (`narration`, `music`) and record nothing until they have picked.

## Writing narration

- **One line per beat**, in the step's `say` field, or set `"fromCaptions": true` to read the captions.
- **Short sentences.** Spoken text runs slower than reading. Aim for under 2.5 words per second of the beat.
- **Say why, not what.** The viewer can see the click. Narrate the outcome ("Orders go out the same day") rather than the action ("Now I click Submit").
- **Each step holds until its line finishes**, so timing takes care of itself. Waits that overlap speech are not sped up.
