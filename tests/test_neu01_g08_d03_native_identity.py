"""G08-D03 pre-source IEEE float32 widening and signed-zero negative gates."""
from __future__ import annotations

from hashlib import sha256
import struct

import numpy as np
import pytest

from experiments import neu01_g08_d03_native_identity as d


def canonical_scalar_oracle(values):
    """Independent built-in struct f32 roundtrip to f64 little endian."""
    return b"".join(
        struct.pack("<d",struct.unpack("<f",struct.pack("<f",v))[0])
        for v in values
    )


def test_independent_scalar_oracle_and_exact_widening_hash():
    sample = [0., -0., 1., -1.25, 0.125, 43.625]
    root = np.array(sample,dtype="<f4").reshape(3,2).astype("<f8")
    derived = np.array(sample,dtype="<f8").reshape(3,2)
    observed = d.inspect_direct_arrays(root, derived, shift=1)
    assert root.tobytes(order="C")==canonical_scalar_oracle(sample)
    assert observed["direct_identity_status"]=="EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL"
    assert observed["all_aligned_numeric_values_count"]==6
    assert observed["numeric_equal_count"]==6
    assert observed["ieee_64bit_pattern_equal_count"]==6
    assert observed["canonical_64bit_content_digests_identical"] is True
    assert observed["maximum_absolute_native_numeric_difference"]==0.
    assert observed["source_original_double_canonical_sha256"]==sha256(
        canonical_scalar_oracle(sample)
    ).hexdigest()
    assert observed["fixed_500_frame_shift_exact_numeric_equal_count"]<6
    assert observed["fixed_reversed_61_channel_exact_numeric_equal_count"]<6


def test_signed_zero_numerical_equality_not_same_bits():
    x=np.array([[0.,-0.],[2.,3.],[4.,5.]],dtype="<f8")
    y=x.copy()
    y[0,1]=0.
    o=d.inspect_direct_arrays(x,y,shift=1)
    assert o["direct_identity_status"]=="NUMERIC_EQUAL_IEEE_BITS_DIFFER"
    assert o["numeric_equal_count"]==6
    assert o["ieee_64bit_pattern_equal_count"]==5
    assert o["numeric_equal_but_ieee_bits_differ_count"]==1
    assert o["canonical_64bit_content_digests_identical"] is False
    assert o["maximum_absolute_native_numeric_difference"]==0.


def test_single_position_numeric_mutation_must_not_be_missed():
    original=np.array([[1.,2.],[3.,4.],[5.,6.]],dtype="<f8")
    changed=original.copy()
    changed[1,0]+=0.5
    o=d.inspect_direct_arrays(original,changed,shift=1)
    assert o["direct_identity_status"]=="AUTHENTICATED_NATIVE_ARRAYS_DIFFER"
    assert o["numeric_equal_count"]==5
    assert o["numeric_differ_count"]==1
    assert o["ieee_64bit_pattern_differ_count"]==1
    assert o["maximum_absolute_native_numeric_difference"]==0.5


def test_nonfinite_dtype_shape_and_controls_rejected():
    x=np.array([[1.,2.],[3.,4.],[5.,6.]],dtype="<f8")
    with pytest.raises(d.SourceNotEligible,match="SHAPE"):
        d.inspect_direct_arrays(x,x[:,:1])
    with pytest.raises(d.SourceNotEligible,match="DOUBLE"):
        d.inspect_direct_arrays(x.astype("<f4"),x)
    with pytest.raises(d.SourceNotEligible,match="NONFINITE"):
        y=x.copy();y[0,0]=np.nan
        d.inspect_direct_arrays(x,y)
    with pytest.raises(d.SourceNotEligible,match="CONTROL"):
        d.inspect_direct_arrays(x,x,shift=0)


def test_float32_widening_is_exact_and_no_fuzzy_tolerance():
    x=np.array([1.125,3.875,0.2,-.3],dtype="<f4")
    y=x.astype("<f8")
    assert y[2]!=0.2
    assert np.array_equal(y,x.astype("<f8"))
    a=np.array([[y[0],y[1]],[y[2],y[3]],[0.,-0.]],dtype="<f8")
    b=a.copy()
    b[1,0]=0.2
    o=d.inspect_direct_arrays(a,b,shift=1)
    assert o["numeric_differ_count"]==1


def test_immutable_G08_D02_and_original_historical_data_before_source():
    d.verify_previous_evidence()
    assert sha256(d.d02.G08_AUDIT.read_bytes()).hexdigest()==d.d02.ORIGINAL_G08_SHA
    path="docs/results/NEU-01-G08-D02-first-run/audit.json"
    from pathlib import Path
    assert sha256(Path(path).read_bytes()).hexdigest()==d.PRIOR_D02_SHA
