# TODO: allow different boundary symbols, including "^" and "$"
# TODO: implement a Token/Sound class for elements, even if only strings
# TODO: text normalization here as well
# TODO: add function to compare to string/list/tuple


class Sequence:
    def __init__(self, sequence, sep=" "):
        # Split `sequence` string and convert to lists tuple ones
        if isinstance(sequence, str):
            sequence = sequence.split(sep)
        elif isinstance(sequence, tuple):
            sequence = list(sequence)

        # Add boundaries if necessary
        # TODO: use .insert and .append
        if sequence[0] != "#":
            sequence = ["#"] + sequence
        if sequence[-1] != "#":
            sequence = sequence + ["#"]

        # Store sequence and separator (used to return as str)
        self._sequence = sequence
        self._sep = sep

    def __getitem__(self, idx):
        return self._sequence[idx]

    def __iter__(self):
        self._iter_idx = 0
        return self

    def __next__(self):
        if self._iter_idx == len(self._sequence):
            raise StopIteration

        ret = self._sequence[self._iter_idx]
        self._iter_idx += 1

        return ret

    def __len__(self):
        return len(self._sequence)

    def __repr__(self):
        return repr(self._sequence)

    def __str__(self):
        return self._sep.join(self._sequence)