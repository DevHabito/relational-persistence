"""NEU-01-G02 pre-source synthetic negative controls.

Every numeric vector is invented here, *not* a physiological EEG sample.
The first real G02 source run is only allowed after these controls pass.
"""
from __future__ import annotations

from copy import deepcopy
from io import BytesIO
import subprocess
import sys

import numpy as np
import pytest

from experiments import neu01_g02_original_signal_qc as qc
from experiments import neu01_g01_brainvision_auth as original


@pytest.fixture
def tiny(monkeypatch):
    monkeypatch.setattr(qc,"N_FRAMES",3000)
    monkeypatch.setattr(qc,"EPOCH_FRAMES",100)
    monkeypatch.setattr(qc,"N_EPOCHS",30)
    monkeypatch.setattr(qc,"TOTAL_PER_TASK",3000*61)
    monkeypatch.setattr(qc,"EPOCH_CELLS",30*61)
    monkeypatch.setattr(qc,"EXACT_ADJACENT_TRANSITIONS",61*2999)
    return np.broadcast_to(
        (np.arange(3000,dtype=np.float32)*0.01)[:,None],
        (3000,61)
    ).copy()


def test_registered_source_ids_hashes_and_fixed_unmodified_g01():
    assert qc.PROTOCOL_SHA=="8afd08353216c0afc3a58a13e2132de2f8c62e67"
    assert qc.SOURCE_SHA[("eyesclosed","eeg")]==(
        "022b9f34914e4314f4d9e45d17bc367031c9d9d879ea983a8d6eb43f7affbc47"
    )
    assert qc.SOURCE_SHA[("eyesopen","eeg")]==(
        "d4c9357b8996fa8e989317d9c945b8e71adfe9e3564c96812689c9cf29e09ac9"
    )
    assert qc.N_CHANNELS==61
    assert qc.HZ==500
    assert qc.EXTREME_FACTOR==10
    assert original.SOURCE_COMMIT=="0c740d838a2c33feeec0b6e514aea323d0e65ca4"


def test_variable_finite_no_flat_or_extreme_counts_and_denominator(tiny):
    report=qc.describe_original_samples(tiny)
    assert report["total_original_float32_values"]==183000
    assert report["finite_sample_count"]==183000
    assert report["nan_sample_count"]==0
    assert report["positive_infinity_sample_count"]==0
    assert report["negative_infinity_sample_count"]==0
    assert report["channels_with_all_finite_values"]==61
    assert report["total_ten_second_channel_epochs"]==1830
    assert report["finite_ten_second_channel_epochs"]==1830
    assert report["ten_second_channel_epochs_exactly_constant"]==0
    assert report["ten_second_channel_epochs_with_relative_ptp_extreme"]==0
    assert report["median_native_numeric_epoch_std"] is not None
    assert report["external_artifact_free_status"]=="NOT_ESTABLISHED"
    assert report["physical_adc_clipping_status"]=="NOT_IDENTIFIABLE_WITHOUT_CALIBRATION"
    assert report["lzc_result_computed"] is False


def test_invented_flatline_channels_and_epochs_are_not_dropped(tiny):
    tiny[:,0]=0
    tiny[0:100,1]=2
    r=qc.describe_original_samples(tiny)
    assert r["channels_exactly_constant_full_record"]==1
    assert r["ten_second_channel_epochs_exactly_constant"]==31
    assert r["channels_with_any_exactly_constant_epoch"]==2
    assert r["channels_with_undefined_relative_extreme_reference"]==1
    assert r["finite_sample_count"]==183000
    assert r["total_ten_second_channel_epochs"]==1830


def test_nan_both_infinities_and_distinct_invalid_epoch_counts(tiny):
    tiny[0,0]=np.nan
    tiny[20,1]=np.inf
    tiny[101,2]=-np.inf
    r=qc.describe_original_samples(tiny)
    assert (r["nan_sample_count"],r["positive_infinity_sample_count"],
            r["negative_infinity_sample_count"])==(1,1,1)
    assert r["finite_sample_count"]==183000-3
    assert r["channels_with_nonfinite_values"]==3
    assert r["ten_second_channel_epochs_with_nonfinite"]==3
    assert r["finite_ten_second_channel_epochs"]==1830-3
    assert r["total_original_float32_values"]==183000


def test_repeated_adjacent_values_are_accounted_without_calling_them_disease(tiny):
    tiny[0:100,0]=0
    r=qc.describe_original_samples(tiny)
    assert r["exact_adjacent_equal_within_channel_pairs"]>=99
    assert r["ten_second_channel_epochs_exactly_constant"]==1
    assert r["original_adjacent_pair_universe"]==61*2999


def test_strict_relative_peak_to_peak_extreme_is_descriptive_not_rejection(tiny):
    tiny[2900:3000,0]=np.linspace(0,20,100,dtype=np.float32)
    r=qc.describe_original_samples(tiny)
    assert r["ten_second_channel_epochs_with_relative_ptp_extreme"]==1
    assert r["channels_with_undefined_relative_extreme_reference"]==0
    assert r["finite_ten_second_channel_epochs"]==1830


def test_wrong_dtype_and_source_shape_are_rejected(tiny):
    with pytest.raises(qc.QcInstrumentError,match="WRONG_FLOAT32_SOURCE_DTYPE"):
        qc.describe_original_samples(tiny.astype(np.float64))
    with pytest.raises(qc.QcInstrumentError,match="WRONG_ORIGINAL_FRAME_CHANNEL_SHAPE"):
        qc.describe_original_samples(tiny[:2800])


def create_header(count=61, resolution="1", unit="µV"):
    return (
        "[Common Infos]\nNumberOfChannels="+str(count)+
        "\n[Channel Infos]\n"+
        "".join(f"Ch{i}=E{i},,{resolution},{unit}\n" for i in range(1,count+1))
    ).encode("latin-1")


def test_declared_channel_units_and_resolutions_aggregated_without_names():
    m=qc.parse_channel_metadata(create_header())
    assert m["header_unit_counts"]=={"µV":61}
    assert m["header_resolution_counts"]=={"1":61}
    assert m["physical_amplifier_clipping_threshold_verified"] is False
    assert "E1" not in str(m)


@pytest.mark.parametrize("count,resolution,unit,message",[
    (60,"1","µV","ORIGINAL_HEADER_CHANNEL_COUNT_CHANGED"),
    (61,"NaN","µV","CHANNEL_RESOLUTION_INVALID"),
    (61,"0","µV","CHANNEL_RESOLUTION_INVALID"),
    (61,"non-numeric","µV","CHANNEL_RESOLUTION_UNPARSABLE"),
])
def test_bad_header_dimension_resolution_or_unit_rejected(count,resolution,unit,message):
    with pytest.raises(qc.QcInstrumentError,match=message):
        qc.parse_channel_metadata(create_header(count,resolution,unit))


def test_original_header_omitted_unit_or_scaling_is_not_invented():
    missing_unit=qc.parse_channel_metadata(create_header(61,"1",""))
    assert missing_unit["header_channels_missing_declared_unit"]==61
    assert missing_unit["header_channels_missing_declared_resolution"]==0
    assert missing_unit["header_unit_counts"]=={"MISSING":61}
    assert missing_unit["header_calibration_complete"] is False

    minimal=(
        "[Common Infos]\\nNumberOfChannels=61\\n[Channel Infos]\\n"
        + "".join(f"Ch{i}=E{i},\\n" for i in range(1,62))
    ).replace("\\n","\n").encode("latin-1")
    omitted=qc.parse_channel_metadata(minimal)
    assert omitted["header_channels_missing_declared_unit"]==61
    assert omitted["header_channels_missing_declared_resolution"]==61
    assert omitted["header_calibration_complete"] is False
    assert omitted["header_resolution_counts"]=={"MISSING":61}
    assert qc.REVISION_SHA=="b4671dd92236d88edde55fa72a0fb587c36bbae5"


def test_g02_network_unavailable_does_not_create_false_signal_result(monkeypatch):
    def offline(*args,**kwargs):
        raise original.SourceBlocked("PUBLIC_ORIGINAL_OBJECT_NOT_RETRIEVED")
    monkeypatch.setattr(original,"download_verified",offline)
    r=qc.run_source()
    assert r["decision"]=="SOURCE_RETRIEVAL_BLOCKED"
    assert r["lzc_computed"] is False
    assert r["all_source_objects_authenticated"] is False
    assert "tasks" not in r


def test_original_wrong_identity_never_relabelled_as_physio_event(monkeypatch):
    def altered(*args,**kwargs):
        raise original.SourceHashMismatch("G01_SOURCE_SHA256_NOT_REPRODUCED")
    monkeypatch.setattr(original,"download_verified",altered)
    r=qc.run_source()
    assert r["decision"]=="ORIGINAL_SOURCE_HASH_MISMATCH"
    assert "tasks" not in r


def test_explicit_guard_stays_active_with_optimized_python():
    cmd=(
        "from experiments.neu01_g02_original_signal_qc import "
        "describe_original_samples,QcInstrumentError;"
        "import numpy as np;"
        "\ntry:\n describe_original_samples(np.zeros((2,2),dtype=np.float32));print('BROKEN')"
        "\nexcept QcInstrumentError:\n print('GUARDS_ACTIVE')"
    )
    x=subprocess.run([sys.executable,"-O","-c",cmd],capture_output=True,
                     text=True,timeout=30,check=False)
    assert x.returncode==0,x.stderr
    assert x.stdout.strip()=="GUARDS_ACTIVE"
