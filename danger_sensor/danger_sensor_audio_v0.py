# danger_sensor_v0.py
# Danger Sensor v0 (Audio/Text) - CUT / HOLD / PASS
# - Audio: WAV -> metrics -> decision
# - Text : spec/email/contract text -> metrics -> decision
#
# Usage (PowerShell):
#   # Audio
#   python .\danger_sensor_v0.py audio .\input.wav --print-metrics
#
#   # Text (direct)
#   python .\danger_sensor_v0.py text --text "ケースバイケースで最適化します"
#
#   # Text (file)
#   python .\danger_sensor_v0.py text --text-file .\spec.txt
#
#   # Output files
#   python .\danger_sensor_v0.py audio .\input.wav --json-out .\result.json --audit-out .\audit.json

from __future__ import annotations

import argparse
import json
import math
import os
import re
import struct
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np


# ============================
# WAV decoding (minimal, robust)
# ============================

@dataclass
class WavInfo:
    sr: int
    channels: int
    sampwidth_bytes: int
    is_float: bool
    num_frames: int


def _read_u32_le(b: bytes, off: int) -> int:
    return struct.unpack_from("<I", b, off)[0]


def _read_u16_le(b: bytes, off: int) -> int:
    return struct.unpack_from("<H", b, off)[0]


def _decode_wav_to_mono_f32(path: str) -> Tuple[np.ndarray, WavInfo]:
    with open(path, "rb") as f:
        data = f.read()

    if len(data) < 44 or data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("Not a RIFF/WAVE file")

    off = 12
    fmt_chunk = None
    data_chunk = None

    while off + 8 <= len(data):
        chunk_id = data[off:off+4]
        chunk_size = _read_u32_le(data, off+4)
        chunk_data_off = off + 8
        chunk_data_end = chunk_data_off + chunk_size
        if chunk_data_end > len(data):
            break

        if chunk_id == b"fmt ":
            fmt_chunk = data[chunk_data_off:chunk_data_end]
        elif chunk_id == b"data":
            data_chunk = data[chunk_data_off:chunk_data_end]

        off = chunk_data_end + (chunk_size & 1)

    if fmt_chunk is None or data_chunk is None:
        raise ValueError("Missing fmt or data chunk")

    audio_format = _read_u16_le(fmt_chunk, 0)  # 1=PCM, 3=float, 0xFFFE=extensible
    channels = _read_u16_le(fmt_chunk, 2)
    sr = _read_u32_le(fmt_chunk, 4)
    block_align = _read_u16_le(fmt_chunk, 12)
    bits_per_sample = _read_u16_le(fmt_chunk, 14)

    if channels < 1 or sr < 8000:
        raise ValueError("Invalid WAV header (channels/sr)")

    is_float = False
    sampwidth = bits_per_sample // 8

    # extensible
    if audio_format == 0xFFFE and len(fmt_chunk) >= 40:
        subformat = _read_u16_le(fmt_chunk, 24)
        audio_format = subformat

    if audio_format == 3:
        is_float = True
    elif audio_format == 1:
        is_float = False
    else:
        raise ValueError(f"Unsupported WAV format code: {audio_format}")

    bytes_per_frame = block_align
    if bytes_per_frame <= 0:
        raise ValueError("Invalid block_align")
    num_frames = len(data_chunk) // bytes_per_frame

    # decode
    if is_float:
        if bits_per_sample == 32:
            arr = np.frombuffer(data_chunk, dtype="<f4")
        elif bits_per_sample == 64:
            arr = np.frombuffer(data_chunk, dtype="<f8").astype(np.float32)
        else:
            raise ValueError(f"Unsupported float depth: {bits_per_sample}")
    else:
        if bits_per_sample == 16:
            arr = np.frombuffer(data_chunk, dtype="<i2").astype(np.float32) / 32768.0
        elif bits_per_sample == 24:
            raw = np.frombuffer(data_chunk, dtype=np.uint8).reshape(-1, 3)
            x = (raw[:, 0].astype(np.int32) |
                 (raw[:, 1].astype(np.int32) << 8) |
                 (raw[:, 2].astype(np.int32) << 16))
            sign = (x & 0x800000) != 0
            x = x | (sign.astype(np.int32) * 0xFF000000)
            arr = x.astype(np.float32) / 8388608.0
        elif bits_per_sample == 32:
            arr = np.frombuffer(data_chunk, dtype="<i4").astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Unsupported PCM depth: {bits_per_sample}")

    if arr.size % channels != 0:
        arr = arr[: (arr.size // channels) * channels]

    arr = arr.reshape(-1, channels)
    mono = arr.mean(axis=1).astype(np.float32)

    info = WavInfo(
        sr=sr,
        channels=channels,
        sampwidth_bytes=sampwidth,
        is_float=is_float,
        num_frames=mono.shape[0],
    )
    return mono, info


# ============================
# Audio metrics
# ============================

def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x * x) + 1e-12))


def _db(x: float) -> float:
    return 20.0 * math.log10(max(x, 1e-12))


def _spectral_flatness(mag: np.ndarray) -> float:
    mag = np.maximum(mag, 1e-12)
    gm = float(np.exp(np.mean(np.log(mag))))
    am = float(np.mean(mag))
    return float(gm / max(am, 1e-12))


def _stft_mag(x: np.ndarray, n_fft: int, hop: int) -> np.ndarray:
    if x.size < n_fft:
        x = np.pad(x, (0, n_fft - x.size))
    n_frames = 1 + (x.size - n_fft) // hop if x.size >= n_fft else 1
    mags = []
    win = np.hanning(n_fft).astype(np.float32)
    for i in range(n_frames):
        s = i * hop
        frame = x[s:s+n_fft]
        if frame.size < n_fft:
            frame = np.pad(frame, (0, n_fft - frame.size))
        spec = np.fft.rfft(frame * win)
        mags.append(np.abs(spec).astype(np.float32))
    return np.stack(mags, axis=0)


def inspect_audio_v0(audio: np.ndarray, sr: int) -> Tuple[Dict[str, Any], Dict[str, float]]:
    x = audio.astype(np.float32)
    if x.size == 0:
        raise ValueError("Empty audio")

    dur_sec = float(x.size) / float(sr)

    clip_thr = 0.999
    clip_rate = float(np.mean(np.abs(x) >= clip_thr))

    # true-peak proxy (x4)
    up = 4
    t = np.arange(x.size, dtype=np.float32)
    ti = np.linspace(0, x.size - 1, x.size * up, dtype=np.float32)
    x_up = np.interp(ti, t, x).astype(np.float32)
    tp = float(np.max(np.abs(x_up)))
    tp_dbfs = _db(tp)

    peak = float(np.max(np.abs(x)))
    rms = _rms(x)
    crest_db = _db(peak / max(rms, 1e-12))

    # dropouts
    silence_thr = 1e-4
    min_gap = int(sr * 0.030)
    is_silent = (np.abs(x) < silence_thr)
    dropout_count = 0
    run = 0
    for v in is_silent:
        if v:
            run += 1
        else:
            if run >= min_gap:
                dropout_count += 1
            run = 0
    if run >= min_gap:
        dropout_count += 1

    # HF ratio + flatness + ZCR
    n_fft = 2048
    hop = 512
    mags = _stft_mag(x, n_fft=n_fft, hop=hop)
    freqs = np.fft.rfftfreq(n_fft, d=1.0/sr).astype(np.float32)

    lo = 50.0
    hf = 5000.0
    band_total = mags[:, (freqs >= lo)].sum(axis=1) + 1e-12
    band_hf = mags[:, (freqs >= hf)].sum(axis=1)
    hf_ratio = float(np.median(band_hf / band_total))

    flat = float(np.median([_spectral_flatness(m[1:]) for m in mags]))

    zc = float(np.mean(x[1:] * x[:-1] < 0.0))
    zcr = zc * sr

    # transient density
    frame = max(int(sr * 0.010), 16)
    xx = x * x
    kernel = np.ones(frame, dtype=np.float32) / float(frame)
    rms_env = np.sqrt(np.convolve(xx, kernel, mode="same") + 1e-12)

    k = 6.0
    trans = (np.abs(x) > (k * rms_env))
    debounce = int(sr * 0.005)
    transient_events = 0
    i = 0
    while i < trans.size:
        if trans[i]:
            transient_events += 1
            i += debounce
        else:
            i += 1
    transient_density = float(transient_events / max(dur_sec, 1e-9))

    metrics = {
        "duration_sec": dur_sec,
        "clip_rate": clip_rate,
        "true_peak_dbfs_proxy": tp_dbfs,
        "crest_db": crest_db,
        "dropout_count": float(dropout_count),
        "hf_ratio": hf_ratio,
        "spectral_flatness": flat,
        "zcr_per_sec": float(zcr),
        "transient_density_per_sec": transient_density,
    }

    # decision rules
    reasons = []
    if clip_rate > 0.001:
        reasons.append("CLIPPING")
    if tp_dbfs > -0.3:
        reasons.append("TRUE_PEAK_RISK")
    if dropout_count > 0:
        reasons.append("DROPOUTS")

    if reasons:
        return {"decision": "CUT", "reasons": reasons}, metrics

    suspicious = []
    if flat > 0.25 and hf_ratio > 0.25:
        suspicious.append("DIGITAL_HF_FLAT")
    if transient_density > 40.0:
        suspicious.append("TRANSIENT_OVERDENSE")
    if crest_db < 6.0:
        suspicious.append("OVERCOMPRESSED")

    if suspicious:
        return {"decision": "HOLD", "reasons": suspicious}, metrics

    return {"decision": "PASS", "reasons": []}, metrics


# ============================
# Text spec sensor (your logic)
# ============================

KW_AMBIGUOUS = [
    r"ケースバイケース", r"柔軟", r"最適化", r"AIで", r"現場次第",
    r"よしなに", r"状況に応じて", r"ベストエフォート", r"検討"
]
KW_NUMERIC = [
    r"\d+ms", r"\d+dB", r"\d+%", r"\d+Hz", r"SLA", r"MTBF",
    r"閾値", r"スループット", r"レイテンシ", r"稼働率"
]
KW_RESPONSIBILITY = [
    r"保証", r"範囲", r"除外", r"復旧", r"監視", r"責任", r"合意", r"仕様"
]


def inspect_text_v0(text: str) -> Tuple[Dict[str, Any], Dict[str, float]]:
    if not text:
        return {"decision": "CUT", "reasons": ["EMPTY_TEXT"]}, {}

    L = len(text)

    count_amb = sum(len(re.findall(p, text)) for p in KW_AMBIGUOUS)
    rate_amb = count_amb / max(L, 1.0) * 1000.0

    count_num = sum(len(re.findall(p, text, re.IGNORECASE)) for p in KW_NUMERIC)
    has_numeric = count_num > 0

    count_resp = sum(len(re.findall(p, text)) for p in KW_RESPONSIBILITY)
    has_resp = count_resp > 0

    metrics = {
        "text_len": float(L),
        "ambiguity_score": float(rate_amb),
        "numeric_count": float(count_num),
        "responsibility_count": float(count_resp),
    }

    reasons = []
    if rate_amb > 2.0 and not has_numeric:
        reasons.append("POEM_SPEC_RISK")
    if L < 10:
        reasons.append("TOO_SHORT")

    if reasons:
        return {"decision": "CUT", "reasons": reasons}, metrics

    if has_numeric and not has_resp:
        return {"decision": "HOLD", "reasons": ["NUMBERS_WITHOUT_CONTRACT"]}, metrics

    if has_resp and not has_numeric:
        return {"decision": "HOLD", "reasons": ["CONTRACT_WITHOUT_NUMBERS"]}, metrics

    return {"decision": "PASS", "reasons": []}, metrics


# ============================
# Unified entry
# ============================

def inspect_fn(req: Dict[str, Any], audio_path: Optional[str] = None, text: Optional[str] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if audio_path:
        x, info = _decode_wav_to_mono_f32(audio_path)
        result_obj, metrics = inspect_audio_v0(x, info.sr)
        audit_log = {
            "version": "danger_sensor_v0",
            "kind": "audio",
            "input": {
                "path": os.path.abspath(audio_path),
                "sr": info.sr,
                "channels": info.channels,
                "frames": info.num_frames,
                "is_float_wav": info.is_float,
            },
            "metrics": metrics,
            "req": dict(req),
        }
        out = {**result_obj, "metrics": metrics}
        return out, audit_log

    if text is not None:
        result_obj, metrics = inspect_text_v0(text)
        audit_log = {
            "version": "danger_sensor_v0",
            "kind": "text",
            "input": {"text_len": len(text)},
            "metrics": metrics,
            "req": dict(req),
        }
        out = {**result_obj, "metrics": metrics}
        return out, audit_log

    raise ValueError("Provide either audio_path or text")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    # audio
    ap_a = sub.add_parser("audio", help="Scan WAV")
    ap_a.add_argument("wav", help="Path to input WAV")

    # text
    ap_t = sub.add_parser("text", help="Scan text")
    ap_t.add_argument("--text", default=None, help="Text to scan")
    ap_t.add_argument("--text-file", default=None, help="Path to UTF-8 text file to scan")

    # shared
    ap.add_argument("--json-out", default=None, help="Write result JSON to file")
    ap.add_argument("--audit-out", default=None, help="Write audit JSON to file")
    ap.add_argument("--print-metrics", action="store_true", help="Print metrics table")

    args = ap.parse_args()

    req = {"mode": "v0"}

    try:
        if args.cmd == "audio":
            if not os.path.exists(args.wav):
                print(f"[ERR] Not found: {args.wav}", file=sys.stderr)
                sys.exit(2)
            result, audit = inspect_fn(req, audio_path=args.wav)

        elif args.cmd == "text":
            t = args.text
            if args.text_file:
                with open(args.text_file, "r", encoding="utf-8") as f:
                    t = f.read()
            if t is None:
                print("[ERR] Provide --text or --text-file", file=sys.stderr)
                sys.exit(2)
            result, audit = inspect_fn(req, text=t)

        else:
            raise ValueError("Unknown cmd")

    except Exception as e:
        print(f"[ERR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.print_metrics:
        m = result.get("metrics", {})
        print("\n--- metrics ---")
        for k in sorted(m.keys()):
            print(f"{k:28s} : {m[k]}")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    if args.audit_out:
        with open(args.audit_out, "w", encoding="utf-8") as f:
            json.dump(audit, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
