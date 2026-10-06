# CLAUDE.md

Notes for working on `project-archiver` (`archiver` CLI): packs research project
directories into md5-hashed, plzip-compressed, optionally split and gpg-encrypted
tar archives, and checks/extracts/lists them later. Long-lived tool: dependencies
are deliberately minimal (only `multiprocessing-logging`; `coloredlogs` optional).
Supports Python >= 3.8 (CI: 3.8/3.9/3.12 on ubuntu-22.04; the cluster env uses 3.9), so avoid newer syntax.

## Commands

```sh
python3 -m pytest tests/ -s          # full suite (needs plzip, tar, gpg, jdupes on PATH)
python3 -m pytest tests/features/test_archive.py -k split
python -m archiver.main <subcommand> ...   # how the tests invoke the CLI (tests/helpers.py:run_archiver_tool)
```

Test baseline (2026-10-05, maintainer's mac): all 111 tests pass.
- The subprocess-based tests (`test_end_to_end`, `test_create_archive_split_granular`) need
  `multiprocessing_logging` installed for the plain `python` on PATH.
- Test keys live in `tests/test-ressources/encryption-keys/`. All are dummy RSA-3072 keys without a passphrase or expiry:
  `public.gpg`/`private.gpg` ("Archiving Tester", the key used for decryption via the `setup_gpg` fixture, which sets
  `GNUPGHOME=/tmp/archiving`) and `public_second.pub`/`private_second.gpg` ("Archiving Tester Second",
  regenerated 2026-10-05 after the old key expired). Encryption tests encrypt to both public keys
  (`archiving_helpers.get_public_key_paths`), so if a key expires, every encryption test fails with "Unusable public key".
- When generating gpg keys, use a short GNUPGHOME such as `mktemp -d /tmp/gpgtk.XXXX`, because long paths break the agent socket.
  Pin RSA explicitly, because gpg 2.5 defaults may not be readable by CI's gpg 2.2.
- macOS has bsdtar, while CI uses GNU tar. The listing parser handles both formats.

Installing: always use pip (`pip install .`, or `pip install -e .` for development). The package metadata is in
`setup.py`, and `pyproject.toml` only declares the build system, so even old pip versions use PEP 517/660. Without it,
pip <= 23.0 fell back to `setup.py develop`. That route keeps the metadata in the checkout's `*.egg-info`, and
`make clean` deletes it, which gives `PackageNotFoundError: project-archiver` (happened on the cluster in 2026-10).
`pip install -e .` needs pip >= 21.3; regular installs work with any pip. Don't use `python setup.py install`: with
setuptools >= 80 it skips the dependencies.

## Layout

- `archiver/main.py`: argparse CLI plus `handle_*` functions. Subcommands: `archive`,
  `create {filelist,tar,compressed-tar}` (step-by-step pipeline for large archives),
  `encrypt`, `decrypt`, `extract`, `list`, `check` (exit code 3 when the integrity check fails),
  `preparation-checks`.
- `archive.py`: creation pipeline. `create_archive` runs
  `create_filelist_and_hashes`, then `_process_part` (tar, tar.md5, tar.lst) for each part via `exec_parallel`,
  then `compress_and_hash` (plzip runs **sequentially** per part, each part with N threads; the .tar.lz.md5 hashes are computed in parallel),
  then optional encryption.
- `splitter.py`: `split_directory()` is a generator yielding `(archive_paths, listing_paths)` per part.
  It walks with os.walk. A whole subdirectory goes into the current part if it fits (sized with `du`) and is then pruned
  from the walk. Otherwise the directory entry goes into the listing and the walk descends into it.
  A file that doesn't fit starts a new part. A file larger than part-size is allowed only if `<= max_single_size`, otherwise
  `ValueError`. Both bounds are inclusive (commit 99b1d16).
- `helpers.py`: hashing, file walking, size parsing (`get_bytes_in_string_with_unit`, binary
  units: K/M/G/T = 2^10..2^40), `run_shell_cmd` (**always `shell=True`**, cmd list joined by spaces),
  `exec_parallel` (multiprocessing Pool + starmap; runs inline when threads==1), `terminate_with_message`
  (logs, then `sys.exit(1)`), name inference (`infer_source_name`, `filepath_without_archive_extensions`).
- `integrity.py`: shallow check (hash of .tar.lz/.gpg vs .md5, plus the expected part files exist per
  `*.parts.txt`) and deep check (extract each part to a temp dir, rehash, compare with `<name>[.partX].md5`,
  verify relative symlinks via tar listings).
- `extract.py`, `listing.py`, `encryption.py`: plzip|tar pipelines, `.tar.lst` parsing
  (`parse_tar_listing`, GNU vs BSD format detection), and gpg `--recipient-file`.
- `preparation_checks.py` and `checks/default_preparation_checks.ini`: shell-command checks configured in an
  ini file. Success conditions are `RETURN_ZERO`, `EMPTY_OUTPUT` and `CONTAINS("...")`, and `{WDIR}` is substituted in messages.
- `scripts/workflow/`: Snakemake workflow plus a wrapper script that runs `create filelist/tar/compressed-tar`
  on an LSF cluster (`ARCHIVER_MAX_CPUS_ENV_VAR=LSB_MAX_NUM_PROCESSORS`).
- `tests/features/`: feature tests against fixture archives in `tests/test-ressources/` (note
  the spelling "ressources"). `tests/helpers.py:generate_splitting_directory` builds a synthetic tree for split tests.

## Archive file layout (per part; split archives insert `.partN` before the suffixes)

`NAME.md5` (per-file md5s, md5sum format, backslash-escaped for `\n`/`\\` in names),
`NAME.lst` (file listing written by the archiver, input for `tar --files-from`), `NAME.tar.lst` (`tar -tvf` output),
`NAME.tar.md5`, `NAME.tar.lz`, `NAME.tar.lz.md5`, optionally `NAME.tar.lz.gpg(.md5)`.
Split archives also have `NAME.parts.txt` containing the part count. Paths in listings and hashes are
relative to the **parent** of the source dir, so they start with `NAME/`. Hash keys are NFC-normalized.

## Known quirks and bug suspects (not yet fixed; check them when debugging)

- `archive --max-single` is accepted by argparse, but `handle_archive` ignores it and `create_archive`
  has no parameter for it. Only `create filelist` actually passes `max_single_size` through.
- `splitter.split_directory` can yield an **empty** part, for example when the very first file walked is
  larger than part-size (allowed by max-single) and `current_archive` is still empty. In
  `create_file_listing_hash`, empty `archive_list`/`listing` are falsy, so it falls back to hashing and listing
  the **entire source tree** for that part.
- After an oversized (max-single) file starts its own part, `archive_size > max_package_size`. The next file
  then always forces another new part, which is fine. But a *directory* is still added to the listing without fitting.
- `get_size_of_directory` uses `du -shb` on Linux and `du -sh` elsewhere. The non-Linux output is
  human-readable and rounded, so sizes there are approximate.
- `run_shell_cmd` runs with shell=True and doesn't quote paths (only `du` adds quotes), so paths with spaces or
  shell metacharacters can break tar/plzip/gpg calls. `uncompress_and_extract` uses Popen and ignores return codes,
  and `CalledProcessError` is never raised there.
- `create_file_listing_hash` opens `.md5`/`.lst` in **append** mode, so a rerun into an existing dir would duplicate lines.
- `create tar --part` is an int and `create compressed-tar --part` is a str (glob `*part{N}.tar`).
- `do_encryption(destination_path, encryption_keys, threads)` is called positionally from
  `create_split_archive`, so `threads` lands in `remove_unencrypted` and `threads` stays 1. A split + encrypted
  `archive` therefore deletes the unencrypted `.tar.lz` files whenever threads >= 1, whatever `--remove` says,
  because `--remove` is never passed through.
- (Fixed 2026-10-05) The last log lines of a run were lost. The causes were a missing `logging.shutdown()` in
  `main()` (now in `finally`) and a race in multiprocessing-logging <0.4 (`empty()` ignores the queue's feeder buffer).
  Hence the requirement `>=0.4,<0.5`. 0.4 asserts the `fork` start method, so `main()` installs the mp handler only
  under `fork` (Linux). On macOS, with `spawn`, it was never useful. Regression test:
  `test_end_to_end.py::test_last_log_message_not_lost`. It's flaky by nature, so loop it about 20 times in the Linux container.
- `constants.ARCHIVE_SUFFIXES` uses non-raw strings with `\.`, which triggers a SyntaxWarning on Python 3.12+.

## Non-UTF-8 file names

Linux file names are raw bytes. Python decodes names that aren't valid UTF-8 using surrogate escapes
(for example, byte 0xF0 becomes `'\udcf0'`). Every text file holding paths (`.md5`, `.lst`, the `tar --files-from` list, and reading
`.tar.lst`) must be opened with `**constants.PATH_FILE_ENCODING` (utf-8 + surrogateescape). Otherwise writing
raises `UnicodeEncodeError: ... surrogates not allowed`, which is what crashed a cluster run in 2026-10. This round-trips the original
bytes, as `md5sum` does. Tests that need such names (`test_archive_with_non_utf8_filenames`) skip on macOS
(APFS rejects them), so run them in a Linux container:
`docker run --rm -v "$PWD":/code:ro <py3.9 image with plzip> bash -c 'cp -r /code /w && cd /w && python3 -m pytest -p no:cacheprovider'`.

## Conventions

- Branches: work on `develop`, PRs `develop` → `main`. External PRs sometimes land directly on `main`, so
  merge `main` back into `develop` when that happens (last synced 2026-10-05). Version is in `setup.py`, `archiver/__init__.py` and
  `setup.cfg` (bumpversion).
- Errors meant for users go through `helpers.terminate_with_message` (it exits). Logging goes to stdout.
