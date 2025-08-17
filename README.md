# Lotto Recommender (Android / Kivy + Buildozer)

이 패키지는 안드로이드용 APK를 바로 빌드할 수 있도록 준비된 템플릿입니다.
엑셀 없이 내장 저장소(JSON) + 빈도 기반 가중 랜덤 알고리즘(α, β, 최근 K회)으로
'Play'를 누르면 6개 번호 × 5세트를 생성합니다.

## 파일 구성
- `main.py` : 앱 메인 소스 (Kivy)
- `buildozer.spec` : Buildozer 설정 파일
- `lotto.kv` : (옵션) Kivy KV 레이아웃 (현재는 main.py 내 KV 정의가 포함되어 있어 없어도 동작)

## 요구사항
- Linux/WSL2/macOS 권장
- Python 3.10± (안정 버전), Java JDK 17
- Buildozer

## 설치
```bash
sudo apt update
sudo apt install -y git python3 python3-pip build-essential     openjdk-17-jdk unzip zip libffi-dev libssl-dev     libsqlite3-dev zlib1g-dev
pip install --upgrade pip
pip install buildozer
```

## 빌드
```bash
cd lotto_android
buildozer android debug
```
완료 후 `bin/` 폴더에 `*.apk` 생성됩니다.

## 기기에 설치/실행 (선택)
```bash
buildozer android deploy run
```

## 권한
CSV 내보내기를 위해 외부 저장소 권한(READ/WRITE_EXTERNAL_STORAGE)을 설정했습니다.
Android 10+에서는 Download 폴더 접근이 제한될 수 있어, 앱 내부 저장소 사용을 우선 시도합니다.

## 참고
- 본 앱은 무작위 추첨 특성상 '정확 예측'을 보장하지 않습니다. 통계적 추천 도구입니다.