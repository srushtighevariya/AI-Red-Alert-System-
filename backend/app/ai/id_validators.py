"""Checksum validation for ID numbers, so random digit runs (order numbers,
invoice totals, phone numbers) are not reported as cards or Aadhaar numbers."""

# Verhoeff tables (dihedral group D5), used by Aadhaar's last digit.
_VERHOEFF_MULTIPLY = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_VERHOEFF_PERMUTE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def digits_only(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def is_valid_luhn(number: str) -> bool:
    digits = [int(char) for char in digits_only(number)]

    if not 13 <= len(digits) <= 19:
        return False

    total = 0

    for position, digit in enumerate(reversed(digits)):
        if position % 2 == 1:
            digit *= 2

            if digit > 9:
                digit -= 9

        total += digit

    return total % 10 == 0


def is_valid_verhoeff(number: str) -> bool:
    check = 0

    for position, char in enumerate(reversed(digits_only(number))):
        check = _VERHOEFF_MULTIPLY[check][_VERHOEFF_PERMUTE[position % 8][int(char)]]

    return check == 0


def is_valid_aadhaar(number: str) -> bool:
    digits = digits_only(number)

    # Aadhaar numbers are 12 digits and never start with 0 or 1. A single
    # repeated digit (999999999999) passes Verhoeff but is a placeholder.
    return (
        len(digits) == 12
        and digits[0] not in "01"
        and len(set(digits)) > 1
        and is_valid_verhoeff(digits)
    )
