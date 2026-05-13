import os
import re


def remove_dates(path="audio"):
    """Remove date-like parenthesized groups (e.g. "(07 08 24)") from filenames.

    - Operates on `path` (default `audio/`). If `path` doesn't exist, returns empty dict.
    - Recurses into all subdirectories.
    - Only processes common audio file extensions.
    - Avoids overwriting existing files by adding an "_1", "_2" suffix when needed.
    - Returns a dict mapping original names -> new names for renamed files.
    """
    if not os.path.exists(path):
        print(f"Directory not found: {path!s}")
        return {}

    date_re = re.compile(r"\s*\(\s*\d{1,2}\s+\d{1,2}\s+\d{2,4}\s*\)\s*")
    collapse_spaces = re.compile(r"\s{2,}")

    renamed = {}
    audio_exts = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.opus'}

    for root, dirs, files in os.walk(path):
        for filename in files:
            _, ext = os.path.splitext(filename)
            if ext.lower() not in audio_exts:
                continue

            src = os.path.join(root, filename)
            new_filename = date_re.sub(" ", filename).strip()
            new_filename = collapse_spaces.sub(" ", new_filename)
            # Remove trailing spaces before extension
            name, ext = os.path.splitext(new_filename)
            new_filename = name.rstrip() + ext
            if not new_filename or new_filename == filename:
                continue

            dest = os.path.join(root, new_filename)
            if os.path.exists(dest):
                base, ext = os.path.splitext(new_filename)
                i = 1
                while True:
                    candidate = f"{base}_{i}{ext}"
                    dest = os.path.join(root, candidate)
                    if not os.path.exists(dest):
                        new_filename = candidate
                        break
                    i += 1

            os.rename(src, dest)
            renamed[filename] = new_filename
            print(f"Renamed: {filename} -> {new_filename}")

    return renamed

def addEvil():
    for file in os.listdir("audio/evil"):
        if not file.endswith("(Evil) .mp3"):
            os.rename(
                os.path.join("audio/evil", file),
                os.path.join("audio/evil", file.replace(".mp3", " (Evil) .mp3"))
            )
def addNeuro():
    for file in os.listdir("audio/neuro"):
        if not file.endswith("(Neuro) .mp3"):
            os.rename(
                os.path.join("audio/neuro", file),
                os.path.join("audio/neuro", file.replace(".mp3", " (Neuro) .mp3"))
            )
def addDuet():
    for file in os.listdir("audio/duet"):
        if not file.endswith("(Duet) .mp3"):
            os.rename(
                os.path.join("audio/duet", file),
                os.path.join("audio/duet", file.replace(".mp3", " (Duet) .mp3"))
            )



if __name__ == "__main__":
    addEvil()
    addNeuro()
    addDuet()
    changed = remove_dates()
    print(f"Total renamed: {len(changed)}")
