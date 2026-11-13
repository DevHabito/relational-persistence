"""G08-D02 negative tests; independent loop oracles, no original EEG fetch."""
from __future__ import annotations

from hashlib import sha256
import math

import numpy as np
import pytest

from experiments import neu01_g08_d02_global_residual as g


def slow_project_and_fit(a,b):
    """Synthetic small-matrix independent loop (not production vectorized path)."""
    n=len(a); m=len(a[0])
    aa=[[a[i][j]-sum(a[i])/m for j in range(m)] for i in range(n)]
    bb=[[b[i][j]-sum(b[i])/m for j in range(m)] for i in range(n)]
    x=sum(aa[i][j]*aa[i][j] for i in range(n) for j in range(m))
    xy=sum(aa[i][j]*bb[i][j] for i in range(n) for j in range(m))
    y=sum(bb[i][j]*bb[i][j] for i in range(n) for j in range(m))
    alpha=xy/x
    r=sum((bb[i][j]-alpha*aa[i][j])**2 for i in range(n) for j in range(m))
    return alpha, (r/y)**0.5


def test_shared_gain_exact_common_reference_even_with_time_varying_offsets():
    x=np.array([[2.,1.,-1.],[3.,7.,2.],[5.,4.,10.],[1.,6.,4.]],dtype=float)
    offset=np.array([100.,-3.,15.,44.])[:,None]
    derivative=3*x+offset
    result=g.projected_global_residual(x,derivative,shift=2)
    alpha,resid=slow_project_and_fit(x.tolist(),derivative.tolist())
    assert abs(result["shared_least_squares_gain"]-alpha)<1e-12
    assert abs(result["fitted_gain_relative_frobenius_residual"]-resid)<1e-12
    assert abs(result["shared_least_squares_gain"]-3)<1e-12
    assert result["fitted_gain_relative_frobenius_residual"]<1e-12
    assert result["fixed_gain_one_relative_frobenius_residual"]>1
    assert result["fixed_500_frame_shift_same_gain_residual"]>0.1
    assert result["fixed_channel_reversal_same_gain_residual"]>0.1


def test_gain_one_referencing_and_non_common_perturbation():
    a=np.array([[2.,1.,-1.],[3.,7.,2.],[5.,4.,10.],[1.,6.,4.]],dtype=float)
    b=a-a.mean(axis=1,keepdims=True)
    z=g.projected_global_residual(a,b,shift=2)
    assert abs(z["shared_least_squares_gain"]-1)<1e-12
    assert z["fitted_gain_relative_frobenius_residual"]<1e-12
    b[2,0]+=0.25
    w=g.projected_global_residual(a,b,shift=2)
    assert w["fitted_gain_relative_frobenius_residual"]>0
    assert w["fitted_gain_relative_frobenius_residual"]>z["fitted_gain_relative_frobenius_residual"]


def test_channel_reversal_without_search_is_negative_control():
    a=np.array([[2.,1.,-1.],[3.,7.,2.],[5.,4.,10.],[1.,6.,4.]],dtype=float)
    b=2*a+np.array([7.,5.,4.,1.])[:,None]
    z=g.projected_global_residual(a,b,shift=2)
    assert z["fixed_channel_reversal_same_gain_residual"]>0.5


def test_invalid_degenerate_nonfinite_and_shift_fail():
    a=np.ones((4,3))
    with pytest.raises(g.ResidualNotEligible,match="DEGENERATE"):
        g.projected_global_residual(a,a)
    with pytest.raises(g.ResidualNotEligible,match="NONFINITE"):
        b=a.copy(); b[0,0]=float("nan")
        g.projected_global_residual(a,b)
    with pytest.raises(g.ResidualNotEligible,match="SHAPE"):
        g.projected_global_residual(a,a[:,:2])
    with pytest.raises(g.ResidualNotEligible,match="CONTROL"):
        g.projected_global_residual(a,a,shift=0)


def test_original_previous_g08_and_g05_archives_are_immutable():
    known=g.verified_archives()
    assert known["census"]["within_channel_equal_adjacent"]==130491
    assert known["census"]["nonzero_equal_adjacent"]==130304
    assert sha256(g.G08_AUDIT.read_bytes()).hexdigest()==g.ORIGINAL_G08_SHA
    assert sha256(g.G05_AUDIT.read_bytes()).hexdigest()==g.ORIGINAL_G05_SHA


def test_g05_old_root_census_exactly_reconciles_or_fails():
    known=g.verified_archives()
    expected_census={
        "total_native_values":9150000,
        "exact_zero_values":5923,
        "native_nonzero_samples":9144077,
        "native_integer_nonzero_samples":912943,
        "within_channel_equal_adjacent":130491,
        "zero_zero_equal_adjacent":187,
        "nonzero_equal_adjacent":130304,
        "native_integer_nonzero_equal_pairs":13008,
        "native_noninteger_nonzero_equal_pairs":117296,
    }
    g.compare_original_root(expected_census,known)
    expected_census["nonzero_equal_adjacent"]+=1
    with pytest.raises(g.PriorCountMismatch,match="nonzero_equal_adjacent"):
        g.compare_original_root(expected_census,known)


def test_native_exact_counts_synthetic_float32_and_float64():
    monkey_vals=np.array([0.,-0.,1.,1.,1.,0.5,0.5,-3.,-3.,-1.25],dtype=np.float32)
    x=np.zeros((g.FRAMES,g.CHANNELS),dtype=np.float32)
    x[:10,0]=monkey_vals
    result=g.original_native_census(x)
    # Baseline all other channel samples are zero; exact accounting is mandatory.
    assert result["total_native_values"]==g.FRAMES*g.CHANNELS
    assert result["within_channel_equal_adjacent"]==result["zero_zero_equal_adjacent"]+result["nonzero_equal_adjacent"]
    assert result["native_nonzero_samples"]+result["exact_zero_values"]==result["total_native_values"]
    assert result["native_integer_nonzero_equal_pairs"]<=result["nonzero_equal_adjacent"]
    with pytest.raises(g.ResidualNotEligible,match="NONFINITE"):
        x[0,0]=float("nan"); g.original_native_census(x)
