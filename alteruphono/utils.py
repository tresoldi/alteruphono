"""
Defines auxiliary functions, structures, and data for the library.
"""

# Python standard libraries imports
import csv
from pathlib import Path

# Import from other modules
from .parser import parse_features
from . import globals

# Set the resource directory; this is safe as we already added
# `zip_safe=False` to setup.py
RESOURCE_DIR = Path(__file__).parent.parent / "resources"


def descriptors2grapheme(descriptors):
    # make sure we can manipulate these descriptors
    descriptors = list(descriptors)

    # Run manual fixes related to pyclts
    if "palatal" in descriptors and "fricative" in descriptors:
        # Fricative palatals are described as alveolo-palatal in pyclts, so
        # replace all of them
        descriptors = [
            feature if feature != "palatal" else "alveolo-palatal"
            for feature in descriptors
        ]

    if "alveolo-palatal" in descriptors and "fricative" in descriptors:
        if "sibilant" not in descriptors:
            descriptors.append("sibilant")

    if "alveolar" in descriptors and "fricative" in descriptors:
        if "sibilant" not in descriptors:
            descriptors.append("sibilant")

    # TODO: should cache this?
    desc = tuple(sorted(descriptors))
    for sound, feat_dict in globals.SOUNDS.items():
        # Collect all features and confirm if all are there
        # TODO: better to sort when loading the SOUNDS
        features = tuple(sorted(feat_dict.values()))
        if desc == features:
            return sound

    # TODO: fixes in case we missed
    if "breathy" in desc:
        new_desc = [v for v in desc if v != "breathy"]
        new_gr = descriptors2grapheme(new_desc)
        if new_gr:
            return "%s[breathy]" % new_gr

    if "long" in desc:
        new_desc = [v for v in desc if v != "long"]
        new_gr = descriptors2grapheme(new_desc)
        if new_gr:
            return "%sː" % new_gr

    return None


# TODO: should cache or pre-process this: if not in list, compute
def features2graphemes(feature_str, sounds):
    """
    Returns a list of graphemes matching a feature description.

    Graphemes are returned according to their definition in the transcription
    system in use. The list of graphemes is sorted first by inverse length
    and then alphabetically, so that it can conveniently be mapped to
    regular expressions.

    For example, asking for not-rounded and not high front vowels:

    >>> alteruphono.utils.features2graphemes("[vowel,front,-rounded,-high]")
    ['ẽ̞ẽ̞', 'ãã', 'a̰ːː', 'ẽẽ', 'e̞e̞', ... 'a', 'e', 'i', 'æ', 'ɛ']

    Parameters
    ----------
    feature_str : string
        A string with the description of feature constraints.

    Returns
    -------
    sounds : list
        A sorted list of all the graphemes matching the requested feature
        constraints.
    """

    # Parse the feature string
    features = parse_features(feature_str)

    # Iterate over all sounds in the transcription system
    graphemes = []
    for grapheme, sound_features in sounds.items():
        # Extract all the features of the current sound
        sound_features = list(sound_features.values())

        # Check if all positive features are there; we can skip
        # immediately if they don't match
        pos_match = all(feat in sound_features for feat in features["positive"])
        if not pos_match:
            continue

        # Check if none of the negative features are there, skipping if not
        neg_match = all(
            feat not in sound_features for feat in features["negative"]
        )
        if not neg_match:
            continue

        # The grapheme passed both tests, add it
        graphemes.append(grapheme)

    # Sort the list, first by inverse length, then alphabetically
    graphemes.sort(key=lambda item: (-len(item), item))

    return tuple(graphemes)


# TODO: comment on `sounds`
def read_sound_classes(sounds, filename=None):
    """
    Read sound class definitions.

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the sound class definition, defaulting
        to the one provided with the library.

    Returns
    -------
    sound_classes : dict
        A dictionary with sound class names as keys (such as "A" or
        "CV"), and corresponding descriptions and list of graphemes
        as values.
    """

    if not filename:
        filename = RESOURCE_DIR / "sound_classes.tsv"
        filename = filename.as_posix()

    with open(filename) as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        sound_classes = {}
        for row in reader:
            if row["GRAPHEMES"]:
                graphemes = tuple(row["GRAPHEMES"].split("|"))
            else:
                graphemes = features2graphemes(row["GRAPHEMES"], sounds)

            sound_classes[row["SOUND_CLASS"]] = {
                "description": row["DESCRIPTION"],
                "features": row["FEATURES"],
                "graphemes": graphemes,
            }

    return sound_classes


def read_sound_features(filename=None):
    """
    Read sound feature definitions.

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the sound feature definition, defaulting
        to the one provided with the library and based on the BIPA
        transcription system.

    Returns
    -------
    features : dict
        A dictionary with feature values (such as "devoiced") as keys and
        feature classes (such as "voicing") as values.
    """

    if not filename:
        filename = RESOURCE_DIR / "features_bipa.tsv"
        filename = filename.as_posix()

    with open(filename) as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        features = {row["VALUE"]: row["FEATURE"] for row in reader}

    return features


def read_sounds(featsys, filename=None):
    """
    Read sound definitions.

    Parameters
    ----------
    featsys : dict
        The feature system to be used.

    filename : string
        Path to the TSV file holding the sound definition, defaulting
        to the one provided with the library and based on the BIPA
        transcription system.

    Returns
    -------
    sounds : dict
        A dictionary with graphemes (such as "a") as keys and
        feature definitions as values.
    """

    if not filename:
        filename = RESOURCE_DIR / "sounds.tsv"
        filename = filename.as_posix()

    sounds = {}
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            features = row["NAME"].split()

            # NOTE: currently skipping over clusters and tones
            if "from" in features:
                continue
            if "tone" in features:
                continue

            descriptors = {featsys[feat]: feat for feat in features}
            sounds[row["GRAPHEME"]] = descriptors

    return sounds


# TODO: better rename to `load`?
def read_phonetic_data():
    """
    Return a single data structure with the default phonetic data.

    Returns
    -------
    data : dict
        A dictionary with default sound features (key `features`),
        sound classes (key `classes`), and sound inventory (key `sounds`).
    """

    globals.FEATURES = read_sound_features()
    globals.SOUNDS = read_sounds(globals.FEATURES)
    globals.SOUND_CLASSES = read_sound_classes(globals.SOUNDS)
    globals.DESC2GRAPH = {}
    globals.APPLYMOD = {}

    # Cache the `graphemes` for `sound_classes`
    # TODO: should be cached in another variable?
    for value in globals.SOUND_CLASSES.values():
        value["graphemes"] = features2graphemes(
            value["features"], globals.SOUNDS
        )


def read_sound_changes(filename=None):
    """
    Read sound changes.

    Sound changes are stored in a TSV file holding a list of sound changes.
    Mandatory fields are, besides a unique `ID`,
    `RULE`, `TEST_ANTE`, and `TEST_POST`.
    A floating-point `WEIGHT` may also be specified
    (defaulting to 1.0 for all rules, unless specified).

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the list of sound changes, defaulting
        to the one provided by the library.

    Returns
    -------
    features : dict
        A dictionary of with IDs as keys and sound changes as values.
    """

    if not filename:
        filename = RESOURCE_DIR / "sound_changes.tsv"
        filename = filename.as_posix()

    # Read the raw notation adding leading and trailing spaces to source
    # and target, as well as adding capturing parentheses to source (if
    # necessary) and replacing back-reference notation in targets
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        rules = {}
        for row in reader:
            rule_id = int(row.pop("ID"))
            row["WEIGHT"] = float(row.get("WEIGHT", 1.0))

            rules[rule_id] = row

    return rules
