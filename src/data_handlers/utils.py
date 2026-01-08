import subprocess
from pathlib import Path
import json
import csv
import glob as globlib
import datetime


DATA_DIR = Path.home() / ".JobSearch"
if not DATA_DIR.exists():
    IS_NEW_USER = True
    DATA_DIR.mkdir()
else:
    IS_NEW_USER = False

def datetime_iso() -> str:
    return datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    

def resolve_paths(paths: list[str]) -> list[str]:
    resolved_paths = []
    for path in paths:
        if "*" in path:
            matched = globlib.glob(path)
            resolved_paths.extend(p for p in matched if Path(p).is_file())
        else:
            resolved_paths.append(path)
    return list(set(resolved_paths))

    
def combine_documents(paths: list[str]) -> str:
    doc_contents = []
    for path in resolve_paths(paths):
        try:
            with open(path, "r") as f:
                content = f.read()
                doc_contents.append(f"=== {path} ===\n{content}")
        except Exception as e:
            print(f"Warning: Could not read {path}: {e}")

    if doc_contents:
        return "\n\n".join(doc_contents)
    
    return ""
