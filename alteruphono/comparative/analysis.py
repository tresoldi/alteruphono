"""Comparative analysis — correspondences, distance, phylogeny."""

from __future__ import annotations

from dataclasses import dataclass, field

from alteruphono.features import get_system


@dataclass
class CorrespondenceSet:
    """A systematic sound correspondence across languages."""

    position: int
    sounds: dict[str, str]  # language -> sound at this position

    @property
    def languages(self) -> list[str]:
        return sorted(self.sounds.keys())


def needleman_wunsch(
    seq_a: list[str],
    seq_b: list[str],
    gap_open: float = -2.0,
    gap_extend: float = -0.5,
    system_name: str | None = None,
) -> tuple[list[str | None], list[str | None], float]:
    """Global alignment of two sound sequences using Needleman-Wunsch.

    Supports affine gap penalties (gap_open + gap_extend) for more realistic
    alignments.

    Returns (aligned_a, aligned_b, score) where None represents a gap.
    """
    m, n = len(seq_a), len(seq_b)
    cost_fn = _feature_weighted_cost if system_name else _simple_cost

    # Affine gap penalty: 3 DP matrices
    # M[i][j] = best score ending with match/mismatch
    # X[i][j] = best score ending with gap in seq_b (deletion from a)
    # Y[i][j] = best score ending with gap in seq_a (insertion from b)
    neg_inf = float("-inf")

    dp_m: list[list[float]] = [[neg_inf] * (n + 1) for _ in range(m + 1)]
    dp_x: list[list[float]] = [[neg_inf] * (n + 1) for _ in range(m + 1)]
    dp_y: list[list[float]] = [[neg_inf] * (n + 1) for _ in range(m + 1)]

    dp_m[0][0] = 0.0
    for i in range(1, m + 1):
        dp_x[i][0] = gap_open + gap_extend * (i - 1)
    for j in range(1, n + 1):
        dp_y[0][j] = gap_open + gap_extend * (j - 1)

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            match_score = cost_fn(seq_a[i - 1], seq_b[j - 1], system_name)

            dp_m[i][j] = (
                max(
                    dp_m[i - 1][j - 1],
                    dp_x[i - 1][j - 1],
                    dp_y[i - 1][j - 1],
                )
                + match_score
            )

            dp_x[i][j] = max(
                dp_m[i - 1][j] + gap_open,
                dp_x[i - 1][j] + gap_extend,
            )

            dp_y[i][j] = max(
                dp_m[i][j - 1] + gap_open,
                dp_y[i][j - 1] + gap_extend,
            )

    # Best score at (m, n)
    final_score = max(dp_m[m][n], dp_x[m][n], dp_y[m][n])

    # Traceback
    aligned_a: list[str | None] = []
    aligned_b: list[str | None] = []
    i, j = m, n

    # Determine which matrix we're in
    if dp_m[m][n] >= dp_x[m][n] and dp_m[m][n] >= dp_y[m][n]:
        state = "M"
    elif dp_x[m][n] >= dp_y[m][n]:
        state = "X"
    else:
        state = "Y"

    while i > 0 or j > 0:
        if state == "M" and i > 0 and j > 0:
            aligned_a.append(seq_a[i - 1])
            aligned_b.append(seq_b[j - 1])
            score_here = dp_m[i][j]
            match_score = cost_fn(seq_a[i - 1], seq_b[j - 1], system_name)
            prev = score_here - match_score
            i -= 1
            j -= 1
            # Determine previous state
            if abs(prev - dp_m[i][j]) < 1e-9:
                state = "M"
            elif abs(prev - dp_x[i][j]) < 1e-9:
                state = "X"
            else:
                state = "Y"
        elif state == "X" and i > 0:
            aligned_a.append(seq_a[i - 1])
            aligned_b.append(None)
            score_here = dp_x[i][j]
            i -= 1
            state = "X" if abs(score_here - (dp_x[i][j] + gap_extend)) < 1e-9 else "M"
        elif j > 0:
            aligned_a.append(None)
            aligned_b.append(seq_b[j - 1])
            score_here = dp_y[i][j]
            j -= 1
            state = "Y" if abs(score_here - (dp_y[i][j] + gap_extend)) < 1e-9 else "M"
        else:
            break

    aligned_a.reverse()
    aligned_b.reverse()
    return aligned_a, aligned_b, final_score


def _simple_cost(a: str, b: str, _system_name: str | None = None) -> float:
    """Simple cost: +1 for match, -1 for mismatch."""
    return 1.0 if a == b else -1.0


def _feature_weighted_cost(a: str, b: str, system_name: str | None = None) -> float:
    """Feature-weighted cost using the feature system's sound_distance."""
    if a == b:
        return 1.0

    sys = get_system(system_name)
    feats_a = sys.grapheme_to_features(a)
    feats_b = sys.grapheme_to_features(b)

    if feats_a is None or feats_b is None:
        return -1.0

    # V-C mismatch penalty: vowel vs consonant is a larger penalty
    a_is_vowel = "vowel" in feats_a
    b_is_vowel = "vowel" in feats_b
    if a_is_vowel != b_is_vowel:
        return -2.0

    dist = sys.sound_distance(feats_a, feats_b)
    # Convert distance [0, 1] to score [-1, 1]: score = 1 - 2*dist
    return 1.0 - 2.0 * dist


def multi_align(
    forms: dict[str, list[str]],
    system_name: str | None = None,
) -> dict[str, list[str | None]]:
    """Progressive multi-alignment: align pairs in order, build consensus.

    Returns dict with same keys, values are aligned sequences (with None gaps).
    """
    langs = sorted(forms.keys())
    if len(langs) == 0:
        return {}
    if len(langs) == 1:
        return {langs[0]: list(forms[langs[0]])}

    # Start with first two languages
    a_aligned, b_aligned, _ = needleman_wunsch(
        forms[langs[0]], forms[langs[1]], system_name=system_name
    )
    result: dict[str, list[str | None]] = {
        langs[0]: a_aligned,
        langs[1]: b_aligned,
    }

    # Progressively add remaining languages
    for k in range(2, len(langs)):
        # Use consensus of current alignment as reference
        ref_len = len(a_aligned)
        consensus: list[str] = []
        for pos in range(ref_len):
            # Take most common non-None sound at this position
            sounds_at_pos: list[str] = []
            for aligned in result.values():
                val = aligned[pos] if pos < len(aligned) else None
                if val is not None:
                    sounds_at_pos.append(val)
            if sounds_at_pos:
                best = max(set(sounds_at_pos), key=sounds_at_pos.count)
                consensus.append(best)

        new_aligned_ref, new_aligned_k, _ = needleman_wunsch(
            consensus, forms[langs[k]], system_name=system_name
        )

        # Re-align existing sequences to match the new reference alignment
        new_result: dict[str, list[str | None]] = {}
        ref_idx = 0
        for pos in range(len(new_aligned_ref)):
            if new_aligned_ref[pos] is not None:
                for lang, aligned in result.items():
                    if lang not in new_result:
                        new_result[lang] = []
                    if ref_idx < len(aligned):
                        new_result[lang].append(aligned[ref_idx])
                    else:
                        new_result[lang].append(None)
                ref_idx += 1
            else:
                for lang in result:
                    if lang not in new_result:
                        new_result[lang] = []
                    new_result[lang].append(None)

        new_result[langs[k]] = new_aligned_k
        result = new_result
        a_aligned = new_aligned_ref

    return result


@dataclass
class ComparativeAnalysis:
    """Comparative analysis of cognate sets across languages.

    Pure Python — no pandas/numpy dependencies.
    """

    cognates: list[dict[str, list[str]]] = field(default_factory=list)
    system_name: str | None = None

    def add_cognate_set(self, forms: dict[str, list[str]]) -> None:
        """Add a cognate set: {language: [sound, sound, ...]}."""
        self.cognates.append(forms)

    def find_correspondences(self) -> list[CorrespondenceSet]:
        """Find systematic sound correspondences using NW alignment."""
        correspondences: list[CorrespondenceSet] = []

        for cognate_set in self.cognates:
            langs = sorted(cognate_set.keys())
            if len(langs) < 2:
                continue

            aligned = multi_align(cognate_set, self.system_name)
            if not aligned:
                continue

            # All aligned sequences should have same length
            align_len = max(len(v) for v in aligned.values())

            for pos in range(align_len):
                sounds: dict[str, str] = {}
                for lang in langs:
                    if lang in aligned and pos < len(aligned[lang]):
                        val = aligned[lang][pos]
                        if val is not None:
                            sounds[lang] = val

                if len(sounds) >= 2:
                    correspondences.append(CorrespondenceSet(position=pos, sounds=sounds))

        return correspondences

    def calculate_distance_matrix(self) -> tuple[list[str], list[list[float]]]:
        """Calculate pairwise phonological distance using NW alignment.

        Returns (language_names, distance_matrix) where distance_matrix[i][j]
        is the distance between languages i and j.
        """
        if not self.cognates:
            return [], []

        all_langs: set[str] = set()
        for cset in self.cognates:
            all_langs.update(cset.keys())
        langs = sorted(all_langs)
        n = len(langs)

        matrix: list[list[float]] = [[0.0] * n for _ in range(n)]

        for cset in self.cognates:
            for i, lang_a in enumerate(langs):
                for j, lang_b in enumerate(langs):
                    if i >= j:
                        continue
                    if lang_a not in cset or lang_b not in cset:
                        continue

                    form_a = cset[lang_a]
                    form_b = cset[lang_b]

                    dist = _nw_distance(form_a, form_b, self.system_name)
                    matrix[i][j] += dist
                    matrix[j][i] += dist

        n_sets = len(self.cognates) or 1
        for i in range(n):
            for j in range(n):
                matrix[i][j] /= n_sets

        return langs, matrix

    def build_phylogeny(self, method: str = "nj") -> list[tuple[str, str, float]]:
        """Build a phylogeny from the distance matrix.

        Args:
            method: "nj" for neighbor-joining (default), "upgma" for UPGMA.

        Returns list of (node_a, node_b, distance) edges.
        """
        langs, matrix = self.calculate_distance_matrix()
        if len(langs) < 2:
            return []

        if method == "nj":
            return _neighbor_joining(langs, matrix)
        return _upgma(langs, matrix)


def _upgma(langs: list[str], matrix: list[list[float]]) -> list[tuple[str, str, float]]:
    """UPGMA clustering (assumes molecular clock)."""
    remaining = list(range(len(langs)))
    labels = list(langs)
    edges: list[tuple[str, str, float]] = []

    while len(remaining) > 1:
        min_dist = float("inf")
        min_i, min_j = 0, 1
        for i_idx in range(len(remaining)):
            for j_idx in range(i_idx + 1, len(remaining)):
                ii = remaining[i_idx]
                jj = remaining[j_idx]
                if matrix[ii][jj] < min_dist:
                    min_dist = matrix[ii][jj]
                    min_i, min_j = i_idx, j_idx

        ii = remaining[min_i]
        jj = remaining[min_j]
        edges.append((labels[ii], labels[jj], min_dist))

        new_label = f"({labels[ii]},{labels[jj]})"
        labels[ii] = new_label

        for k_idx in range(len(remaining)):
            kk = remaining[k_idx]
            if kk != ii and kk != jj:
                avg = (matrix[ii][kk] + matrix[jj][kk]) / 2
                matrix[ii][kk] = avg
                matrix[kk][ii] = avg

        remaining.pop(min_j)

    return edges


def _neighbor_joining(langs: list[str], matrix: list[list[float]]) -> list[tuple[str, str, float]]:
    """Neighbor-joining algorithm (no molecular clock assumption).

    Computes Q-matrix to find optimal pair to join at each step.
    """
    n = len(langs)
    if n < 2:
        return []

    # Work with mutable copies
    dist: dict[tuple[int, int], float] = {}
    for i in range(n):
        for j in range(n):
            dist[(i, j)] = matrix[i][j]

    active: list[int] = list(range(n))
    labels: dict[int, str] = {i: langs[i] for i in range(n)}
    edges: list[tuple[str, str, float]] = []
    next_id = n

    while len(active) > 2:
        r = len(active)

        # Compute row sums
        row_sum: dict[int, float] = {}
        for i in active:
            s = 0.0
            for j in active:
                if i != j:
                    s += dist.get((i, j), 0.0)
            row_sum[i] = s

        # Compute Q-matrix and find minimum
        min_q = float("inf")
        min_pair = (active[0], active[1])
        for idx_i in range(len(active)):
            for idx_j in range(idx_i + 1, len(active)):
                i = active[idx_i]
                j = active[idx_j]
                q = (r - 2) * dist.get((i, j), 0.0) - row_sum[i] - row_sum[j]
                if q < min_q:
                    min_q = q
                    min_pair = (i, j)

        f, g = min_pair
        d_fg = dist.get((f, g), 0.0)

        # Branch lengths
        delta = (row_sum[f] - row_sum[g]) / (r - 2) if r > 2 else 0.0
        branch_f = (d_fg + delta) / 2
        branch_g = (d_fg - delta) / 2

        # Ensure non-negative
        branch_f = max(branch_f, 0.0)
        branch_g = max(branch_g, 0.0)

        # Create new node
        new_node = next_id
        next_id += 1
        new_label = f"({labels[f]},{labels[g]})"
        labels[new_node] = new_label

        edges.append((labels[f], labels[g], d_fg))

        # Compute distances from new node to all other active nodes
        for k in active:
            if k != f and k != g:
                d_new = (dist.get((f, k), 0.0) + dist.get((g, k), 0.0) - d_fg) / 2
                dist[(new_node, k)] = d_new
                dist[(k, new_node)] = d_new

        dist[(new_node, new_node)] = 0.0

        # Update active list
        active = [k for k in active if k != f and k != g]
        active.append(new_node)

    # Last two nodes
    if len(active) == 2:
        i, j = active
        edges.append((labels[i], labels[j], dist.get((i, j), 0.0)))

    return edges


def _nw_distance(a: list[str], b: list[str], system_name: str | None = None) -> float:
    """Compute NW-based distance between two sound lists."""
    if not a and not b:
        return 0.0
    if not a or not b:
        return 1.0

    _, _, score = needleman_wunsch(a, b, system_name=system_name)
    max_len = max(len(a), len(b))
    # Normalize score to [0, 1] distance
    # Best possible score = max_len (all match at 1.0)
    # Worst possible score = -max_len
    return 1.0 - (score + max_len) / (2 * max_len)
