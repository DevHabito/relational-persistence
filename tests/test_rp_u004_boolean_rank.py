"""Post-result regression for the nested Boolean objective-order obstruction.

This tests the declared scoring rule, not the complete U004 benchmark.
The Lean module independently certifies the finite comparison logic.
"""

from itertools import product

from experiments.rp_u004_equal_information import _function_merit


ADMISSIBLE = ((0, 0), (1, 0), (1, 1))


def test_nested_boolean_scores_are_the_only_admissible_combinations():
    all_scores = tuple(product((0, 1), repeat=2))
    assert tuple(score for score in all_scores if not score[1] or score[0]) == ADMISSIBLE


def test_greedy_objective_order_is_redundant_for_nested_boolean_functions():
    for a, b in product(ADMISSIBLE, repeat=2):
        f1_preference = _function_merit(a, "F1") > _function_merit(b, "F1")
        f2_preference = _function_merit(a, "F2") > _function_merit(b, "F2")
        f1_tie = _function_merit(a, "F1") == _function_merit(b, "F1")
        f2_tie = _function_merit(a, "F2") == _function_merit(b, "F2")
        assert f1_preference == f2_preference
        assert f1_tie == f2_tie


def test_two_step_future_then_immediate_rankings_also_agree():
    for future_a, now_a, future_b, now_b in product(ADMISSIBLE, repeat=4):
        left = (_function_merit(future_a, "F1"), _function_merit(now_a, "F1"))
        right = (_function_merit(future_b, "F1"), _function_merit(now_b, "F1"))
        left_f2 = (_function_merit(future_a, "F2"), _function_merit(now_a, "F2"))
        right_f2 = (_function_merit(future_b, "F2"), _function_merit(now_b, "F2"))
        assert (left > right) == (left_f2 > right_f2)
        assert (left == right) == (left_f2 == right_f2)


def test_nesting_is_necessary_for_the_rank_equivalence():
    admissible = (1, 0)
    inadmissible = (0, 1)
    assert _function_merit(admissible, "F1") > _function_merit(inadmissible, "F1")
    assert _function_merit(admissible, "F2") < _function_merit(inadmissible, "F2")
