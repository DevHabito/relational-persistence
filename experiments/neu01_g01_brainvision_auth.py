"""NEU-01-G01: source-only BrainVision file authentication.

Protocol-only SHA aad92e9dbbc7518e1d0dac954683d024ee93d0f3
was committed BEFORE this code and any original header/EEG body inspection.

Only anonymous public original OpenNeuro S3 source objects are permitted.
No individual voltage, marker description, personal ID or full channel list
is written into output. This is NOT an LZc or mental-health experiment.
"""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from hashlib import md5, sha1, sha256
from io import StringIO
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROTOCOL_SHA = "aad92e9dbbc7518e1d0dac954683d024ee93d0f3"
SOURCE_COMMIT = "0c740d838a2c33feeec0b6e514aea323d0e65ca4"
ROOT = "https://s3.amazonaws.com/openneuro.org/ds004148/sub-01/ses-session1/eeg/"
BASENAME = "sub-01_ses-session1_task-"
CHANNELS_GIT_BLOB = "105960eb0ac14bae43bea73aa479a5c6d995c7a3"
OUTPUT = Path("docs/results/NEU-01-G01-first-run/audit.json")
MAX_OBJECT = 40 * 1024 * 1024
CHUNK = 1024 * 1024
SOURCE = {
    "eyesclosed": {
        "vhdr": (1122,"c5e313903936ef2fb9c1b3e0bfd61593"),
        "vmrk": (5960,"372402829a14249220eb8365f964d2de"),
        "eeg": (36600000,"0fceeb9eb4163b86b815061f8fff80d7"),
        "json_eeg_channel_count": 64,
    },
    "eyesopen": {
        "vhdr": (1118,"a5f9899c3cfa0c85f24c93c4eb83ef4c"),
        "vmrk": (5958,"df580c077add7e4a840b46585cf8499e"),
        "eeg": (36600000,"75e12c6499540e3148316ef502ad03dd"),
        "json_eeg_channel_count": 61,
    },
}
BIDS_TSV_CHANNEL_ROWS = 61
BIDS_RATE_HZ = Decimal(500)
BIDS_DURATION_SECONDS = Decimal(300)
CHANNEL_RE = re.compile(r"Ch([1-9][0-9]*)\Z")
MARKER_RE = re.compile(r"Mk([1-9][0-9]*)\Z")


class SourceBlocked(Exception):
    pass


class SourceHashMismatch(Exception):
    pass


class SourceLayoutError(Exception):
    pass


def file_name(task: str, ext: str) -> str:
    if task not in SOURCE or ext not in ("vhdr","vmrk","eeg","channels.tsv"):
        raise SourceLayoutError("UNREGISTERED_SOURCE_OBJECT")
    suffix = "channels.tsv" if ext == "channels.tsv" else "eeg."+ext
    return BASENAME+task+"_"+suffix


def original_https(task: str, ext: str) -> str:
    return ROOT+file_name(task,ext)


def blob_sha1(data: bytes) -> str:
    return sha1(b"blob "+str(len(data)).encode("ascii")+b"\x00"+data).hexdigest()


def download_verified(task: str, ext: str, path: Path, opener=urlopen) -> dict:
    """Bounded, streamed, hash-verifying download. No values from EEG exposed."""
    if task not in SOURCE or ext not in ("vhdr","vmrk","eeg"):
        raise SourceLayoutError("UNREGISTERED_SOURCE_OBJECT")
    expected_bytes, expected_md5 = SOURCE[task][ext]
    observed_size = 0
    hmd5, hsha = md5(), sha256()
    req = Request(original_https(task,ext),headers={"User-Agent":"RP-NEU01-G01-source-audit/1"})
    try:
        with opener(req,timeout=35) as response:
            with path.open("wb") as stream:
                while True:
                    part = response.read(CHUNK)
                    if not part:
                        break
                    observed_size += len(part)
                    if observed_size > min(MAX_OBJECT,expected_bytes):
                        raise SourceHashMismatch("SOURCE_BYTES_EXCEED_FROZEN_SIZE")
                    hmd5.update(part)
                    hsha.update(part)
                    stream.write(part)
    except SourceHashMismatch:
        raise
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise SourceBlocked("PUBLIC_ORIGINAL_OBJECT_NOT_RETRIEVED") from exc
    if observed_size != expected_bytes or hmd5.hexdigest() != expected_md5:
        raise SourceHashMismatch("ORIGINAL_ANNEX_MD5_OR_BYTE_SIZE_DIFFER")
    return {
        "task": task, "source_file_type": ext, "bytes": observed_size,
        "original_annex_md5_confirmed": True, "sha256": hsha.hexdigest(),
    }


def read_channels_tsv(task: str, opener=urlopen) -> tuple[list[str],dict]:
    """Text-only companion from the SAME fixed publisher S3 dataset version."""
    req=Request(original_https(task,"channels.tsv"),headers={
        "User-Agent":"RP-NEU01-G01-source-audit/1"
    })
    try:
        with opener(req,timeout=35) as response:
            data=response.read(65537)
    except (HTTPError,URLError,TimeoutError,OSError) as exc:
        raise SourceBlocked("PUBLIC_CHANNELS_TSV_NOT_RETRIEVED") from exc
    if len(data)>65536:
        raise SourceLayoutError("CHANNELS_TSV_TOO_LARGE")
    if blob_sha1(data)!=CHANNELS_GIT_BLOB:
        raise SourceHashMismatch("PUBLISHER_TSV_GIT_BLOB_DIFFERENT")
    try:
        table=csv.DictReader(StringIO(data.decode("utf-8-sig")),delimiter="\t")
        if table.fieldnames is None or "name" not in table.fieldnames:
            raise SourceLayoutError("TSV_CHANNEL_NAMES_MISSING")
        names=[r["name"] for r in table]
    except (UnicodeError,csv.Error,KeyError) as exc:
        raise SourceLayoutError("TSV_PARSE_FAILURE") from exc
    if len(names)!=61 or any(not v.strip() for v in names) or len(set(names))!=61:
        raise SourceLayoutError("TSV_LIST_NOT_61_UNIQUE_CHANNELS")
    return names,{"source_channels_tsv_git_blob_verified":True,
                  "tsv_channel_rows":len(names)}


def parse_sections(raw: bytes) -> dict[str,dict[str,str]]:
    try:
        content=raw.decode("latin-1")
    except UnicodeError as exc:
        raise SourceLayoutError("BRAINVISION_HEADER_ENCODING_UNSUPPORTED") from exc
    sections:dict[str,dict[str,str]]={}
    active=None
    for line in content.splitlines():
        line=line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            active=line[1:-1].lower()
            if active in sections:
                raise SourceLayoutError("DUPLICATE_BRAINVISION_SECTION")
            sections[active]={}
            continue
        if active is None:
            # Version label occurs above first section.
            if line.lower().startswith("brain vision data exchange"):
                continue
            raise SourceLayoutError("BRAINVISION_HEADER_NOT_RECOGNIZED")
        if "=" not in line:
            raise SourceLayoutError("MALFORMED_BRAINVISION_SECTION_LINE")
        key,value=line.split("=",1)
        key=key.strip()
        if not key or key in sections[active]:
            raise SourceLayoutError("BRAINVISION_KEY_INVALID_OR_DUPLICATE")
        sections[active][key]=value.strip()
    return sections


def must_exact_file(value: str|None, expected: str) -> None:
    if value is None or value.strip()!=expected or "/" in value or "\\" in value or ".." in value:
        raise SourceLayoutError("BRAINVISION_FILENAME_MISMATCH")


def parse_header(task:str, raw:bytes, original_eeg_bytes:int) -> tuple[dict,list[str]]:
    sections=parse_sections(raw)
    common=sections.get("common infos",{})
    binary=sections.get("binary infos",{})
    channels=sections.get("channel infos",{})
    must_exact_file(common.get("DataFile"),file_name(task,"eeg"))
    must_exact_file(common.get("MarkerFile"),file_name(task,"vmrk"))
    if common.get("DataFormat")!="BINARY" or common.get("DataOrientation")!="MULTIPLEXED":
        raise SourceLayoutError("BRAINVISION_ORIENTATION_OR_DATAFORMAT_UNSUPPORTED")
    try:
        num=int(common["NumberOfChannels"])
        interval=Decimal(common["SamplingInterval"])
    except (KeyError,ValueError,InvalidOperation) as exc:
        raise SourceLayoutError("BRAINVISION_COUNTS_OR_INTERVAL_MALFORMED") from exc
    if num<1 or num>256 or not interval.is_finite() or interval<=0:
        raise SourceLayoutError("BRAINVISION_CHANNEL_OR_RATE_INVALID")
    if Decimal(1000000)/interval!=BIDS_RATE_HZ:
        raise SourceLayoutError("BRAINVISION_SAMPLE_RATE_NOT_500_HZ")
    fmt=binary.get("BinaryFormat")
    if fmt not in ("IEEE_FLOAT_32","INT_16"):
        raise SourceLayoutError("BRAINVISION_BINARY_FORMAT_NOT_SUPPORTED")
    width=4 if fmt=="IEEE_FLOAT_32" else 2
    if original_eeg_bytes % (num*width):
        raise SourceLayoutError("BRAINVISION_EEG_BYTES_NOT_WHOLE_SAMPLES")
    samples=original_eeg_bytes//(num*width)
    duration=Decimal(samples)/BIDS_RATE_HZ
    if duration!=BIDS_DURATION_SECONDS:
        raise SourceLayoutError("BRAINVISION_DURATION_NOT_300_SECONDS")
    indexed=[]
    for key,value in channels.items():
        m=CHANNEL_RE.fullmatch(key)
        if m is None:
            raise SourceLayoutError("BRAINVISION_CHANNEL_KEY_MALFORMED")
        name=value.split(",",1)[0]
        if not name or name!=name.strip():
            raise SourceLayoutError("BRAINVISION_CHANNEL_NAME_MALFORMED")
        indexed.append((int(m.group(1)),name))
    indexed.sort()
    if [i for i,_ in indexed]!=list(range(1,num+1)):
        raise SourceLayoutError("BRAINVISION_CHANNEL_ORDINALS_NOT_CONTIGUOUS")
    names=[n for _,n in indexed]
    if len(names)!=len(set(names)):
        raise SourceLayoutError("BRAINVISION_DUPLICATE_CHANNEL_NAMES")
    return ({
        "source_header_number_of_channels":num,
        "source_header_sampling_interval_microseconds":str(interval),
        "source_header_rate_hz":int(BIDS_RATE_HZ),
        "source_header_format":fmt,
        "source_binary_samples_per_channel":samples,
        "source_binary_duration_seconds":int(duration),
    }, names)


def parse_markers(task:str,raw:bytes) -> dict:
    sections=parse_sections(raw)
    common=sections.get("common infos",{})
    must_exact_file(common.get("DataFile"),file_name(task,"eeg"))
    marks=sections.get("marker infos")
    if marks is None:
        raise SourceLayoutError("BRAINVISION_MARKER_SECTION_MISSING")
    indexed=[]
    for key,value in marks.items():
        match=MARKER_RE.fullmatch(key)
        if not match or not value:
            raise SourceLayoutError("BRAINVISION_MARKER_MALFORMED")
        indexed.append(int(match.group(1)))
    if sorted(indexed)!=list(range(1,len(indexed)+1)):
        raise SourceLayoutError("BRAINVISION_MARKERS_NOT_CONTIGUOUS")
    return {"marker_record_count":len(indexed)}


def inspect_original_pair(opener=urlopen) -> dict:
    findings={}
    file_hashes=[]
    with TemporaryDirectory(prefix="neu01-g01-") as directory:
        root=Path(directory)
        for task in ("eyesclosed","eyesopen"):
            paths={}
            for ext in ("vhdr","vmrk","eeg"):
                path=root/file_name(task,ext)
                result=download_verified(task,ext,path,opener)
                file_hashes.append(result)
                paths[ext]=path
            names_tsv,tsv_status=read_channels_tsv(task,opener)
            header,names=parse_header(task,paths["vhdr"].read_bytes(),paths["eeg"].stat().st_size)
            markers=parse_markers(task,paths["vmrk"].read_bytes())
            if names!=names_tsv:
                raise SourceLayoutError("ACTUAL_HEADER_CHANNELS_DIFFER_FROM_TSV")
            findings[task]={
                **header,**markers,**tsv_status,
                "header_to_tsv_names_exactly_equal":True,
                "bids_json_eeg_channel_count":SOURCE[task]["json_eeg_channel_count"],
                "bids_json_channel_count_agrees_with_vhdr":
                    SOURCE[task]["json_eeg_channel_count"]==header["source_header_number_of_channels"],
            }
    return {
        "original_files":file_hashes,
        "tasks":findings,
        "channel_intersection_count":len(set(names_tsv)), # overwritten below
    }


def evaluate(opener=urlopen) -> dict:
    result={
        "study":"NEU-01-G01",
        "protocol_only_commit":PROTOCOL_SHA,
        "source_dataset_git_commit":SOURCE_COMMIT,
        "source_openneuro_version":"1.0.0",
        "source_route":"OpenNeuro official anonymous S3",
        "original_eeg_samples_or_markers_published":False,
        "lzc_computed":False,
        "psychiatric_biomarker_tested":False,
        "decision":"INSTRUMENT_FAILURE",
    }
    try:
        checked=inspect_original_pair(opener)
        result.update({
            "original_files":checked["original_files"],
            "task_header_vs_sidecar":checked["tasks"],
            "all_original_annex_keys_authenticated":True,
            "decision":"ORIGINAL_BRAINVISION_PAIR_AUTHENTICATED",
        })
    except SourceBlocked as exc:
        result.update(decision="SOURCE_RETRIEVAL_BLOCKED",error_code=str(exc))
    except SourceHashMismatch as exc:
        result.update(decision="ORIGINAL_SOURCE_HASH_MISMATCH",error_code=str(exc))
    except SourceLayoutError as exc:
        result.update(decision="BRAINVISION_LAYOUT_NOT_VERIFIED",error_code=str(exc))
    except Exception as exc:
        result.update(decision="INSTRUMENT_FAILURE",error_code=type(exc).__name__)
    return result


def main() -> None:
    result=evaluate()
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True,indent=2),flush=True)


if __name__=="__main__":
    main()
