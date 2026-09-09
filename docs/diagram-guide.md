# Part 2: diagram build guide

Everything you need to draw the system diagram and fill in `docs/system-design.md`.

## What `system-design.md` is

It is the Part 2 writeup. The PDF asks for two things and this file is the second one:

> Use your knowledge in system design to develop a **system diagram (draw.io or similar) and write up** to explain your decisions, why you've decided to work with particular tools or technology, and how your system might scale. Your system should be end-to-end, from retrieving the data to making it available for others. Think about how to ingest the play-by-play data, how does your code know when to run, and the storage strategy.

So four questions have to be answered somewhere in it:

1. How does the play-by-play data get in
2. How does the code know when to run
3. Where does the data live
4. How does it scale

The file already exists in your repo with headings. Nothing is written under them yet. The diagram gets embedded at the top with the image link that is already there.

Assume you have only two things: the script you wrote, and a play-by-play REST API from a data provider. Everything else you are inventing.

---

## Decide the architecture before opening draw.io

Drawing is the easy part. Knowing what goes in the boxes is the work. Here is a design that fits this problem. Change anything you disagree with, but be able to defend whatever you draw.

### The flow

**1. Schedule check.** Once a day, hit the provider's schedule endpoint and get the list of games and start times. This is what tells the system there is work to do.

**2. Poller.** For each game, from tip-off until the final buzzer, call the play-by-play endpoint every 20 to 30 seconds. One task per game. On a busy night that is maybe 12 tasks running at once.

**3. Raw landing.** Write every API response to object storage as-is, partitioned by date and game. Nothing transformed. This is what lets you rebuild the whole table later if you find a bug in the logic, and it is what you diff against when the provider changes a field.

**4. Trigger.** New plays landing for a game is the signal to recompute that game. Not a clock, an event. The poller drops a message on a queue, the compute job picks it up.

**5. Compute.** Your script, containerized, running for one game. It reads that game's raw plays, runs the same six functions, writes to the table.

**6. Storage.** The `pbp_players_on_court` table, plus the source tables it joins to.

**7. Serving.** Analysts querying SQL directly, a BI tool, and downstream models that need lineup context.

### The part specific to your algorithm

Your period-opener rule needs a player to appear in a period before it knows he was on the floor. Three minutes into a quarter you might only have evidence for three of the five. The lineup is not fully determined until enough plays have happened.

That means a live pipeline cannot compute a period's lineup once and be done. Two ways out:

- Only finalize a period once it ends, and serve the earlier periods in the meantime.
- Reprocess the entire game on every update and let the answer improve as evidence arrives.

The second is better here, and the reason is something you already built. Your write is delete-then-insert per game, so reprocessing a game is safe and leaves the table exactly matching the current state of the source. Every update self-corrects. A game is 500 plays, so recomputing the whole thing takes no time at all.

Say this in the writeup. It connects Part 1 to Part 2 and it is the kind of thing that separates a diagram from a real design.

### Tool choices

Pick one per row and be ready to say why.

| job | choice | why |
|---|---|---|
| orchestration | Airflow | the standard for this, gives you retries, backfill, and a schedule in one place |
| poller and compute | containers on ECS or Cloud Run | one image, scales per game, nothing to keep warm between games |
| queue | SQS or Pub/Sub | decouples polling from compute so a slow job does not block ingestion |
| raw landing | S3 | cheap, immutable, replayable |
| serving | MySQL now, Postgres or Snowflake if it grows | matches what you built, and the data is small |
| monitoring | alerts on the validate step | the checks you already wrote become the pipeline's health signal |

### Scale

A season is about 1,230 games and 615,000 plays, so roughly 6 million rows. That is small. The reason to design it this way is not volume, it is concurrency during the 7pm to 10pm window and the ability to reprocess history without hand-holding.

Games share nothing, so the compute layer scales by adding workers. The bottleneck is the provider's rate limit, not your code.

---

## What you are drawing

Top to bottom. The provider and the daily schedule check feed a poller at the top. Data drops straight down through raw storage, a queue, your job, and the database. The people who read it sit at the bottom. A dashed box around the middle shows what you own.

<!--DIAGRAM_SVG-->

Eleven boxes. The example in the PDF has three, so this is well past the bar.

### What goes in each box and why it is there

**Provider play-by-play API.** The vendor's REST endpoint. This is the one thing the prompt says you already have, so it goes on the far left, outside your boundary. Everything else on the diagram is something you are proposing to build.

**Schedule check (daily).** A small task that runs once a day and asks the provider which games are on tonight and when they start. It is on the diagram because without it nothing knows there is work to do. This is half the answer to "how does your code know when to run."

**Poller.** A container, one per live game. From tip-off to the final buzzer it calls the play-by-play endpoint every 20 seconds. One per game rather than one for everything, so a stuck game does not hold up the other eleven.

**Raw landing (S3).** Object storage holding every API response exactly as it came back, partitioned by date and game. It is on the diagram because it is the thing that makes the whole pipeline replayable. If the period-opener logic has a bug, you rebuild from here rather than refetching.

**Queue.** One message per batch of new plays. It sits between the poller and the compute job so that ingestion never waits on compute. This is the other half of "how does your code know when to run": the code runs because a message arrived, not because a timer fired.

**on_court job.** Your script, in a container, running for one game. Reads that game's raw plays, runs the six functions, validates, writes. This is the box that is actually Part 1.

**MySQL.** The serving database. Holds `pbp_players_on_court` plus the three source tables it joins to.

**Airflow.** The orchestrator. It owns the daily schedule, the retries when the provider 500s, and backfills when you need to rerun a month. It sits below the pipeline with an arrow up because it drives things rather than passing data through.

**Analysts, BI dashboard, Downstream models.** The consumers, outside the boundary on the right. They are on the diagram because the prompt asks for end-to-end "to making it available for others." Without them the diagram stops at a database and never answers that.

### What to leave out

A first diagram tends to sprawl. Skip auth, VPCs, load balancers, CI/CD, logging infrastructure and anything else that is true of every system. The reviewer is looking at how play-by-play data becomes a lineup table, so draw only the data path. If a box does not touch the data or decide when something runs, cut it.

---

## Draw it

Written for someone who has never opened draw.io. Every click.

### 1. Install the extension

`Ctrl+Shift+X`, search `hediet.vscode-drawio`, install **Draw.io Integration**. It is already in this workspace's recommendations, so it may be installed.

### 2. Create the file

In the Explorer, right-click the `docs` folder, **New File**, and name it exactly:

```
system-design.drawio.png
```

The double extension is the trick. VS Code opens it in a draw.io editor, and when you save it writes a real PNG with the diagram data tucked inside. You get an editable diagram and an embeddable image from one file, no export step.

The tab should open to a blank white canvas with a shape panel down the left. If instead you get a broken-image icon or a hex dump, close the tab, delete the file, and make one named `system-design.drawio` instead. That works the same way but you export a PNG at the end (**File > Export as > PNG**).

`docs/system-design.md` already has `![system diagram](system-design.drawio.png)` at the top, so the image appears there as soon as the file has content.

### 3. Learn the four things you need

**Left panel** is shapes. There is a search box at the top of it. Type `rectangle` and drag one onto the canvas.

**Right panel** is Format, with three tabs: **Style**, **Text**, **Arrange**. Style sets colors. Arrange sets exact size and position, which is how you avoid fighting the mouse.

**To label a shape**, double-click it, type, press `Escape`.

**To connect two shapes**, hover over the edge of the first one until blue arrows appear around it. Drag from the edge onto the second shape and let go when the second shape lights up blue. Do not drag from the middle, that moves the shape.

### 4. The one shortcut that matters

Select any shape and press `Ctrl+E`. A box opens containing that shape's entire style as a single string. Replace it, click OK, and the shape takes on every property at once. Fill, border, font, corners, dashes.

That is how you do all the styling in this diagram. The Style panel on the right does the same job one checkbox at a time.

Three strings, one per group.

**Things you run** (Schedule check, Poller, Airflow, Queue, on_court job):

```
rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=13;container=0;
```

**Storage** (Raw landing, MySQL):

```
rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontSize=13;container=0;
```

**Outside your control** (Provider API, Analysts, BI dashboard, Downstream models):

```
rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#999999;fontSize=13;container=0;
```

`container=0` stops draw.io deciding a big rectangle is a folder and swallowing shapes you drag near it. It will do that otherwise and it is annoying to undo.

### 5. Build one box properly, then copy it

Drag one rectangle onto the canvas. Then:

**Size and position.** Right panel, **Arrange** tab. Type `220` and `62` into Width and Height, then `30` and `40` into Left and Top.

**Label.** Double-click the shape. Type `Provider`, press `Shift+Enter` for a second line, type `play-by-play API`. Then drag-select just the word `Provider` and press `Ctrl+B`. Press `Escape` to finish.

The two-line bold-then-plain label is what makes these readable. Do it on every box.

**Style.** `Ctrl+E`, paste the "outside your control" string, OK.

Now copy it. `Ctrl+C` then `Ctrl+V` gives you a duplicate carrying the same size, font and style. Change its position in Arrange, double-click to retype the label, and `Ctrl+E` only if it belongs to a different color group.

Ten more boxes:

| label (bold line / plain line) | Left | Top | W | H | style |
|---|---:|---:|---:|---:|---|
| **Provider** / play-by-play API | 30 | 40 | 220 | 62 | outside |
| **Schedule check** / daily | 610 | 46 | 220 | 62 | run |
| **Poller** / one per live game, 20s | 320 | 170 | 220 | 62 | run |
| **Airflow** / schedule, retries, backfill | 610 | 170 | 220 | 62 | run |
| **Raw landing** / S3 by date and game | 320 | 300 | 220 | 62 | storage |
| **Queue** / one message per update | 320 | 430 | 220 | 62 | run |
| **on_court job** / container, one game | 320 | 560 | 220 | 62 | run |
| **MySQL** / pbp_players_on_court | 320 | 690 | 220 | 62 | storage |
| **Analysts (SQL)** | 20 | 820 | 200 | 52 | outside |
| **BI dashboard** | 330 | 820 | 200 | 52 | outside |
| **Downstream models** | 640 | 820 | 200 | 52 | outside |

The bottom three are one line each, no `Shift+Enter`.

If you lose track of the canvas, `Ctrl+Shift+H` fits everything to the window.

### 6. Lines

Hover over the **edge** of a shape, not the middle. The border turns green and four small arrows appear around it. Drag from the edge onto the target shape and let go when the whole target lights up with a blue outline.

Two kinds of connection, and the difference matters:

- Let go when the whole shape is outlined blue and you get a **floating** connection. The line picks its own attachment point and reroutes itself when you move boxes. This is what you want.
- Let go on a small green circle on the shape's border and you get a **fixed** connection, pinned to that exact point. It will look wrong the moment you nudge anything.

Draw these ten:

| from | to | label |
|---|---|---|
| Provider play-by-play API | Poller | every 20s while live |
| Schedule check | Poller | today's games |
| Airflow | Poller | |
| Poller | Raw landing | raw responses |
| Raw landing | Queue | new plays |
| Queue | on_court job | reprocess whole game |
| on_court job | MySQL | delete + insert per game |
| MySQL | Analysts (SQL) | |
| MySQL | BI dashboard | |
| MySQL | Downstream models | |

**To label a line**, double-click the middle of it, type, `Escape`. The text sits on the line with a white background, which is correct.

**To style the lines**, select one, `Ctrl+E`, paste:

```
edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#555555;fontSize=11;fontColor=#555555;
```

`orthogonalEdgeStyle` gives you right-angle elbows rather than diagonals, which is what the two arrows into the Poller need.

Faster: style one line, select it, `Ctrl+Alt+C` to copy its style, then select the other nine (`Shift`-click each) and `Ctrl+Alt+V` to paste the style onto all of them.

**If a line takes an ugly route**, drag the middle of it. That adds a waypoint and the line bends through it. Right-click the line and **Clear Waypoints** undoes all of that.

### 7. The dashed boundary

Drag out one more rectangle. Arrange tab: Width `550`, Height `756`, Left `300`, Top `18`.

`Ctrl+E`, and replace everything with:

```
rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=none;strokeColor=#888888;verticalAlign=top;align=left;spacingLeft=10;spacingTop=6;fontColor=#888888;fontSize=12;container=0;
```

Each part is doing something: `dashed=1` is the dashes, `fillColor=none` makes it transparent so the boxes show through, and `verticalAlign=top;align=left` with the two spacings puts the label in the top-left corner instead of the middle.

Double-click it and type `our system`.

Then `Ctrl+Shift+B` to send it behind everything. Without that it sits on top and blocks clicks.

**The gotcha:** because it has no fill, clicking inside it selects whatever is underneath, not the rectangle. To select the boundary again you have to click directly on its dashed border. If you cannot get hold of it, right-click empty canvas, **Select All**, then `Shift`-click the boxes to deselect them.

The provider API ends up outside the boundary at the top left, and the three consumers outside at the bottom. That is deliberate. The box is showing what you are responsible for.

### 8. Legend

Four more rectangles in the empty column on the left, under the Provider box. Same plain rectangle from **General** as every other box, just smaller.

The three swatches are 16 by 16. The label sits outside each one to the right, so it is three shapes rather than six.

| what it becomes | Left | Top | W | H | label |
|---|---:|---:|---:|---:|---|
| surrounding box | 20 | 540 | 200 | 110 | key |
| blue swatch | 30 | 570 | 16 | 16 | compute |
| green swatch | 30 | 600 | 16 | 16 | storage |
| grey swatch | 30 | 630 | 16 | 16 | external |

Swatch style, blue shown. Swap `fillColor` and `strokeColor` for the other two.

```
rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=6;fontSize=12;fontColor=#333333;
```

`labelPosition=right` is what pushes the text outside the square instead of cramming it inside. `align=left` then left-aligns it and `spacingLeft=6` gives it a gap off the swatch.

Style for the surrounding box:

```
rounded=0;html=1;fillColor=none;strokeColor=#cccccc;verticalAlign=top;align=left;spacingLeft=8;spacingTop=4;fontSize=11;fontColor=#999999;container=0;
```

Then `Ctrl+Shift+B` on the surrounding box so it sits behind the swatches.

Skip the surrounding box if the three swatches read clearly on their own. Skip the whole legend if you would rather explain the colors in one sentence in `system-design.md`.

### 9. Tidy

- `Shift`-click a group of boxes, then **Arrange** tab, **Align** buttons to line them up
- `Ctrl+Shift+H` fits the diagram to the window
- **Extras > Edit Diagram** shows the underlying XML, which is the escape hatch if something ends up somewhere you cannot click
- `Ctrl+Shift+G` groups a selection, `Ctrl+Shift+U` ungroups

### 10. Save and check

`Ctrl+S`, same as any file.

Open `docs/system-design.md` and press `Ctrl+Shift+V`. The diagram should appear at the top. If you get a broken image, the filename does not match the link on line 3.

Commit the PNG. It is the Part 2 deliverable.

---

## Then write `system-design.md`

The headings are already there. What belongs under each:

**Goal and assumptions.** What you were given (the script, a REST API), what you are assuming (provider has a schedule endpoint, plays arrive within seconds, roughly 12 concurrent games at peak).

**Architecture overview.** The flow in a paragraph, pointing at the diagram.

**Ingestion.** Poll, why polling instead of waiting for a webhook you were not offered, what you write to raw storage and why raw first.

**Triggering.** The four-question list said "how does your code know when to run." Answer it directly: daily schedule check finds games, poller runs while a game is live, new plays put a message on the queue, the queue starts the job. Not a cron that guesses.

**Compute.** Your script, one game per run, containerized. The mid-period evidence problem and why reprocessing the whole game each time is the answer.

**Storage.** Raw JSON in object storage forever. Derived table in MySQL. Why both.

**Serving.** Who reads it and how.

**Data quality and observability.** `validate` becomes the pipeline's gate. What you alert on: a lineup that does not resolve to five, a game that stops updating mid-quarter, a play count that goes backwards.

**Scaling.** The season numbers. What breaks first (provider rate limit, not your code).

**Tool choices and alternatives considered.** The table above, in prose. Mention what you did not pick and why, briefly. Spark for 6 million rows would be the obvious wrong answer.

**Failure modes and recovery.** Provider goes down mid-game. A play gets corrected after the fact. The job crashes halfway. Answer each in a sentence. Your idempotent write covers most of it.

Keep it about the same length as the Part 1 walkthrough. The diagram carries the structure, the writeup explains the choices.
