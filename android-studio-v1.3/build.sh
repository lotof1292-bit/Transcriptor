#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
: "${STUDIO_SDK:?Define STUDIO_SDK con la ruta al Android SDK}"
: "${STUDIO_KEYSTORE:?Define STUDIO_KEYSTORE con un almacén propio de firma}"
: "${STUDIO_KEY_ALIAS:?Define STUDIO_KEY_ALIAS}"
: "${STUDIO_STORE_PASSWORD:?Define STUDIO_STORE_PASSWORD}"
bt="$STUDIO_SDK/build-tools/35.0.0"
platform="$STUDIO_SDK/platforms/android-35/android.jar"
mkdir -p classes dex
java com.sun.tools.javac.Main -source 8 -target 8 -classpath "$platform" -d classes src/mx/transcriptor/studio/*.java
python3 - <<'PY'
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
with ZipFile('assets/sources.zip','w',ZIP_DEFLATED) as z:
 for directory in ['src','server','tests','res']:
  for p in Path(directory).rglob('*'):
   if p.is_file() and '__pycache__' not in str(p) and p.name!='server-token.txt':z.write(p,str(p))
 z.write('assets/index.html','assets/index.html')
 for name in ['README.md','AndroidManifest.xml','build.sh','package.json']:z.write(name,name)
PY
"$bt/aapt" package -f -M AndroidManifest.xml -I "$platform" -S res -A assets -F unsigned.apk
"$bt/d8" --lib "$platform" --min-api 26 --output dex classes/mx/transcriptor/studio/*.class
python3 - <<'PY'
from zipfile import ZipFile
with ZipFile('unsigned.apk','a') as z:z.write('dex/classes.dex','classes.dex')
PY
"$bt/zipalign" -f 4 unsigned.apk aligned.apk
"$bt/apksigner" sign --ks "$STUDIO_KEYSTORE" --ks-key-alias "$STUDIO_KEY_ALIAS" --ks-pass env:STUDIO_STORE_PASSWORD --out Transcriptor-Studio-v1.3.apk aligned.apk
"$bt/apksigner" verify --verbose Transcriptor-Studio-v1.3.apk
