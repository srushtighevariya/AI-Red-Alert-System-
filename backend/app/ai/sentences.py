"""Sentence splitting that copes with Indian legal and business documents.

A plain "split after every full stop" breaks "Adv. R. K. Mehta" into three
sentences and "Rs. 2,18,760" into two. Here a full stop only ends a sentence
when the word before it is not a known abbreviation or an initial, and the
next word does not start in lower case. Line breaks end a sentence for
headings, address lines and lists, but not for a long line that simply wraps.

sentence_spans() returns (start, end) offsets, so callers can map sentences
back to positions in the original text.
"""

import re

ABBREVIATIONS = {
    # titles and names
    "adv", "mr", "mrs", "ms", "dr", "sr", "jr", "smt", "shri", "sh", "prof", "hon", "kum",
    # legal and business
    "no", "nos", "rs", "re", "dt", "dtd", "regd", "ltd", "pvt", "co", "corp", "inc", "bros",
    "vs", "v", "u", "s", "sec", "secs", "art", "cl", "para", "ch", "ref", "govt", "dept",
    "tel", "mob", "ph", "fax", "acc", "ac", "a/c", "addl", "asst", "dist", "rd", "st", "nr",
    "opp", "approx", "est", "etc", "viz", "ie", "eg", "fig", "vol", "pg", "pp", "max", "min",
    "inr", "amt", "qty", "encl", "attn", "cc", "bldg", "flr", "blk",
    # months
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
}

BOUNDARY = re.compile(r"[.!?।]+[\"'”’)\]]*(?=\s|$)|\n")
WORD_BEFORE = re.compile(r"([^\s(\[\"“]+)$")
WRAPPED_LINE_MIN_WORDS = 8


def _is_abbreviation(text: str, dot_index: int) -> bool:
    match = WORD_BEFORE.search(text[max(dot_index - 30, 0):dot_index])

    if not match:
        return False

    token = match.group(1).lower().strip(".,:;")
    last_part = re.split(r"[./]", token)[-1] if token else ""

    return (
        token in ABBREVIATIONS
        or last_part in ABBREVIATIONS
        or len(last_part) == 1  # an initial such as "R." or "A. D."
    )


def _next_starts_lowercase(text: str, index: int) -> bool:
    following = text[index:index + 40].lstrip()
    return bool(following) and following[0].islower()


def _line_ends_sentence(line: str, next_line: str) -> bool:
    stripped = line.strip()

    if not stripped or not next_line.strip():
        return True  # blank line = paragraph break

    if stripped[-1] in ".!?:;।":
        return True

    # A long line without punctuation followed by lower-case text is a wrapped
    # sentence (common in PDFs); anything else (headings, addresses) is separate.
    is_long = len(stripped.split()) >= WRAPPED_LINE_MIN_WORDS
    return not (is_long and next_line.lstrip()[:1].islower())


def sentence_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    start = 0

    def add(end: int) -> None:
        segment = text[start:end]
        leading = len(segment) - len(segment.lstrip())
        trailing = len(segment) - len(segment.rstrip())

        if segment.strip():
            spans.append((start + leading, end - trailing))

    for match in BOUNDARY.finditer(text):
        if match.start() < start:
            continue

        if match.group() == "\n":
            line_start = text.rfind("\n", 0, match.start()) + 1
            next_end = text.find("\n", match.end())
            next_line = text[match.end(): next_end if next_end != -1 else len(text)]

            if not _line_ends_sentence(text[line_start:match.start()], next_line):
                continue

            add(match.start())
        else:
            if match.group().startswith(".") and len(match.group().rstrip("\"'”’)]")) == 1:
                if _is_abbreviation(text, match.start()) or _next_starts_lowercase(text, match.end()):
                    continue

            add(match.end())

        start = match.end()

    add(len(text))
    return spans


def split_sentences(text: str) -> list[str]:
    return [" ".join(text[start:end].split()) for start, end in sentence_spans(text)]
