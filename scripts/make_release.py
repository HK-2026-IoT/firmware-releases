#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_release.py — AH221/GA3/PWRFLEX 공통 OTA manifest 생성기.

자기 위치(firmware-releases/scripts/)를 기준으로 REPO_ROOT 자동 인식.
PC가 바뀌어도 그대로 동작.

사용법:
    python make_release.py <model> <version>
예:
    python make_release.py pwrflex 1.1.4
    python make_release.py ah221   1.1.0
"""

import hashlib
import json
import datetime
import sys
from pathlib import Path

# 모델 -> .bin 파일명 매핑. PWRFLEX만 Title Case, 나머지는 대문자.
MODEL_BIN_MAP = {
    "ah221":   "AH221.bin",
    "ga3":     "GA3.bin",
    "pwrflex": "Pwrflex.bin",
}

SCRIPT_DIR  = Path(__file__).resolve().parent
REPO_ROOT   = SCRIPT_DIR.parent
GITHUB_BASE = "https://raw.githubusercontent.com/HK-2026-IoT/firmware-releases/main/dist"

# 안전장치: dist/가 있어야 firmware-releases 레포 위치가 맞음
if not (REPO_ROOT / "dist").exists():
    print("[ERR] dist/ folder not found at: " + str(REPO_ROOT))
    print("      이 스크립트는 firmware-releases/scripts/ 안에서 실행되어야 합니다.")
    sys.exit(1)


def usage_and_exit(msg=""):
    if msg:
        print("[ERR] " + msg + "\n")
    print(__doc__)
    print("지원 모델: " + ", ".join(MODEL_BIN_MAP.keys()))
    sys.exit(1)


def main():
    if len(sys.argv) != 3:
        usage_and_exit("인자 수가 잘못됐습니다. <model> <version> 두 개 필요")

    model   = sys.argv[1].lower().strip()
    version = sys.argv[2].strip()

    if model not in MODEL_BIN_MAP:
        usage_and_exit("알 수 없는 모델: " + model)

    bin_name      = MODEL_BIN_MAP[model]
    bin_path      = REPO_ROOT / "dist" / model / bin_name
    manifest_path = REPO_ROOT / "dist" / model / "manifest.json"

    if not bin_path.exists():
        print("[ERR] .bin 파일 없음: " + str(bin_path))
        print("      먼저 Arduino IDE 빌드 후 dist/" + model + "/" + bin_name + " 으로 복사하세요.")
        return 1

    data = bin_path.read_bytes()
    sha  = hashlib.sha256(data).hexdigest()
    size = len(data)

    now_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest = {
        "model":                  model,
        "version":                version,
        "url":                    GITHUB_BASE + "/" + model + "/" + bin_name,
        "sha256":                 sha,
        "size_bytes":             size,
        "released_at":            now_iso,
        "min_bootloader_version": "1.0.0",
        "notes":                  model + " v" + version + " release",
        "rollback_allowed":       True,
    }

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print("[OK] wrote " + str(manifest_path))
    print("     model   = " + model)
    print("     version = " + version)
    print("     size    = " + format(size, ",") + " B")
    print("     sha256  = " + sha)
    print("     url     = " + manifest["url"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
