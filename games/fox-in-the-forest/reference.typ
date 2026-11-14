// Card-size reference cards for The Fox in the Forest Deluxe.
//
// Two double-sided cards:
//   A: scoring / suit card abilities
//   B: special cards 1 / special cards 2
//
// Letter sheet for a copy shop, 2 copies of each: print duplex at 100%,
// flip on the LONG edge, then cut on the crop marks (6 guillotine cuts):
//   typst compile games/fox-in-the-forest/reference.typ tmp/fox-reference.pdf
// Individual card-size pages (A front, A back, B front, B back):
//   typst compile --input layout=cards games/fox-in-the-forest/reference.typ tmp/fox-reference-cards.pdf

#let layout = sys.inputs.at("layout", default: "sheet")

#let card-w = 63.5mm
#let card-h = 88.9mm

#let ink = rgb("#2b2118")
#let accent = rgb("#8a3b12")
#let rule-color = rgb("#b39a78")
#let paper = rgb("#fbf6ec")
#let body-size = 7.6pt

#let title(body) = align(center, text(size: 11pt, weight: "bold", fill: accent, body))
#let sep = line(length: 100%, stroke: 0.4pt + rule-color)

// One ability row: rank badge, name, text.
#let ability(rank, name, body) = grid(
  columns: (5mm, 1fr),
  column-gutter: 1.5mm,
  align(center + horizon, box(
    width: 5mm,
    height: 5mm,
    radius: 50%,
    stroke: 0.6pt + accent,
    align(center + horizon, text(size: 8.5pt, weight: "bold", fill: accent, rank)),
  )),
  [*#name:* #body],
)

#let abilities(..rows) = stack(spacing: 1fr, ..rows.pos())

// A card-size box with inner margin. Content gets the full inner height, so
// `1fr` spacing spreads things out to fill the card.
#let card(body) = block(
  width: card-w,
  height: card-h,
  inset: 4mm,
  fill: paper,
  breakable: false,
  {
    set text(
      font: "Libertinus Serif",
      size: body-size,
      fill: ink,
      hyphenate: true,
    )
    set par(leading: 0.45em, justify: false)
    body
  },
)

// Title, rule, then abilities filling the rest of the card.
#let ability-card(heading, ..rows, footer: none) = card({
  title(heading)
  v(-1mm)
  sep
  v(1mm)
  block(height: 1fr, abilities(..rows))
  if footer != none {
    v(1mm)
    sep
    text(size: 6.5pt, footer)
  }
})

// ---------------------------------------------------------------- Card A
#let a-front = card({
  set text(size: 8.6pt)
  title[The Fox in the Forest]
  v(-1mm)
  sep
  v(1fr)
  list(
    spacing: 1.2em,
    [Deal *13* cards to each player.],
    [Flip the next card: the *decree*. Its suit is trump.],
    [Play until someone has *21* points \ #text(size: 7.4pt)[(shorter game: *16*, longer game: *35*)]],
  )
  v(1fr)
  set text(size: 10pt)
  table(
    columns: (1fr, 1fr, 1.4fr),
    // Inner lines only, no outline.
    stroke: (x, y) => (
      left: if x > 0 { 0.5pt + rule-color },
      top: if y > 0 { 0.5pt + rule-color },
    ),
    inset: (x: 2mm, y: 2mm),
    align: (center, center, left + horizon),
    table.header(..([Tricks], [Points], [Result]).map(h => text(fill: accent, weight: "bold", h))),
    [0–3], [6], [Humble],
    [4], [1], table.cell(rowspan: 3)[Defeated],
    [5], [2],
    [6], [3],
    [7–9], [6], [Victorious],
    [10–13], [0], [Greedy],
  )
  v(1fr)
})

#let a-back = ability-card(
  [Suit Card Abilities],
  ability[11][Monarch][When you lead this, if your opponent has a card of this suit, they must play either the Swan of this suit or their highest ranked card of this suit.],
  ability[9][Witch][When determining the winner of a trick with a single Witch, treat the Witch as if it were in the trump suit.],
  ability[8][Poison][The winner of the trick loses 1 point for each Poison in the trick.],
  ability[7][Treasure][The winner of the trick gains 1 point for each Treasure in the trick.],
  ability[5][Woodcutter][When you play this, draw 1 card. Then discard any 1 card to the bottom of the deck, face down.],
  ability[3][Fox][When you play this, you may exchange the decree card with a card from your hand.],
  ability[1][Swan][If you play this and lose the trick, you lead the next trick.],
)

// ---------------------------------------------------------------- Card B
#let b-front = ability-card(
  [Special Cards],
  ability[?][Bow][This always beats any trump card or special card, and it always loses to any other card.],
  ability[?][Hammer][If you follow with this, name a suit. Your opponent must discard their card to the bottom of the deck, face down. They must draw 1 card, then play 1 card to the trick of the named suit, if possible. This always beats any odd card, and it always loses to any other card.],
  ability[?][Potion][When you play this, discard it and another card from your hand to the bottom of the deck, face down. Draw 2 cards, then keep 1 in your hand and play 1 to the trick, ignoring suit requirements.],
  ability[?][Shovel][When you play this, you may take 1 random card from the last trick you won and play it to the trick instead. If you do not or cannot, you lose the trick.],
  ability[8][Axe][If you follow a Woodcutter with this, use the Woodcutter's ability and win the trick. Otherwise, this is an unsuited 8.],
)

#let b-back = ability-card(
  [Special Cards],
  ability[6][Tree][If you lead this, your opponent must play 1 random card from their hand to the trick, ignoring suit requirements. This is an unsuited 6.],
  ability[4][Fairy][When you play this, look at up to 2 random cards from your opponent's hand. You may take 1 of those cards. If you do, give your opponent 1 card from your hand. This is an unsuited 4.],
  ability[2][Crown][You may add this to any legal play of a non-special card. If you do, draw 1 card. Ignore any ability your other card has and treat it as a Monarch of its suit when determining the winner of the trick. You may instead play this on its own as an unsuited 2.],
  ability[M][Mirror][This is always treated as if it were identical to the current decree card in rank, suit, and ability.],
  footer: [*Unsuited:* matches the other card's suit. *Identical cards:* leader wins. *Special decree:* no trump (a single Witch still counts as trump).],
)

// ---------------------------------------------------------------- Output
#if layout == "cards" {
  set page(width: card-w, height: card-h, margin: 0pt)
  a-front
  pagebreak()
  a-back
  pagebreak()
  b-front
  pagebreak()
  b-back
} else {
  // Letter sheet: the four cards butt together in a 2x2 block centered on the
  // page, so it takes 6 straight cuts. The background bleeds past the block's
  // outer edges; crop marks sit outside the bleed on every cut line. Each row
  // holds two copies of the same card, so the block is left-right symmetric:
  // with a long-edge flip every back lands behind its front, right side up.
  set page(paper: "us-letter", margin: 0pt)
  let bleed = 3mm
  let mark-len = 5mm
  let mark-off = bleed + 1.5mm
  let mark = 0.3pt + black
  let x0 = (8.5in - 2 * card-w) / 2
  let y0 = (11in - 2 * card-h) / 2
  let xs = (x0, x0 + card-w, x0 + 2 * card-w)
  let ys = (y0, y0 + card-h, y0 + 2 * card-h)

  let sheet(rows) = {
    place(dx: x0 - bleed, dy: y0 - bleed, rect(
      width: 2 * card-w + 2 * bleed,
      height: 2 * card-h + 2 * bleed,
      fill: paper,
    ))
    for (i, c) in rows.enumerate() {
      for j in (0, 1) {
        place(dx: xs.at(j), dy: ys.at(i), c)
      }
    }
    for x in xs {
      place(dx: x, dy: ys.first() - mark-off - mark-len, line(length: mark-len, angle: 90deg, stroke: mark))
      place(dx: x, dy: ys.last() + mark-off, line(length: mark-len, angle: 90deg, stroke: mark))
    }
    for y in ys {
      place(dx: xs.first() - mark-off - mark-len, dy: y, line(length: mark-len, stroke: mark))
      place(dx: xs.last() + mark-off, dy: y, line(length: mark-len, stroke: mark))
    }
  }

  sheet((a-front, b-front))
  pagebreak()
  sheet((a-back, b-back))
}
