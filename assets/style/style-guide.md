# Brawler Asset Style Guide

## Tool-Decision

**Tool:** ChatGPT Plus (DALL-E 3)
**Subscription:** Robert Parei — Plus
**Kosten:** Inkludiert in Plus-Abo
**Prompt-Pattern:** Text-Prompt + optionales Referenz-Bild-Upload (Brawl-Stars-Screenshot)
**Style-Reference:** lokal unter `assets/style/style-reference.png` (gitignored)

## Art Style

- **Inspiration:** Brawl Stars (Supercell)
- Dicke schwarze Outlines
- Knallige, gesättigte Farben
- Chibi-Proportionen (großer Kopf, kompakter Körper)
- Sauberes Cel-Shading, kein realistisches Rendering
- Weißer Hintergrund beim Generieren → nachträglich transparent machen (Preview / GIMP / online)
- Ausgabe: PNG, min. 512×512 px, RGBA

## Tier-Progression (geplant)

| Tier | Name | Unlock |
|---|---|---|
| 1 | Common | Start |
| 2 | Rare | 30 Coins |
| 3 | Epic | 100 Coins |
| 4 | Mythic | 250 Coins |
| 5 | Legendary | 500 Coins + 30d Streak |

Dateiname-Schema: `assets/brawlers/<user>-<fach>/<tier>-idle.png`

## Charakter-Definitionen

### Robert
- Alter: ~40 Jahre
- Haare: dunkel
- Typ: erwachsener Mann, sportlich-casual

### Friedrich
- Alter: 11 Jahre
- Haare: dunkelblond
- Typ: Schuljunge, energisch

### Jenni
- Alter: 43 Jahre
- Haare: blond
- Typ: Frau, freundlich
- Fächer: TBD (Onboarding Phase 4.1b)

## Fach-Accessoires

| Fach | Accessoire | Stil |
|---|---|---|
| Englisch | Union-Jack-Abzeichen oder kleines Flaggen-Pin | subtil, am Outfit |
| Italienisch | Italienische Flagge (Trikolore) als Pin | subtil, am Outfit |
| Musik | Kopfhörer (um den Hals oder auf dem Kopf) | erkennbar aber nicht übertrieben |
| Mathematik | Kleines Taschenrechner-Symbol oder Zahlen-Emblem | am Gürtel oder Tasche |

## Prompt-Vorlage

```
Generate a game character avatar in Brawl Stars art style.
Character: [BESCHREIBUNG]
Accessory: [FACH-ACCESSOIRE]
Style: bold thick black outlines, bright saturated colors, chibi proportions,
clean cel-shading, mobile game aesthetic, white background.
Output: single character centered, full body visible, idle standing pose
(relaxed, facing slightly forward), minimum 512x512 pixels, PNG format.
No text, no background elements, no weapons.
```

## Geplante Assets — Phase 1 (Common-Tier)

| Datei | User | Fach | Status |
|---|---|---|---|
| `robert-englisch/common-idle.png` | Robert | Englisch | generieren heute |
| `robert-italienisch/common-idle.png` | Robert | Italienisch | generieren heute |
| `friedrich-englisch/common-idle.png` | Friedrich | Englisch | pending |
| `friedrich-musik/common-idle.png` | Friedrich | Musik | pending |
| `friedrich-mathematik/common-idle.png` | Friedrich | Mathematik | pending |
| `jenni-???/common-idle.png` | Jenni | TBD | pending (4.1b) |
