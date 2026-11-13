# Data survey for the change model (M3/M4), 2026-11-13

This is a record of what proto→daughter data can be reached from this environment, and what each exclusion rule leaves. The proto-language names were checked against each dataset's `cldf/languages.csv`; I had first written two of them from memory, wrongly. **It is not the training split.** `TRAINING_SPLIT.md` will be written and committed before any fit, after Tiago decides between the options in §3. No dataset listed here has been downloaded beyond its language table, and nothing has been fitted.

## 1. Sources reachable

**Lexibank.**
- `lexibank/lexibank-analysed` `etc/lexibank.tsv` lists 134 datasets. 7 are flagged `ProtoCore` (they contain proto-forms):

| dataset | version | family (Glottolog) | proto-languages |
|---|---|---|---|
| `carvalhopurus` | v1.1 | Arawakan (Purus) | Proto-Purus |
| `luangthongkumkaren` | v1.1 | Sino-Tibetan (Karen) | Proto-Karen |
| `seifartecheverriboran` | v1.0 | Bora–Muinane | Proto-Bora-Muinane |
| `yanglalo` | v4.0 | Sino-Tibetan (Lalo) | Proto-Lalo |
| `davletshinaztecan` | v1.1 | Uto-Aztecan | Proto-Aztecan |
| `pharaocoracholaztecan` | v1.1.1 | Uto-Aztecan | Proto-Nahua, Proto-Corachol-Nahua, Proto-Uto-Aztecan, Proto-Southern-Uto-Aztecan |
| `sidwellvietic` | v1.1 | Austroasiatic (Vietic) | Proto-Vietic |

- Not flagged, but with proto-forms in `languages.csv`: `lionnetyotonahua` (Uto-Aztecan; Proto-Sonoran and Proto-Tepiman). blindrec ingested it as the "tepiman" Tier-B track and dropped it before scoring.

**Wiktionary, via kaikki.org.**
- kaikki publishes per-language files only for languages with at least 500 senses.
- The proto-languages it has are Proto-Germanic, West Germanic, Slavic, Finnic, Indo-European, Sami, Celtic, Turkic, Indo-Iranian, Malayo-Polynesian, Bantu, Italic, Samoyedic, Brythonic, Uralic, Ryukyuan, Japonic, Balto-Slavic, Permic, Iranian and Sino-Tibetan.
- Smaller proto-languages (Algonquian, Mayan, Semitic, Tai, …) exist only in the multi-language dump, which is too large for this environment's disk.
- Wiktionary gives daughter reflexes in their orthographies. Turning them into aligned IPA pairs means joining each reflex to its own entry's pronunciation and normalising the proto-notation. That is real work, with its own error rate, to be measured before use.

**Index Diachronica** (the catalogue, not data) is reachable and was fetched for the parity harness. It is CC BY-NC-SA, never committed.

## 2. The circularity, again

Every proto-form above was made with the comparative method (DESIGN §6.6). Uto-Aztecan, Bora–Muinane and Vietic come from single authors' reconstructions. Wiktionary's come from many editors citing handbooks.

None of these families has a documented ancestor, so the "documented-ancestor" calibration subset of DESIGN §6.6 would be empty under every option below except one that admits Indo-European; Latin, the obvious documented ancestor, is excluded under all of them.

## 3. What each exclusion rule leaves

| rule | excluded | families left for fitting and calibration |
|---|---|---|
| **D4 as approved: Glottolog top-level family of every evaluation family, confounder and null control** | Indo-European, Sino-Tibetan, Austronesian, Atlantic-Congo, Tucanoan, Arawakan, Mixe-Zoque, Nuclear Trans New Guinea, Uralic, Japonic, Dravidian, Basque, Albanian, Eskimo-Aleut | **Uto-Aztecan, Bora–Muinane, Austroasiatic**, plus Turkic once the Wiktionary conversion is done: **3–4 families** |
| D4 without the confounders and null controls: they are never reconstructed or scored, only rejected at stage 1 | the scored families' top-level families only | the above, plus **Uralic** (Proto-Uralic, Finnic, Sami, Permic, Samoyedic) and **Japonic** (Proto-Japonic, Ryukyuan): **5–6 families** |
| The prompt's list: the scored families, PIE/Hittite laryngeal material, simulated families | Germanic, Romance (and Latin, IE-CoR Romance), Tukanoan, Burmish, Karen, Bai, Polynesian, Lalo, Bizic, Bantu, Mixe-Zoque, Finisterre-Huon; PIE | the above, plus non-excluded branches of Indo-European (Slavic, Celtic, Indo-Iranian), and non-Polynesian Austronesian. A Wiktionary entry citing PIE or Proto-Polynesian would need filtering, and sister branches share handbooks with the excluded ones. |

**My error in DESIGN §7.** I justified excluding Uralic, Japonic and the other confounder families by saying that it "costs little". The survey shows it costs about half of the usable data: Uralic is the richest source left after Indo-European.

**DESIGN's own stop rule.** DESIGN §7 says M3 stops and reports if fewer than about 5 families qualify. Under D4 as approved, 3–4 do. So M3 stops here, for Tiago's decision.
