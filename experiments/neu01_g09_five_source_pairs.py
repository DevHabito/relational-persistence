"""G09: first authenticated source-level direct IEEE check for five DERIVATIVE bodies.

Exactly five previously named participants/states, NO participant resampling,
no gain/shift/channel search, no raw EEG upload and no neural causal claim.
"""
from __future__ import annotations

import csv
from hashlib import md5, sha1, sha256
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

import numpy as np
from scipy.io import loadmat, whosmat

from experiments import neu01_g04_independent_replay as original
from experiments import neu01_g07_eeglab_pilot as one_derivative
from experiments import neu01_g08_fixed_pair as grid
from experiments import neu01_g08_d03_native_identity as ieee

PROTOCOL_COMMIT = "090efb85c4869ded1b968c9af883662a7eb0902d"
G08_D03_FIRST_SHA = "0a20ff8636afd7c90057fbd852c55864fd6192b9094dc7310680f40557e54e46"
G08_D03_FIRST = Path("docs/results/NEU-01-G08-D03-first-run/audit.json")
BIDS_TSV_SHA = "105960eb0ac14bae43bea73aa479a5c6d995c7a3"
BIDS_TSV_BYTES = 983
DERIV_BYTES = 73824136
FRAMES, CHANNELS = 150000, 61
S3_ROOT = "https://s3.amazonaws.com/openneuro.org/ds004148/"
OUTPUT = Path("docs/results/NEU-01-G09-P01-first-run/audit.json")
BLOCK=1024*1024
FIVE=(
    ("sub-02","eyesopen","EO","2e4f087c19643b88e59fc2f526bc12c8"),
    ("sub-03","eyesclosed","EC","d300eaa41f478a3f39c28a0d0ceb5198"),
    ("sub-03","eyesopen","EO","b93b201815edbc5cfe1cd030aa5bbf45"),
    ("sub-04","eyesclosed","EC","fc75f8e9015290d22510067d5a8e96bf"),
    ("sub-04","eyesopen","EO","d5b765994ba96c189030d5162b151e09"),
)


class SourceIneligible(Exception):
    """Published original object cannot be authenticated or parsed."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise SourceIneligible("SOURCE_REDIRECT_NOT_PERMITTED")


def check_immutable_first_evidence():
    ieee.verify_previous_evidence()
    grid.hash_archive(G08_D03_FIRST,1865,G08_D03_FIRST_SHA)
    prior=json.loads(G08_D03_FIRST.read_bytes())
    if (prior.get("status") != "EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL"
            or prior.get("direct_IEEE_comparison",{}).get("numeric_equal_count") != 9150000):
        raise SourceIneligible("ORIGINAL_G08_D03_SOURCE_IDENTITY_CHANGED")


def is_pair(subject:str, task:str, abbrev:str, published_md5:str)->bool:
    return (subject,task,abbrev,published_md5) in FIVE


def paths(subject:str,task:str,abbr:str,expected_md5:str)->dict:
    if not is_pair(subject,task,abbr,expected_md5):
        raise SourceIneligible("UNREGISTERED_FIVE_PAIR_SOURCE")
    id_number=subject.removeprefix("sub-")
    return {
        "header":f"{subject}/ses-session1/eeg/{subject}_ses-session1_task-{task}_eeg.vhdr",
        "channels":f"{subject}/ses-session1/eeg/{subject}_ses-session1_task-{task}_channels.tsv",
        "derivative":f"derivatives/preprocessed data/preprocessed_data/sub{id_number}_01_{abbr}.set",
    }


def read_original_tsv(relative:str, *, opener=urlopen)->bytes:
    if not any(relative==paths(*spec)["channels"] for spec in FIVE):
        raise SourceIneligible("UNREGISTERED_BIDS_CHANNEL_PATH")
    address=S3_ROOT+quote(relative,safe="/")
    request=Request(address,headers={"User-Agent":"RelationalPersistence-G09-ChannelTSV/1"})
    try:
        with opener(request,timeout=45) as response:
            if response.geturl()!=address:
                raise SourceIneligible("CHANNEL_TSV_REDIRECT_OR_WRONG_SOURCE")
            data=response.read(BIDS_TSV_BYTES+1)
    except (HTTPError,URLError,TimeoutError,OSError) as exc:
        raise SourceIneligible("ORIGINAL_CHANNEL_TSV_UNAVAILABLE") from exc
    if len(data)!=BIDS_TSV_BYTES or grid._git_blob_sha1(data)!=BIDS_TSV_SHA:
        raise SourceIneligible("CHANNEL_TSV_PUBLISHER_GIT_HASH_MISMATCH")
    return data


def ordered_original_header(raw_header:bytes, subject:str, task:str)->list[str]:
    original.header_audit(raw_header,subject,task)
    section=""
    names={}
    for line in raw_header.decode("latin-1").splitlines():
        s=line.strip()
        if s.startswith("[") and s.endswith("]"):
            section=s[1:-1].strip().casefold()
        elif section=="channel infos" and "=" in s:
            key,value=s.split("=",1)
            names[key.strip()]=grid.label(value.split(",",1)[0])
    if set(names)!={f"Ch{i}" for i in range(1,CHANNELS+1)}:
        raise SourceIneligible("BRAINVISION_CHANNEL_ORDER_INVALID")
    ordered=[names[f"Ch{i}"] for i in range(1,CHANNELS+1)]
    if len(set(ordered))!=CHANNELS:
        raise SourceIneligible("DUPLICATE_HEADER_CHANNEL_LABELS")
    return ordered


def derive_metadata(original_derivative:Path,
                    original_labels:list[str],bids_labels:list[str])->dict:
    manifest={name:(tuple(shape),kind) for name,shape,kind in whosmat(original_derivative)}
    if manifest.get("data")!=((CHANNELS,FRAMES),"double"):
        raise SourceIneligible("DERIVATIVE_MATLAB_DOUBLE_LAYOUT_NOT_ELIGIBLE")
    fields=loadmat(
        original_derivative,
        variable_names=["chanlocs","times","xmin","xmax","nbchan","pnts","trials","srate","ref"],
        squeeze_me=True,struct_as_record=False,verify_compressed_data_integrity=True,
    )
    derivative_labels=grid.extract_derivative_labels(fields.get("chanlocs"))
    def int_field(name):
        v=grid.clean_scalar(fields.get(name))
        return int(v) if v is not None and v.is_integer() and v>=0 else None
    ref=fields.get("ref")
    return grid.inspect_fixed_grid(
        original_labels,bids_labels,derivative_labels,
        fields.get("times"),fields.get("xmin"),fields.get("xmax"),
        rate=grid.clean_scalar(fields.get("srate")),
        n_channels=int_field("nbchan"),n_points=int_field("pnts"),
        n_trials=int_field("trials"),data_shape=manifest["data"][0],
        reference=ref if isinstance(ref,str) else None,
    )


def authenticate_derivative(subject:str,task:str,short:str,expected_md5:str,
                            destination:Path,*,opener=None)->dict:
    relative=paths(subject,task,short,expected_md5)["derivative"]
    url=S3_ROOT+quote(relative,safe="/")
    request=Request(url,headers={"User-Agent":"RelationalPersistence-G09-PublishedDerivative/1"})
    chosen=opener if opener is not None else build_opener(NoRedirects()).open
    h_md5,h_sha=md5(),sha256()
    count=0
    try:
        with chosen(request,timeout=45) as response,destination.open("xb") as dest:
            if response.geturl()!=url:
                raise SourceIneligible("WRONG_DERIVATIVE_RESPONSE_URL")
            while True:
                data=response.read(BLOCK)
                if not data:
                    break
                count+=len(data)
                if count>DERIV_BYTES:
                    raise SourceIneligible("DERIVATIVE_EXCEEDS_EXPECTED_SIZE")
                h_md5.update(data);h_sha.update(data);dest.write(data)
    except (HTTPError,URLError,TimeoutError,OSError) as exc:
        raise SourceIneligible("DERIVATIVE_OBJECT_NOT_ACCESSIBLE") from exc
    if count!=DERIV_BYTES:
        raise SourceIneligible("DERIVATIVE_SIZE_MISMATCH")
    if h_md5.hexdigest()!=expected_md5:
        raise SourceIneligible("DERIVATIVE_MD5_MISMATCH")
    return {"fully_authenticated_publisher_md5":True,
            "annex_expected_md5":expected_md5,
            "actual_sha256":h_sha.hexdigest(),
            "bytes":count,"source_body_published":False}


def evaluate_one(spec:tuple[str,str,str,str])->dict:
    subject,task,abbrev,expected_md5=spec
    target=paths(*spec)
    with TemporaryDirectory(prefix="neu01-g09-one-pair-no-outputs-") as directory:
        path=Path(directory)/"published-original.set"
        source_header=original.authenticated_bytes(subject,task,"vhdr")
        original_labels=ordered_original_header(source_header,subject,task)
        bids,units=grid.parse_bids_channel_labels(read_original_tsv(target["channels"]))
        derivative_identity=authenticate_derivative(*spec,destination=path)
        metadata=derive_metadata(path,original_labels,bids)
        if not metadata["metadata_gate_passed"]:
            return {"participant":subject,"task":task,
                    "status":"PAIR_GRID_METADATA_NOT_ELIGIBLE",
                    "derivative_source_identity":derivative_identity,
                    "metadata_gate":metadata,"bids_units":units,
                    "direct_IEEE_comparison":None,
                    "root_eeg_signal_read":False}
        root_bytes=original.authenticated_bytes(subject,task,"eeg")
        signal=np.frombuffer(root_bytes,dtype="<f4").reshape(FRAMES,CHANNELS).astype("<f8")
        matlab=loadmat(path,variable_names=["data"],squeeze_me=False,
                       verify_compressed_data_integrity=True)
        data=matlab.get("data")
        if (not isinstance(data,np.ndarray) or data.shape!=(CHANNELS,FRAMES)
                or data.dtype.kind!="f" or data.dtype.itemsize!=8):
            raise SourceIneligible("DERIVATIVE_SIGNAL_CLASS_OR_SHAPE_NOT_ELIGIBLE")
        result=ieee.inspect_direct_arrays(signal,np.asarray(data.T,dtype="<f8"))
        del root_bytes,signal,matlab,data
    return {"participant":subject,"task":task,
            "status":result["direct_identity_status"],
            "derivative_source_identity":derivative_identity,
            "metadata_gate":metadata,"bids_units":units,
            "direct_IEEE_comparison":result,
            "root_eeg_signal_read":True}


def run_original()->dict:
    check_immutable_first_evidence()
    results=[]
    for spec in FIVE:
        try:
            item=evaluate_one(spec)
        except (SourceIneligible,original.SourceFailure,ieee.SourceNotEligible,
                OSError,ValueError,TypeError,KeyError,NotImplementedError,MemoryError) as exc:
            item={"participant":spec[0],"task":spec[1],
                  "status":"PAIR_SOURCE_NOT_ELIGIBLE",
                  "error_type":type(exc).__name__,
                  "error_code":str(exc)[:145],
                  "direct_IEEE_comparison":None,
                  "root_eeg_signal_read":False}
        results.append(item)
    complete=all(item["status"] in (
        "EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL",
        "NUMERIC_EQUAL_IEEE_BITS_DIFFER",
        "AUTHENTICATED_NATIVE_ARRAYS_DIFFER",
    ) for item in results)
    return {
        "study":"NEU-01-G09-P01",
        "status":("FIVE_PAIR_DIRECT_IDENTITY_CENSUS_COMPLETE" if complete
                  else "FIVE_PAIR_ELIGIBILITY_INCOMPLETE"),
        "protocol_commit":PROTOCOL_COMMIT,
        "preexisting_G08_D03_one_pair_identity_known":True,
        "old_original_G08_D03_archive_sha256":G08_D03_FIRST_SHA,
        "publisher_dataset_revision":"0c740d838a2c33feeec0b6e514aea323d0e65ca4",
        "all_five_preselected_pairs_included":len(results)==5,
        "fixed_source_record_count":5,
        "first_original_five_pair_results":results,
        "number_exact_bitwise_identical_pairs":sum(
            x["status"]=="EXACT_WIDENED_NATIVE_ARRAYS_IDENTICAL" for x in results
        ),
        "number_numerically_different_pairs":sum(
            x["status"]=="AUTHENTICATED_NATIVE_ARRAYS_DIFFER" for x in results
        ),
        "one_original_prior_G08_D03_pair_separate":True,
        "new_participants_or_independent_human_sample":False,
        "causal_processing_stage_identified":False,
        "physical_units_calibration_verified":False,
        "source_amplitude_values_uploaded":False,
    }


def main():
    try:
        result=run_original()
    except (SourceIneligible,ieee.SourceNotEligible,ValueError,
            OSError,TypeError,KeyError,MemoryError) as exc:
        result={"study":"NEU-01-G09-P01","status":"SOURCE_NOT_ELIGIBLE",
                "protocol_commit":PROTOCOL_COMMIT,
                "error_type":type(exc).__name__,"error_code":str(exc)[:145]}
    result["source_amplitude_values_uploaded"]=False
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True),flush=True)
    if result["status"]!="FIVE_PAIR_DIRECT_IDENTITY_CENSUS_COMPLETE":
        raise SystemExit(2)


if __name__=="__main__":
    main()
