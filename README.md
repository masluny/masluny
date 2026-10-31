<p align="center">
  <img src="assets/parrot.svg" width="270" alt="a pixel macaw walking on a branch">
  <br>
  <sub>this is Pirrot. he walks while my models think. he walks a lot.</sub>
</p>

```
KACPER(1)                      User Commands                      KACPER(1)

NAME
     kacper – turns "how hard can it be" into a repository

SYNOPSIS
     kacper [--from=poland] [--lives=barcelona] [--mornings=off] idea ...

DESCRIPTION
     Builds tools for AI agents, trains models and ships native apps.
     Lives in Barcelona, a city full of wild parrots, which probably
     explains the bird.

OPTIONS
     --sleep          not implemented
     --scope-creep    on by default, can not be disabled

BUGS
     26 commits about app icons. 2 commits about tests.
     Considers this ratio correct.

SEE ALSO
     kacperkotowski.pl, x.com/137Kacper, linkedin.com/in/kacper-kotowski
```

### things i made instead of sleeping

**for AI agents**
- [write-as-me](https://github.com/masluny/write-as-me) clones your writing style into a skill, then scores how much the draft actually sounds like you
- [factual-research](https://github.com/masluny/factual-research) research agent that is not allowed to make up a single citation
- [cursor-computer-use](https://github.com/masluny/cursor-computer-use) gives any vision model eyes and hands on a Mac
- [front-design](https://github.com/masluny/front-design) reads what real designers say before it touches your UI
- [Pirrot](https://github.com/masluny/Pirrot) 🏴‍☠️ the bird above + an NVIDIA key rotator for the pi agent

**ML**
- [ripple](https://github.com/masluny/ripple) predicts how one late LOT flight in Warsaw ruins everyone's connection (probabilistic GNN)

**apps & games**
- [horyzont](https://github.com/masluny/horyzont) island driving game in Godot with 143k trees, because 142k looked empty
- [Revind](https://github.com/masluny/video-editor) desktop video editor in Tauri, Rust and FFmpeg
- [OptiTrain](https://github.com/masluny/OptiTrain) reads Apple Health and tells you if today is a training day or a sofa day
- [gridatlas](https://github.com/masluny/gridatlas) the whole world offline, cut into ~4 km windows ([try it](https://masluny.github.io/gridatlas/))

### when i actually code

<p align="center"><img src="assets/commit-clock.svg" alt="commits by hour of day"></p>

<p align="center">
<!-- clock:start -->
<sub>42% of my commits happen after 9pm or before 6am. Between 07:00 and 11:00: zero. Not one, ever. Last seen pushing to <a href="https://github.com/masluny/Pirrot">Pirrot</a> on Oct 31 at 01:13.</sub>
<!-- clock:end -->
</p>

<details>
<summary><sub>🦜 how the bird is made</sub></summary>

<br>

This is the whole parrot. Twelve strings. `R` is red, `O` is the beak, `K` is the eye, `y` and `B` are the wing, `f` are the feet.

```
....RR......
..RRRR......
.RRWWROOO...
.RRWKROOOO..
.RRRRoOOO...
.RRRRooO....
..RyyRR.....
.RyyyRR.....
.RBBRR......
.RBRR.......
..RRR.......
..f.f.......
```

In the terminal every two of these rows become one line of `▀` characters in 24-bit color. Here [a script](scripts/parrot.py) turns the same strings into the SVG at the top.

</details>

<sub>The chart is redrawn by a bot every night at 3am UTC, which makes him the only one on this account with a regular sleep schedule.</sub>
