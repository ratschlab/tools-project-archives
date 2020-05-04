# tools-project-archives

Simple and easy command line tool a researcher can use to archive files at the end of a project.

## Requirements

-   python 3.x
-   plzip

## Usage

```
$ archiver archive [src] [archive_dir] # Create a new archive
$ archiver list [archive_dir] [<subdir>] # List content of archive
$ archiver extract [-subdir <path in archive>] [archive_dir] [dest] # Extract archive
$ archiver check [archive_dir] # Check integrity of archive
```

## Testing

```
PYTHONPATH=./archiver/ pytest tests/ -s
```

## Issues

Tar archive has inconsistent relative paths that are dependent on where the script will be executed from
