"""Proto-form reconstruction methods."""

from __future__ import annotations

from collections import Counter

from alteruphono.comparative.analysis import multi_align
from alteruphono.features import get_system


def reconstruct_proto(
    forms: dict[str, list[str]],
    method: str = "majority",
    phylogeny: list[tuple[str, str, float]] | None = None,
    system_name: str | None = None,
) -> list[str]:
    """Reconstruct a proto-form from cognate set.

    Args:
        forms: {language: [sound, sound, ...]} cognate set
        method: "majority" (most common sound), "conservative" (prefer sounds
                found in more branches), "parsimony" (Fitch algorithm),
                or "sankoff" (weighted parsimony with cost matrix)
        phylogeny: list of (parent, child, weight) edges for tree-based methods
        system_name: feature system for weighted alignment

    Returns:
        Reconstructed proto-form as list of sounds.
    """
    if not forms:
        return []

    if method == "majority":
        return _majority_reconstruction(forms, system_name)
    if method == "conservative":
        return _conservative_reconstruction(forms, phylogeny, system_name)
    if method == "parsimony":
        return _parsimony_reconstruction(forms, phylogeny, system_name)
    if method == "sankoff":
        return _sankoff_reconstruction(forms, phylogeny, system_name)

    msg = f"Unknown reconstruction method: {method!r}"
    raise ValueError(msg)


def _majority_reconstruction(
    forms: dict[str, list[str]],
    system_name: str | None = None,
) -> list[str]:
    """Reconstruct by taking the most common sound at each position."""
    aligned = multi_align(forms, system_name)
    max_len = max(len(v) for v in aligned.values()) if aligned else 0
    result: list[str] = []

    for pos in range(max_len):
        counter: Counter[str] = Counter()
        for form in aligned.values():
            val = form[pos] if pos < len(form) else None
            if val is not None:
                counter[val] += 1

        if counter:
            result.append(counter.most_common(1)[0][0])

    return result


def _compute_branch_weights(
    phylogeny: list[tuple[str, str, float]],
    languages: set[str],
) -> dict[str, float]:
    """Compute branch weights via BFS tree traversal.

    Builds adjacency from phylogeny edges, finds root, assigns depth-based
    weights. Languages at deeper (more independent) branches get higher weight.
    """
    if not phylogeny:
        return {lang: 1.0 for lang in languages}

    # Build adjacency list
    children: dict[str, list[tuple[str, float]]] = {}
    all_parents: set[str] = set()
    all_children: set[str] = set()

    for parent, child, weight in phylogeny:
        children.setdefault(parent, []).append((child, weight))
        all_parents.add(parent)
        all_children.add(child)

    # Find root: appears as parent but never as child
    roots = all_parents - all_children
    root = phylogeny[0][0] if not roots else sorted(roots)[0]

    # BFS to assign depth-based weights
    weights: dict[str, float] = {}
    queue: list[tuple[str, int]] = [(root, 0)]
    visited: set[str] = set()

    while queue:
        node, depth = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)

        if node in languages:
            # Weight = 1 + depth (deeper = more independent)
            weights[node] = 1.0 + depth * 0.5

        for child, _ in children.get(node, []):
            queue.append((child, depth + 1))

    # Assign default weight to languages not found in tree
    for lang in languages:
        if lang not in weights:
            weights[lang] = 1.0

    return weights


def _conservative_reconstruction(
    forms: dict[str, list[str]],
    phylogeny: list[tuple[str, str, float]] | None = None,
    system_name: str | None = None,
) -> list[str]:
    """Reconstruct by preferring sounds present in more independent branches.

    Uses feature markedness as tiebreaker (simpler sounds preferred).
    Falls back to majority when no phylogeny provided.
    """
    aligned = multi_align(forms, system_name)
    max_len = max(len(v) for v in aligned.values()) if aligned else 0

    branch_weights = _compute_branch_weights(phylogeny or [], set(forms.keys()))

    result: list[str] = []
    sys = get_system(system_name) if system_name else None

    for pos in range(max_len):
        weighted_counts: dict[str, float] = {}
        for lang, form in aligned.items():
            val = form[pos] if pos < len(form) else None
            if val is not None:
                weight = branch_weights.get(lang, 1.0)
                weighted_counts[val] = weighted_counts.get(val, 0.0) + weight

        if not weighted_counts:
            continue

        # Get candidates with highest weight
        max_weight = max(weighted_counts.values())
        candidates = [s for s, w in weighted_counts.items() if w == max_weight]

        if len(candidates) == 1 or sys is None:
            result.append(candidates[0])
        else:
            # Tiebreaker: prefer less marked (simpler) sounds
            best = candidates[0]
            best_features = sys.grapheme_to_features(best)
            best_count = len(best_features) if best_features else 999

            for cand in candidates[1:]:
                feats = sys.grapheme_to_features(cand)
                count = len(feats) if feats else 999
                if count < best_count:
                    best = cand
                    best_count = count

            result.append(best)

    return result


def _parsimony_reconstruction(
    forms: dict[str, list[str]],
    phylogeny: list[tuple[str, str, float]] | None = None,
    system_name: str | None = None,
) -> list[str]:
    """Reconstruct using Fitch parsimony algorithm.

    Bottom-up: intersect child sets (union on conflict, +1 cost).
    Top-down: select from set.

    Falls back to majority when no phylogeny provided.
    """
    if not phylogeny:
        return _majority_reconstruction(forms, system_name)

    # Build tree structure
    tree = _build_phylo_tree(phylogeny, set(forms.keys()))
    aligned = multi_align(forms, system_name)
    max_len = max(len(v) for v in aligned.values()) if aligned else 0

    result: list[str] = []
    for pos in range(max_len):
        # Get tip values at this position
        tip_values: dict[str, set[str]] = {}
        for lang, form in aligned.items():
            val = form[pos] if pos < len(form) else None
            if val is not None:
                tip_values[lang] = {val}

        if not tip_values:
            continue

        proto_sound = _fitch_one_position(tip_values, tree)
        result.append(proto_sound)

    return result


def _sankoff_reconstruction(
    forms: dict[str, list[str]],
    phylogeny: list[tuple[str, str, float]] | None = None,
    system_name: str | None = None,
) -> list[str]:
    """Reconstruct using Sankoff weighted parsimony algorithm.

    Uses feature-based cost matrix for non-uniform transition costs.
    Falls back to majority when no phylogeny provided.
    """
    if not phylogeny:
        return _majority_reconstruction(forms, system_name)

    tree = _build_phylo_tree(phylogeny, set(forms.keys()))
    aligned = multi_align(forms, system_name)
    max_len = max(len(v) for v in aligned.values()) if aligned else 0

    result: list[str] = []
    for pos in range(max_len):
        tip_values: dict[str, set[str]] = {}
        for lang, form in aligned.items():
            val = form[pos] if pos < len(form) else None
            if val is not None:
                tip_values[lang] = {val}

        if not tip_values:
            continue

        proto_sound = _sankoff_one_position(tip_values, tree, system_name)
        result.append(proto_sound)

    return result


def _build_phylo_tree(
    edges: list[tuple[str, str, float]],
    tip_names: set[str],
) -> dict[str, list[str]]:
    """Build a tree from phylogeny edges.

    Returns adjacency list: node -> [child1, child2, ...].
    """
    children: dict[str, list[str]] = {}
    all_parents: set[str] = set()
    all_children: set[str] = set()

    for parent, child, _ in edges:
        children.setdefault(parent, []).append(child)
        all_parents.add(parent)
        all_children.add(child)

    # If tree is empty or too simple, create a star tree
    if not children:
        root = "root"
        children[root] = list(tip_names)
        return children

    return children


def _find_root(tree: dict[str, list[str]]) -> str | None:
    """Find root node: appears as parent but never as child."""
    all_children_set: set[str] = set()
    for kids in tree.values():
        all_children_set.update(kids)
    roots = [n for n in tree if n not in all_children_set]
    return roots[0] if roots else None


def _fitch_one_position(
    tip_values: dict[str, set[str]],
    tree: dict[str, list[str]],
) -> str:
    """Run Fitch parsimony for one alignment position."""
    root = _find_root(tree)

    if root is None:
        all_sounds: list[str] = []
        for vals in tip_values.values():
            all_sounds.extend(vals)
        if all_sounds:
            return Counter(all_sounds).most_common(1)[0][0]
        return ""

    # Bottom-up pass
    node_sets: dict[str, set[str]] = {}

    def bottom_up(node: str) -> set[str]:
        if node in tip_values:
            node_sets[node] = set(tip_values[node])
            return node_sets[node]

        if node not in tree:
            node_sets[node] = set()
            return set()

        child_sets = [bottom_up(c) for c in tree[node]]
        non_empty = [s for s in child_sets if s]

        if not non_empty:
            node_sets[node] = set()
            return set()

        result = set(non_empty[0])
        for cs in non_empty[1:]:
            intersection = result & cs
            result = intersection or result | cs

        node_sets[node] = result
        return result

    bottom_up(root)

    root_set = node_sets.get(root, set())
    if root_set:
        all_tip_sounds: list[str] = []
        for vals in tip_values.values():
            all_tip_sounds.extend(vals)
        counter = Counter(all_tip_sounds)
        return max(root_set, key=lambda s: counter.get(s, 0))

    all_sounds_fallback: list[str] = []
    for vals in tip_values.values():
        all_sounds_fallback.extend(vals)
    if all_sounds_fallback:
        return Counter(all_sounds_fallback).most_common(1)[0][0]
    return ""


def _sankoff_one_position(
    tip_values: dict[str, set[str]],
    tree: dict[str, list[str]],
    system_name: str | None = None,
) -> str:
    """Run Sankoff weighted parsimony for one alignment position.

    Uses feature-based cost matrix for non-uniform substitution costs.
    """
    # Collect all states
    all_states: set[str] = set()
    for vals in tip_values.values():
        all_states.update(vals)

    if len(all_states) <= 1:
        return next(iter(all_states)) if all_states else ""

    states = sorted(all_states)

    # Build cost matrix from feature distances
    sys = get_system(system_name) if system_name else None
    cost_matrix: dict[tuple[str, str], float] = {}
    for a in states:
        for b in states:
            if a == b:
                cost_matrix[(a, b)] = 0.0
            elif sys:
                feats_a = sys.grapheme_to_features(a)
                feats_b = sys.grapheme_to_features(b)
                if feats_a and feats_b:
                    cost_matrix[(a, b)] = sys.sound_distance(feats_a, feats_b)
                else:
                    cost_matrix[(a, b)] = 1.0
            else:
                cost_matrix[(a, b)] = 1.0

    root = _find_root(tree)
    if root is None:
        all_sounds: list[str] = []
        for vals in tip_values.values():
            all_sounds.extend(vals)
        return Counter(all_sounds).most_common(1)[0][0] if all_sounds else ""

    # Bottom-up: compute cost for each state at each node
    node_costs: dict[str, dict[str, float]] = {}

    def bottom_up(node: str) -> dict[str, float]:
        if node in tip_values:
            # Leaf: cost 0 for observed state, infinity for others
            costs = {}
            for s in states:
                costs[s] = 0.0 if s in tip_values[node] else float("inf")
            node_costs[node] = costs
            return costs

        if node not in tree:
            costs = {s: 0.0 for s in states}
            node_costs[node] = costs
            return costs

        # Internal node: sum over children
        costs = {s: 0.0 for s in states}
        for child in tree[node]:
            child_costs = bottom_up(child)
            for parent_state in states:
                # Minimum cost: child_cost[s] + transition_cost(parent_state, s)
                min_child_cost = float("inf")
                for child_state in states:
                    c = child_costs[child_state] + cost_matrix.get(
                        (parent_state, child_state), 1.0
                    )
                    if c < min_child_cost:
                        min_child_cost = c
                costs[parent_state] += min_child_cost

        node_costs[node] = costs
        return costs

    root_costs = bottom_up(root)

    # Select state with minimum cost at root
    best_state = min(states, key=lambda s: root_costs[s])
    return best_state
