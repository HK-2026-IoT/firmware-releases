#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publish.py — Arduino IDE 빌드 후 한 줄로 OTA 배포 처리.

빌드된 firmware.ino.doitESP32devkitV1.bin 을 dist/<model>/<Model>.bin 으로
복사한 후 같은 폴더에 manifest.json 을 생성. make_release.py 의 로직을
재사용하며 .bin 복사 한 단계를 자동화.

사용법:
    python publish.py <model> <version>

예:
    python publish.py pwrflex 1.1.4
    python publish.py ga3     1.1.4
    python publish.py ah221   1.1.4

모델별로 한 번씩 Arduino IDE 빌드 후 이 명령 1줄 실행, 마지막에 git push.
한 사이클의 명령 수가 모델당 4줄에서 1줄로 감소.

전제 조건:
    - 이 스크립트는 firmware-releases/scripts/ 위치에 있어야 함 (make_release.py 와 동일)
    - 빌드된 .bin은 D:\\03_hk_git_code\\firmware\\firmware.ino.doitESP32devkitV1.bin
      위치에 있다고 가정 (Arduino IDE Export Compiled Binary 기본 경로)
"""

import hashlib
import json
import datetime
import shutil
import sys
from pathlib import Path

# 모델 -> .bin 파일명 매핑 (make_release.py 와 동일)
MODEL_BIN_MAP = {
    "ah221":   "AH221.bin",
    "ga3":     "GA3.bin",
    "pwrflex": "Pwrflex.bin",
}

# Arduino IDE Export Compiled Binary 산출물 (자기 환경에 맞게 조정)
SOURCE_BIN = Path(r"D:\03_hk_git_code\firmware\firmware.ino.doitESP32devkitV1.bin")

SCRIPT_DIR  = Path(__file__).resolve().parent
REPO_ROOT   = SCRIPT_DIR.parent
GITHUB_BASE = "https://raw.githubusercontent.com/HK-2026-IoT/firmware-releases/main/dist"

# 안전장치: dist/ 가 있어야 firmware-releases 위치가 맞음
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

    if not SOURCE_BIN.exists():
        print("[ERR] 빌드된 .bin 없음: " + str(SOURCE_BIN))
        print("      Arduino IDE 에서 Sketch -> Export Compiled Binary 후 다시 실행하세요.")
        return 1

    bin_name      = MODEL_BIN_MAP[model]
    dest_bin      = REPO_ROOT / "dist" / model / bin_name
    manifest_path = REPO_ROOT / "dist" / model / "manifest.json"

    # ── 1. .bin 복사 ─────────────────────────────────────────
    shutil.copyfile(SOURCE_BIN, dest_bin)
    print("[1/2] copied .bin")
    print("      " + str(SOURCE_BIN))
    print("      -> " + str(dest_bin))

    # ── 2. manifest.json 생성 ────────────────────────────────
    data = dest_bin.read_bytes()
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

    print("[2/2] wrote manifest.json")
    print("      model   = " + model)
    print("      version = " + version)
    print("      size    = " + format(size, ",") + " B")
    print("      sha256  = " + sha[:16] + "...")
    print()
    print("Next steps:")
    print("  - 다른 모델도 빌드 + publish.py 반복")
    print("  - 끝나면: git add dist/ && git commit -m \"release: v" + version + "\" && git push origin main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
