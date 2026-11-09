"""NEU-01-G02 — exact, bounded quality census of original EEG *sample values*.

First protocol committed alone as 8afd08353216c0afc3a58a13e2132de2f8c62e67
before any original G02 signal values were accessed. Do NOT calculate LZc,
compare psychological states statistically or publish per-electrode voltages.

The G01 verified original OpenNeuro BrainVision source is reused with the
independent G01 SHA-256 and original annex MD5/byte-size guards.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from experiments import neu01_g01_brainvision_auth as source

PROTOCOL_SHA="8afd08353216c0afc3a58a13e2132de2f8c62e67"
REVISION_SHA="b4671dd92236d88edde55fa72a0fb587c36bbae5"
OUTPUT=Path("docs/results/NEU-01-G02-first-run/audit.json")
SOURCE_SHA={
    ("eyesclosed","vhdr"):"b3f437f5e1cc95b3dbedb989d9c637c832ae4406b55782f8c8aeeb2fefc96061",
    ("eyesclosed","eeg"):"022b9f34914e4314f4d9e45d17bc367031c9d9d879ea983a8d6eb43f7affbc47",
    ("eyesopen","vhdr"):"7a02a0d6d25413ebc1600a737f2d30f33fc4fc608b25c03564f5918463c3845f",
    ("eyesopen","eeg"):"d4c9357b8996fa8e989317d9c945b8e71adfe9e3564c96812689c9cf29e09ac9",
}
N_CHANNELS=61
N_FRAMES=150000
HZ=500
EPOCH_FRAMES=5000
N_EPOCHS=30
TOTAL_PER_TASK=N_CHANNELS*N_FRAMES
EPOCH_CELLS=N_CHANNELS*N_EPOCHS
EXACT_ADJACENT_TRANSITIONS=N_CHANNELS*(N_FRAMES-1)
EXTREME_FACTOR=10


class QcInstrumentError(ValueError):
    pass


def bounded_float(value:float) -> float:
    if not math.isfinite(value):
        raise QcInstrumentError("NONFINITE_AGGREGATE_METRIC")
    # Decimal rendering is stable between runs on a pinned numpy+Python
    # environment; tiny differences are not scientific effects.
    return round(float(value),10)


def parse_channel_metadata(header:bytes) -> dict:
    """Never invent acquisition scaling/units when original header omits them."""
    sections=source.parse_sections(header)
    common=sections.get("common infos",{})
    if common.get("NumberOfChannels")!="61":
        raise QcInstrumentError("ORIGINAL_HEADER_CHANNEL_COUNT_CHANGED")
    channels=sections.get("channel infos",{})
    if len(channels)!=N_CHANNELS:
        raise QcInstrumentError("CHANNEL_DETAIL_COUNT_CHANGED")
    units=Counter()
    resolutions=Counter()
    missing_units=0
    missing_resolutions=0
    for i in range(1,N_CHANNELS+1):
        value=channels.get(f"Ch{i}")
        if not isinstance(value,str):
            raise QcInstrumentError("CHANNEL_ORDINALS_NOT_COMPLETE")
        parts=value.split(",")
        if not parts or not parts[0].strip():
            raise QcInstrumentError("CHANNEL_NAME_MISSING")
        declared_res=parts[2].strip() if len(parts)>2 else ""
        declared_unit=parts[3].strip() if len(parts)>3 else ""
        if not declared_res:
            missing_resolutions+=1
            resolutions["MISSING"]+=1
        else:
            try:
                res=float(declared_res)
            except ValueError as exc:
                raise QcInstrumentError("CHANNEL_RESOLUTION_UNPARSABLE") from exc
            if not math.isfinite(res) or res<=0:
                raise QcInstrumentError("CHANNEL_RESOLUTION_INVALID")
            resolutions[format(res,".12g")]+=1
        if not declared_unit:
            missing_units+=1
            units["MISSING"]+=1
        else:
            units[declared_unit]+=1
    if sum(units.values())!=N_CHANNELS or sum(resolutions.values())!=N_CHANNELS:
        raise QcInstrumentError("CHANNEL_METADATA_PARTITION_FAILURE")
    return {
        "header_unit_counts":dict(sorted(units.items())),
        "header_resolution_counts":dict(sorted(resolutions.items())),
        "header_channels_missing_declared_resolution":missing_resolutions,
        "header_channels_missing_declared_unit":missing_units,
        "header_calibration_complete":missing_resolutions==0 and missing_units==0,
        "physical_amplifier_clipping_threshold_verified":False,
    }


def describe_original_samples(data:np.ndarray) -> dict:
    """Complete full-record census; no channel values/identity leave function."""
    if getattr(data,"dtype",None)!=np.dtype("<f4") and getattr(data,"dtype",None)!=np.dtype("float32"):
        raise QcInstrumentError("WRONG_FLOAT32_SOURCE_DTYPE")
    if data.shape != (N_FRAMES,N_CHANNELS):
        raise QcInstrumentError("WRONG_ORIGINAL_FRAME_CHANNEL_SHAPE")
    nan_count=0
    positive_inf_count=0
    negative_inf_count=0
    finite_count=0
    zero_count=0
    adjacent_eq_count=0
    channel_nonfinite=0
    whole_constant=0
    channel_flat_epoch=0
    nonfinite_epoch=0
    flat_epochs=0
    finite_epochs=0
    extremes=0
    undefined_extreme_channels=0
    epoch_ptps=[]
    epoch_stds=[]
    epoch_rmss=[]
    for ci in range(N_CHANNELS):
        # MEMMAP column into float64 to avoid precision overflow in RMS, but
        # samples are originally decoded and authenticated as little-endian f4.
        values=np.asarray(data[:,ci],dtype=np.float64)
        finite=np.isfinite(values)
        n_nan=int(np.count_nonzero(np.isnan(values)))
        n_pos=int(np.count_nonzero(np.isposinf(values)))
        n_neg=int(np.count_nonzero(np.isneginf(values)))
        n_fin=int(np.count_nonzero(finite))
        if n_fin+n_nan+n_pos+n_neg != N_FRAMES:
            raise QcInstrumentError("FLOAT_CLASSIFICATION_NOT_CONSERVED")
        nan_count+=n_nan
        positive_inf_count+=n_pos
        negative_inf_count+=n_neg
        finite_count+=n_fin
        zero_count+=int(np.count_nonzero(values==0))
        adjacent_eq_count+=int(np.count_nonzero(values[1:]==values[:-1]))
        if n_fin!=N_FRAMES:
            channel_nonfinite+=1
        elif bool(np.all(values==values[0])):
            whole_constant+=1
        ptps=[]
        had_flat=False
        for i in range(N_EPOCHS):
            epoch=values[i*EPOCH_FRAMES:(i+1)*EPOCH_FRAMES]
            if len(epoch)!=EPOCH_FRAMES:
                raise QcInstrumentError("EPOCH_LENGTH_NOT_COMPLETE")
            if not bool(np.all(np.isfinite(epoch))):
                nonfinite_epoch+=1
                continue
            finite_epochs+=1
            ptp=float(np.max(epoch)-np.min(epoch))
            if not math.isfinite(ptp) or ptp<0:
                raise QcInstrumentError("PTP_UNDEFINED")
            if ptp==0:
                flat_epochs+=1
                had_flat=True
            sd=float(np.std(epoch,dtype=np.float64))
            rms=float(np.sqrt(np.mean(np.square(epoch,dtype=np.float64))))
            if not math.isfinite(sd) or not math.isfinite(rms):
                raise QcInstrumentError("STD_OR_RMS_UNDEFINED")
            ptps.append(ptp)
            epoch_ptps.append(ptp)
            epoch_stds.append(sd)
            epoch_rmss.append(rms)
        if had_flat:
            channel_flat_epoch+=1
        if not ptps:
            undefined_extreme_channels+=1
            continue
        median_ptp=float(np.median(ptps))
        if median_ptp<=0:
            undefined_extreme_channels+=1
            continue
        extremes+=sum(v>EXTREME_FACTOR*median_ptp for v in ptps)
    if nan_count+positive_inf_count+negative_inf_count+finite_count!=TOTAL_PER_TASK:
        raise QcInstrumentError("ALL_SAMPLE_DENOMINATOR_NOT_CONSERVED")
    if finite_epochs+nonfinite_epoch!=EPOCH_CELLS:
        raise QcInstrumentError("ALL_CHANNEL_EPOCHS_NOT_CONSERVED")
    if adjacent_eq_count>EXACT_ADJACENT_TRANSITIONS:
        raise QcInstrumentError("ADJACENT_COUNT_OUTSIDE_UNIVERSE")
    if whole_constant>channel_flat_epoch:
        raise QcInstrumentError("CONSTANT_CHANNEL_EPOCH_INVARIANT")
    if flat_epochs>finite_epochs or extremes>finite_epochs:
        raise QcInstrumentError("EPOCH_FLAG_EXCEEDS_VALID_UNIVERSE")
    if undefined_extreme_channels>N_CHANNELS:
        raise QcInstrumentError("UNDEFINED_MEDIAN_CHANNELS_EXCEED_SOURCE")
    def median(values):
        return bounded_float(float(np.median(values))) if values else None
    return {
        "total_original_float32_values":TOTAL_PER_TASK,
        "finite_sample_count":finite_count,
        "nan_sample_count":nan_count,
        "positive_infinity_sample_count":positive_inf_count,
        "negative_infinity_sample_count":negative_inf_count,
        "exact_zero_sample_count":zero_count,
        "exact_adjacent_equal_within_channel_pairs":adjacent_eq_count,
        "original_adjacent_pair_universe":EXACT_ADJACENT_TRANSITIONS,
        "channels_with_nonfinite_values":channel_nonfinite,
        "channels_with_all_finite_values":N_CHANNELS-channel_nonfinite,
        "channels_exactly_constant_full_record":whole_constant,
        "total_ten_second_channel_epochs":EPOCH_CELLS,
        "finite_ten_second_channel_epochs":finite_epochs,
        "ten_second_channel_epochs_with_nonfinite":nonfinite_epoch,
        "ten_second_channel_epochs_exactly_constant":flat_epochs,
        "channels_with_any_exactly_constant_epoch":channel_flat_epoch,
        "relative_extreme_ptp_factor_strictly_greater_than":EXTREME_FACTOR,
        "ten_second_channel_epochs_with_relative_ptp_extreme":extremes,
        "channels_with_undefined_relative_extreme_reference":undefined_extreme_channels,
        "median_native_numeric_epoch_ptp":median(epoch_ptps),
        "median_native_numeric_epoch_std":median(epoch_stds),
        "median_native_numeric_epoch_rms":median(epoch_rmss),
        "external_artifact_free_status":"NOT_ESTABLISHED",
        "physical_adc_clipping_status":"NOT_IDENTIFIABLE_WITHOUT_CALIBRATION",
        "lzc_result_computed":False,
    }


def run_source(opener=source.urlopen) -> dict:
    result={"study":"NEU-01-G02","protocol_only_commit":PROTOCOL_SHA,
            "pre_original_signal_content_addendum_commit":REVISION_SHA,
            "original_failed_first_attempt":42637541779,
            "original_openneuro_source_commit":source.SOURCE_COMMIT,
            "source_version":"ds004148/1.0.0",
            "source_scope":"original sub-01 session1 eyesclosed and eyesopen only",
            "n_original_channels_each":N_CHANNELS,"n_samples_per_channel_each":N_FRAMES,
            "original_sample_rate_hz":HZ,"ten_second_epochs_each":N_EPOCHS,
            "all_source_objects_authenticated":False,
            "original_signal_values_published":False,
            "lzc_computed":False,"subjective_self_or_clinical_claim":False,
            "source_eyesopen_additional_ICA_documented":True,
            "decision":"INSTRUMENT_FAILURE"}
    reports={}
    try:
        with TemporaryDirectory(prefix="neu01-g02-") as directory:
            for task in ("eyesclosed","eyesopen"):
                file_info={}
                local={}
                for ext in ("vhdr","eeg"):
                    path=Path(directory)/source.file_name(task,ext)
                    identity=source.download_verified(task,ext,path,opener)
                    if identity["sha256"]!=SOURCE_SHA[(task,ext)]:
                        raise source.SourceHashMismatch("G01_SOURCE_SHA256_NOT_REPRODUCED")
                    file_info[ext]={"bytes":identity["bytes"],"sha256":identity["sha256"],
                                    "original_annex_md5_confirmed":True}
                    local[ext]=path
                header_raw=local["vhdr"].read_bytes()
                header,names=source.parse_header(task,header_raw,local["eeg"].stat().st_size)
                if (len(names)!=N_CHANNELS or
                    header["source_header_number_of_channels"]!=N_CHANNELS or
                    header["source_header_rate_hz"]!=HZ or
                    header["source_binary_samples_per_channel"]!=N_FRAMES or
                    header["source_header_format"]!="IEEE_FLOAT_32"):
                    raise QcInstrumentError("PINNED_G01_HEADER_LAYOUT_CHANGED")
                metadata=parse_channel_metadata(header_raw)
                # mmap original 36.6 MB body, never report EEG sample arrays.
                eeg=np.memmap(local["eeg"],dtype="<f4",mode="r",
                              shape=(N_FRAMES,N_CHANNELS),order="C")
                stats=describe_original_samples(eeg)
                del eeg
                reports[task]={"verified_file_identity":file_info,
                               "source_header_details":metadata,
                               "sample_integrity":stats}
        flags=[reports[t]["sample_integrity"] for t in ("eyesclosed","eyesopen")]
        review_needed=any(
            q["nan_sample_count"] or q["positive_infinity_sample_count"] or
            q["negative_infinity_sample_count"] or
            q["channels_exactly_constant_full_record"] or
            q["ten_second_channel_epochs_exactly_constant"] or
            q["channels_with_undefined_relative_extreme_reference"]
            for q in flags
        )
        calibration_complete=all(
            reports[t]["source_header_details"]["header_calibration_complete"]
            for t in ("eyesclosed","eyesopen")
        )
        status=("SOURCE_NATIVE_NUMERIC_QC_REVIEW_REQUIRED" if review_needed else
                "SOURCE_SIGNAL_QC_CENSUS_COMPLETE" if calibration_complete else
                "SOURCE_NATIVE_NUMERIC_QC_CENSUS_COMPLETE_CALIBRATION_UNVERIFIED")
        result.update({"all_source_objects_authenticated":True,
                       "tasks":reports,
                       "total_original_float32_values_examined":2*TOTAL_PER_TASK,
                       "total_ten_second_channel_epochs_examined":2*EPOCH_CELLS,
                       "aggregate_source_qc_review_flags_present":bool(review_needed),
                       "calibrated_physical_amplitude_ready":calibration_complete,
                       "unit_calibration_status":("FULLY_DECLARED_NOT_HARDWARE_VERIFIED"
                         if calibration_complete else "NOT_ESTABLISHED"),
                       "decision":status})
    except source.SourceBlocked as exc:
        result.update(decision="SOURCE_RETRIEVAL_BLOCKED",error_code=str(exc))
    except source.SourceHashMismatch as exc:
        result.update(decision="ORIGINAL_SOURCE_HASH_MISMATCH",error_code=str(exc))
    except source.SourceLayoutError as exc:
        result.update(decision="RAW_LAYOUT_UNVERIFIED",error_code=str(exc))
    except QcInstrumentError as exc:
        result.update(decision="INSTRUMENT_FAILURE",error_code=str(exc))
    except Exception as exc:
        result.update(decision="INSTRUMENT_FAILURE",error_code=type(exc).__name__)
    return result


def main() -> None:
    outcome=run_source()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(outcome,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(outcome,indent=2,sort_keys=True),flush=True)
    if outcome["decision"]=="INSTRUMENT_FAILURE":
        raise SystemExit(1)


if __name__=="__main__":
    main()
