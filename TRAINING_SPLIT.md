# Training split for the change model

Committed on 2026-11-13, **before any model was fitted** (decision 5 of the task). Nothing in this file may change after the first fit, except to record a deviation, under §8, with its date and reason.

The decision on the exclusion rule is Tiago's (2026-11-13). D4 (DESIGN §7) applies as approved, except that the families of blindrec's confounders and null controls are no longer excluded. Those languages are never reconstructed or scored, only rejected at stage 1. The numbers behind the decision are in [docs/v2/DATA_SURVEY.md](docs/v2/DATA_SURVEY.md).

## 1. Excluded, in every form, from fitting and from calibration

| excluded | reason |
|---|---|
| **Indo-European**, all of it | Germanic (Kroonen), Romance (NorthEuraLex daughters, Latin, IE-CoR Romance), Gothic, the PIE/Hittite laryngeal material, and the Sanskrit/Greek/Latin material of blindrec's `historia` are scored or used. Sister branches share handbooks and proto-forms (PIE) with them. |
| **Sino-Tibetan** | Burmish, Karen, Bai, Lalo and Bizic are scored. |
| **Austronesian** | Polynesian (ABVD, Walworth) is scored, and ABVD spans the family. |
| **Atlantic-Congo** | Bantu is scored. |
| **Tucanoan** | Tukanoan is scored. |
| **Arawakan** | `chaconbaniwa` is in the Tukanoan track. |
| **Mixe-Zoque** | scored |
| **Nuclear Trans New Guinea** | Finisterre-Huon is scored. |
| **every simulated family** | blindrec's simulators produce them. |
| **cross-family "descendants"** | Wiktionary lists loans as descendants (for example Proto-Germanic forms under Proto-Finnic, and Proto-Mongolic under Proto-Turkic). A pair is used only if its source and target belong to the same family. |

**Not excluded, by Tiago's decision:** Uralic, Japonic, Basque, Albanian, Eskimo-Aleut and Dravidian. These are the families of blindrec's confounders and null controls (Finnish, Hungarian, Basque, Albanian, Japanese, Aleut, Malayalam). Of them, only Uralic and Japonic have usable data here.

## 2. Training families

| family | source | proto-languages | role |
|---|---|---|---|
| Uto-Aztecan | Lexibank `lionnetyotonahua` v1.0, `pharaocoracholaztecan` v1.1.1, `davletshinaztecan` v1.1 | Proto-Sonoran, Proto-Tepiman; Proto-Nahua, Proto-Corachol-Nahua, Proto-Uto-Aztecan, Proto-Southern-Uto-Aztecan; Proto-Aztecan | fit |
| Uralic | Wiktionary via kaikki: Proto-Uralic, -Finnic, -Sami, -Permic, -Samoyedic | proto→proto pairs | fit |
| Japonic | Wiktionary via kaikki: Proto-Japonic, -Ryukyuan | proto→proto pairs | fit |
| Turkic | Wiktionary via kaikki: Proto-Turkic | proto→proto pairs | fit |
| Austroasiatic (Vietic) | Lexibank `sidwellvietic` v1.1 | Proto-Vietic | **calibration, held out** |
| Bora–Muinane | Lexibank `seifartecheverriboran` v1.0 | Proto-Bora-Muinane | **calibration, held out** |

**The calibration draw.** The held-out families were drawn by family, before any data was processed beyond counting entries. Two of the six names, sorted, were drawn with `random.Random(20261113).sample(sorted(families), 2)`. The draw gave Austroasiatic and Bora–Muinane. No model sees them in fitting or in hyperparameter selection. A secondary within-family split, holding out 30% of cognate sets with seed 20261114, is reported alongside but is not the primary calibration result.

## 3. What is extracted

- **Lexibank.** For every cognate set that contains a proto-form, the pair (proto-form, daughter form) is taken for each daughter of that proto-language's subgroup in the dataset. Both sides are taken from the CLDF `Segments`.
  - Cognacy comes from `cognates.csv`. In `seifartecheverriboran`, which has no such file, it comes from `forms.csv`'s `Cognacy`/`ProtoSet`.
  - Each pair is aligned with a merkmal-dissimilarity aligner (DESIGN §6.6, point 3). Pairs whose alignment is ambiguous, meaning two best alignments of equal score that disagree, are dropped and counted.
- **Wiktionary, version 1.** Only pairs of a proto-form and its immediate descendant that is also a reconstruction (a starred form) in the same family are used. Pairs with attested (orthographic) descendants are not used: turning them into IPA needs a conversion table per language, with its own error rate.
  - Reconstruction notation (Uralic phonetic alphabet conventions, Turkological and Japonic conventions) is converted to IPA with a table per family. The table is written before fitting and committed with the extraction code.
  - A form that the table cannot convert is dropped and counted, not guessed.
- **Every opportunity counts.** Each proto-segment occurrence is an opportunity, whether or not it changed (DESIGN §6.3).

## 4. Catalogues (the prior)

| catalogue | identity | handling |
|---|---|---|
| alteruphono `resources/sound_changes.tsv` | sha256 `eb3fe6a4faf66558b13ecb30fc8357892f3c5dfd8d316f102b34d30d6d7838a1` | committed here |
| Index Diachronica v10.2 (`index-diachronica.tex?as=text`, fetched 2026-11-13) | sha256 `615ff2a200ce2c521f5c56d7a9e295137e6561fa062f772f7aede4d1fb98337d` | CC BY-NC-SA; fetched, never committed (D6). Packs derived from it are generated locally. |

**Leave-out.** Index Diachronica sections for every family in §1 are removed from the prior, starting from blindrec's `LEAVE_OUT` filters (`recon.py:1463`) and extended to §1's families. The exact section list is committed with the extraction code, before fitting.

For the simulated stage-5 test (D5), the catalogues are additionally split in two halves. That split is defined in blindrec's PREREG entry, not here.

## 5. Circularity

Every proto-form used here was made with the comparative method, so the model partly learns the reconstructors' beliefs about natural directions (DESIGN §6.6, point 1). No training family has a documented ancestor. The documented-ancestor calibration subset of DESIGN §6.6 is therefore empty, and that is reported, not hidden.

The Wiktionary pairs are reconstruction-to-reconstruction (for example Proto-Uralic to Proto-Finnic), so both sides carry the circularity.

## 6. Files

`data/` is git-ignored. Every file used, with its sha256 at the time of fetching (2026-11-13T16:48Z), is listed here. Lexibank datasets are pinned to release tags, at these commits:
- `lionnetyotonahua` v1.0 = `e9f01cb9442a282752ea85f8ca8c12224d859f95`
- `pharaocoracholaztecan` v1.1.1 = `c49bdff04c2bd64763e74374b72fc8263305c8e3`
- `davletshinaztecan` v1.1 = `313ca210e17dd35b1a72a22be5e47ce1efe70324`
- `seifartecheverriboran` v1.0 = `5fd1af9a1e4ee5f69076a7db4d6333231b7a5393`
- `sidwellvietic` v1.1 = `43be06aa3ef0aab101c5628625440a35a95cd588`

kaikki files are not versioned upstream: their checksums are the only identity, and a refetch that differs is a deviation.

| file | sha256 |
|---|---|
| `lexibank/davletshinaztecan/cldf/forms.csv` | `af5f1da6bd964d430e2c51100f8a92f851588421976e9d8f33de3efaf35bbfc8` |
| `lexibank/lionnetyotonahua/cldf/forms.csv` | `d64d268521c1ae08a215d6d1a7f6ce13769f110d25834ea4b144f591a738818d` |
| `lexibank/pharaocoracholaztecan/cldf/forms.csv` | `939ad69acf7735f36a285cbe3cbe887d0b92b43bddc683c3b3f829efc302c36c` |
| `lexibank/seifartecheverriboran/cldf/forms.csv` | `922018876c86126c85d8119295f5a6182bedfc537dd25bdaf52d19f6633d2c63` |
| `lexibank/sidwellvietic/cldf/forms.csv` | `8a8c04c51f82c6d14adc0727ae94360bb3ec82c8af5cb1ec6d11514e18566495` |
| `lexibank/davletshinaztecan/cldf/cognates.csv` | `8e079d62d86bea783c669ea28323b1ad68b16ac387f3a64f7006a291a3036d14` |
| `lexibank/lionnetyotonahua/cldf/cognates.csv` | `82d562af0e66a2a9ff76a8f8c507ce46617aff0983e283bb85c76b3725e82905` |
| `lexibank/pharaocoracholaztecan/cldf/cognates.csv` | `254bcb6ed312a233389f65faeca48fa512fdd59f66e23ed3e6d85420d1293ff8` |
| `lexibank/sidwellvietic/cldf/cognates.csv` | `7590e5424e226b1252d99c451e0949f197096c891e31e8dfde26c81425f33749` |
| `lexibank/davletshinaztecan/cldf/languages.csv` | `24398db8da12aeca288c87973c08024ba7c243ada0cd5235e91235119ab84659` |
| `lexibank/lionnetyotonahua/cldf/languages.csv` | `c72ce40df8d638911960e7fac75e78957cb9cde96caf3d124f20b85cc414c836` |
| `lexibank/pharaocoracholaztecan/cldf/languages.csv` | `1fa040e62a981ed8d68e769818b1dcb53e51383d62871a9942df63378fb8de59` |
| `lexibank/seifartecheverriboran/cldf/languages.csv` | `b7b5299109736c70f8a4a1e9d09b448cb8fe7183f02a63e4e385c86e6621b0b3` |
| `lexibank/sidwellvietic/cldf/languages.csv` | `931809c54a72667e0193ab2c95d46635607504885929dd9bf51340c231ea6602` |
| `kaikki/ProtoFinnic.jsonl` | `82b4476815f9f7746d1141c1c5043953f4b252f945ac381f0d15e117bf6d203a` |
| `kaikki/ProtoJaponic.jsonl` | `4c110f65f12ae7075ffd472fabaa78878c43db227695681d403f6caeafd9cb39` |
| `kaikki/ProtoPermic.jsonl` | `6eac2ffa86eb30a9f0bfbc833836654235aa03aba45c48b3a244d649ac3353d5` |
| `kaikki/ProtoRyukyuan.jsonl` | `3de82e19872fcce22e9db124014b01a0468899293dc6eadd4ad96eb9e451de4b` |
| `kaikki/ProtoSami.jsonl` | `9c4ea7bec6f8ff88ac2da4d4c98f60c8299283e5ccbcb31d67c318f984ce3ce0` |
| `kaikki/ProtoSamoyedic.jsonl` | `35abc324308ad556a60a7f726a30d5c2a763fe5c604bb4c6d815f2e4acb771f6` |
| `kaikki/ProtoTurkic.jsonl` | `a026d4695e96a4ec48af81a344a6bcb38acbe863039ab8e9ccb88b89bb7ee198` |
| `kaikki/ProtoUralic.jsonl` | `839a990d531c524b9349bcb15481161e4e10714c9df9c508385a708bc2194158` |

## 7. Leakage checks to run before the first fit

1. No language in the extracted pairs has a Glottolog top-level family in §1. This is checked by Glottocode where the source gives one, and by language name for Wiktionary.
2. No form in the held-out families' pairs appears in the fitting pairs.
3. The catalogue after leave-out contains no section named for a family in §1.

## 8. Deviations

1. **2026-11-13: the extraction rules were committed with the first fit, not before it.** The first fit was M3's two baseline scalars (P(stay) and the distance temperature) on Uto-Aztecan. The rules are in `alteruphono/model/extract.py`'s docstring:
   - nearest-proto-ancestor pairing by Glottolog classification;
   - a doculect with no Glottocode as its dataset's root;
   - segment cleaning;
   - alignment with gap cost 0.55.

   They were written before that fit and not changed after it, but they reached the repository in the same commit. Glottolog CLDF v5.2 is pinned:
   - `languages.csv` sha256 `c3007b0650e3fdb792d2f0ac5c3ac6f5e8d807a3608096f07ae34cfb0c4c9664`;
   - `values.csv` sha256 `a7fbfbada2dfc53bec34e4250300d9d4eac4b5836f0871e9213f6bec4445a964`.
2. **2026-11-13: the Index Diachronica leave-out is by top-level `\section`**, which is cleaner than blindrec's keyword list. The removed sections are Indo-European, Austronesian, Niger-Congo, Sino-Tibetan, Trans-New Guinea, Macro-Arawakan, Totozoquean (it contains Mixe-Zoque), and two sections without family provenance: "Vowel Shifts" and "Most-Wanted Sound Changes". Each evaluated family's own section is removed as well. alteruphono's own `sound_changes.tsv` has no family labels and is used whole; it may contain changes from excluded families.
3. **2026-11-13, before any fit on a Wiktionary family: the notation tables were extended once, after counting conversion failures.** The tables are in `alteruphono/model/wiktionary.py`.
   - **What was added:** Uralic å, ɜ, breve vowels, ľ, and u̇/ȯ; Turkic ŕ, ĺ and ń.
   - **Why it matters:** the failure counts were looked at, but nothing about the pairs' changes was.
   - **A filter error, fixed at the same time:** the family filter wrongly dropped Proto-Selkup, -Mari, -Khanty and -Mansi.

   Result: Uralic 2,613 aligned pairs (11,286 opportunities; 129 forms unconvertible), Turkic 424 (1,647; 93), Japonic 423 (1,727; 23).
4. **2026-11-13: the σ grid of `alteruphono/model/fit.py` was extended** from (0.1, 0.3, 1, 3) to include 0.01 and 0.03, because 0.1, the edge, won. This was decided on the fitting families' leave-one-family-out loss only, before the held-out families were scored.
