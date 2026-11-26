#!/usr/bin/env python3
"""Export only approved public files; exclude operational data and Git metadata."""
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from publication import audit, public_files

ROOT = Path(__file__).resolve().parents[1]


def main():
    if audit(ROOT):
        raise SystemExit('Publication checks failed; no package created.')
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    archive = out / 'wordpress-vps-migration.zip'
    files = public_files(ROOT)
    with ZipFile(archive, 'w', compression=ZIP_DEFLATED, compresslevel=9) as bundle:
        for p in files:
            bundle.write(p, 'wordpress-vps-migration/' + p.relative_to(ROOT).as_posix())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (out / 'wordpress-vps-migration.zip.sha256').write_text(digest + '  ' + archive.name + '\n')
    print(f'Public package: {archive.name}; {len(files)} files; SHA-256 {digest}')


if __name__ == '__main__':
    main()
