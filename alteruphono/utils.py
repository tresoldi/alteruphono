"""
Defines auxiliary functions, structures, and data for the library.
"""

# Python standard libraries imports
import csv
from itertools import chain
from pathlib import Path
import re
import sys
import unicodedata

# Set the resource directory; this requires `zip_safe=False` in setup.py
RESOURCE_DIR = Path(__file__).parent.parent / "resources"

# TODO: should be computed and not coded, see comments in model.py
# TODO: compile the feature description to a Features object
# TODO: should load from disk if found, seeding the cache
HARD_CODED_INVERSE_MODIFIER = {
    ("ɸ", "{'positive': ['fricative'], 'negative': [], 'custom': []}"): "p",
    ("t", "{'positive': ['voiceless'], 'negative': [], 'custom': []}"): "d",
    ("f", "{'positive': ['voiceless'], 'negative': [], 'custom': []}"): "v",
    ("ɶ", "{'positive': ['rounded'], 'negative': [], 'custom': []}"): "a",
    ("ĩ", "{'positive': ['nasalized'], 'negative': [], 'custom': []}"): "i",
    ("t", "{'positive': ['alveolar'], 'negative': [], 'custom': []}"): "k",
    ("c", "{'positive': ['palatal'], 'negative': [], 'custom': []}"): "k",
    ("g", "{'positive': ['voiced'], 'negative': [], 'custom': []}"): "k",
    ("k", "{'positive': ['velar'], 'negative': [], 'custom': []}"): "p",
    ("ɲ", "{'positive': ['palatal'], 'negative': [], 'custom': []}"): "n",
    ("d", "{'positive': ['voiced'], 'negative': [], 'custom': []}"): "t",
    ("b", "{'positive': ['voiced'], 'negative': [], 'custom': []}"): "p",
    ("b̪", "{'positive': ['stop'], 'negative': [], 'custom': []}"): "v",
    ("g", "{'positive': ['stop'], 'negative': [], 'custom': []}"): "ɣ",
    ("x", "{'positive': ['voiceless'], 'negative': [], 'custom': []}"): "ɣ",
    ("d̪", "{'positive': ['stop'], 'negative': [], 'custom': []}"): "ð",
    ("b", "{'positive': ['stop'], 'negative': [], 'custom': []}"): "β",
    (
        "t̠",
        "{'positive': ['post-alveolar'], 'negative': [], 'custom': []}",
    ): "k",
    ("k", "{'positive': ['voiceless'], 'negative': [], 'custom': []}"): "g",
}

# originally from this recipe http://code.activestate.com/recipes/577504/
def rec_getsizeof(o, handlers=None, verbose=False):
    """Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """

    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {
        tuple: iter,
        list: iter,
        dict: dict_handler,
        set: iter,
        frozenset: iter,
    }
    if handlers:
        all_handlers.update(handlers)  # user handlers take precedence
    seen = set()  # track which object id's have already been seen
    default_size = sys.getsizeof(0)  # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:  # do not double count the same object
            return 0
        seen.add(id(o))
        s = sys.getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o))

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)


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
        pos_match = all(feat in sound_features for feat in features.positive)
        if not pos_match:
            continue

        # Check if none of the negative features are there, skipping if not
        neg_match = all(feat not in sound_features for feat in features.negative)
        if not neg_match:
            continue

        # The grapheme passed both tests, add it
        graphemes.append(grapheme)

    # Sort the list, first by inverse length, then alphabetically
    graphemes.sort(key=lambda item: (-len(item), item))

    return tuple(graphemes)


def read_sound_changes(filename=None):
    """
    Read a list of sound changes.

    Sound changes are stored in a TSV file holding a list of sound changes.
    Mandatory fields are a unique `ID` and the `RULE` itself, plus
    the recommended `TEST_ANTE` and `TEST_POST`. A floating-point `WEIGHT`
    for sampling might also be specified, and will default to 1.0 for
    all rules if not provided.

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the list of sound changes, defaulting
        to the one distributed with the library. Strings are cleaned
        upon loading, which includes Unicode normalization to the NFC form.

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
        rules = {}
        for row in csv.DictReader(csvfile, delimiter="\t"):
            rule_id = int(row.pop("ID"))
            row["RULE"] = clear_text(row["RULE"])
            row["TEST_ANTE"] = clear_text(row["TEST_ANTE"])
            row["TEST_POST"] = clear_text(row["TEST_POST"])
            row["WEIGHT"] = float(row.get("WEIGHT", 1.0))

            rules[rule_id] = row

    return rules


def clear_text(text):
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text
