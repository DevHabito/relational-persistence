"""Finite external regression for the retrospective RP-U004-F01 order claim.

These tests compare tiny Boolean orderings. They do not certify the
graph simulator or make a separate physical/predictive claim.
"""

from itertools import product

VALID = ((0, 0), (1, 0), (1, 1))


def f1_rank(score):
    return 2 * score[0] + score[1]


def f2_rank(score):
    return 2 * score[1] + score[0]


def test_only_three_boolean_pairs_have_f2_imply_f1():
    all_pairs = tuple(product((0, 1), repeat=2))
    assert tuple(pair for pair in all_pairs if pair[1] <= pair[0]) == (
        (0, 0), (1, 0), (1, 1),
    )


def test_strict_and_tied_score_comparisons_are_identical():
    for a, b in product(VALID, repeat=2):
        assert (f1_rank(a) < f1_rank(b)) == (f2_rank(a) < f2_rank(b))
        assert (f1_rank(a) == f1_rank(b)) == (f2_rank(a) == f2_rank(b))


def test_future_then_immediate_lex_order_and_ties_are_identical():
    for future_a, now_a, future_b, now_b in product(VALID, repeat=4):
        left = (f1_rank(future_a), f1_rank(now_a))
        right = (f1_rank(future_b), f1_rank(now_b))
        other_left = (f2_rank(future_a), f2_rank(now_a))
        other_right = (f2_rank(future_b), f2_rank(now_b))
        assert (left < right) == (other_left < other_right)
        assert (left == right) == (other_left == other_right)
