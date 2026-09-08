# Markdown cheat sheet

Reference for the writeups. Not a deliverable. Preview any `.md` in VS Code with `Ctrl+Shift+V`.

Rule zero: **blank line between every block** (paragraph, list, code, table, heading). Most rendering bugs are a missing blank line.

## Headings

```markdown
# Title (one per file)
## Section
### Subsection (stop here)
```

## Text

| type | this |
|---|---|
| `**bold**` | **bold** |
| `*italic*` | *italic* |
| `` `code` `` | `code` |
| `~~strike~~` | ~~strike~~ |

Two spaces at the end of a line force a line break; otherwise a single newline is ignored and lines join into one paragraph. Blank line = new paragraph.

## Lists

```markdown
- bullet
- bullet
  - nested (two spaces)

1. step
2. step
3. step

- [ ] todo
- [x] done
```

Bullets: `-`, `*`, `+` all work; pick `-` and stick with it. Numbered lists renumber themselves; `1. 1. 1.` renders as 1, 2, 3.

## Code

Inline: `` `play_id 149` `` → `play_id 149`. Use for anything a reader might search for or type.

Block: three backticks, a language tag, the code, three backticks.

````markdown
```python
openers = period_openers(pbpp)
```

```bash
python on_court.py --game all --validate
```

```text
validate passed: 9930 rows, 993 plays, 2 games
```

```sql
SELECT COUNT(*) FROM pbp_players_on_court;
```
````

Tags that matter: `python`, `bash`, `sql`, `text` (for program output), `json`, `yaml`. Untagged blocks render but with no highlighting.

To show a code block *inside* a code block (like above), fence the outer one with four backticks.

## Tables

```markdown
| column | column | number |
|---|---|---:|
| text | text | 9930 |
| text | text | 1011 |
```

| column | column | number |
|---|---|---:|
| text | text | 9930 |
| text | text | 1011 |

Header row, then the `|---|` separator row, then data. `---:` right-aligns (use for numbers), `:---:` centers. Pipes don't have to line up in the source, but it's easier to read if they do. Cells can hold inline code and bold, not lists or line breaks.

## Links and images

```markdown
[text](https://example.com)
[on_court.py](../on_court.py)            relative path from the .md file's folder
[section](#time-complexity)              heading anchor: lowercase, spaces -> hyphens, punctuation dropped
![alt text](system-design.drawio.png)    image, same relative-path rule
```

## Quotes and rules

```markdown
> quoted text, e.g. the exact requirement from the PDF

---
```

`>` renders as a blockquote. Three dashes alone on a line = horizontal rule (needs blank lines around it or it turns the line above into a heading).

## Escaping

Backslash before a character that would otherwise format: `\*not italic\*`, `\_snake\_case\_`, `\#not a heading`. Inside backticks nothing is interpreted, so `` `a_b_c` `` needs no escaping.

## Things that break

| symptom | cause |
|---|---|
| list renders as one paragraph | no blank line before the list |
| table renders as pipes and dashes | no blank line before it, or missing `\|---\|` row |
| code block swallows the rest of the file | unclosed triple backticks |
| `#` heading renders as literal `#` | no space after the `#` |
| line above `---` became a heading | no blank line between them |
| numbered list restarts at 1 | a paragraph or code block between items with no indent (indent the block 3 spaces to keep it inside the item) |

## Habits for a technical writeup

- Lead each section with the conclusion, then evidence.
- Output in `text` blocks, commands in `bash` blocks, never as prose.
- Numbers in tables.
- Bold one thing per section at most.
- Inline code for identifiers (`walk_plays()`, `--game`, `event_id`), plain text for ordinary words.
- Relative links to the files you're describing.
- No em-dashes. Colon, comma, or new sentence.
