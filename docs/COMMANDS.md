# Chat commands reference

Type commands in the message box. They start with `/`.

## Everyone

| Command | Arguments | Description |
|---------|-----------|-------------|
| `/help` | — | Show this list in-chat |
| `/timeskip` | optional text | Insert a **Scene** time-skip header |
| `/scene` | text | Insert a **Scene** beat |
| `/world` | text | Insert a **World** lore/rule beat |
| `/world-test` | — | Cue the model to prove world awareness |
| `/pin` | text | Pin a beat the model should not contradict |
| `/pins` | — | List pins |
| `/mute` | topic | Soft-avoid a topic |
| `/unmute` | topic | Remove a mute |
| `/mutes` | — | List mutes |
| `/branch` | name | Create & activate a named branch |
| `/branches` | — | List branches |
| `/intensity` | 0–100 | Emotional intensity for this chat |
| `/filter` | strict\|moderate\|mature\|unfiltered | Content filter this chat |
| `/continue` | — | Generate next beat without a user line |
| `/hint` | — | Suggest user replies |
| `/as` | Name text | Inject a side-character line |
| `/side-test` | Name | Inject NPC + pin presence for testing |
| `/roster` | — | List side NPCs from the character card |
| `/age` | 19 or +1 | Temporary main character age |
| `/age-side` | Name 17 or +1 | Temporary side age |
| `/clothes` | description | Temporary main outfit |
| `/clothes-side` | Name description | Temporary side outfit |

## Buttons near the chat box

| Control | Purpose |
|---------|---------|
| **Hint** | Suggest 3 replies from persona + history |
| **Continue** | Bot keeps going without you typing |
| **Send** | Normal user message |
| **Gear** | History, Memory, Filter, Layout, Wallpaper, Style, Persona, Intensity, Branches |

## Dev mode (Settings → Dev mode)

Extra tools for testing memory, backstory, forced sides, etc. Use in-chat `/help` when dev mode is on.
