import os

# путь к pyjnius в .buildozer
p = ".buildozer/android/platform/build-arm64-v8a/build/other_builds/pyjnius/arm64-v8a__ndk_target_21/pyjnius/jnius_utils.pxi"

if os.path.exists(p):
    with open(p, "r+") as f:
        text = f.read()
        if "long = int" not in text:
            f.seek(0, 0)
            f.write("try:\n    long\nexcept NameError:\n    long = int\n\n" + text)
