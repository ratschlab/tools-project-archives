# tools-project-archives

Simple and easy command line tool a researcher can use to archive files at the end of a project.

## Requirements

-   python >= 3.6
-   plzip

## Usage

```
$ archiver archive [src] [archive_dir] [-n --threads] [-c --compression] # Create a new archive
$ archiver list [archive_dir] [<subdir>] [-d --deep] [-n --threads] # List content of archive
$ archiver extract [archive_dir] [dest] [--subdir <path in archive>] # Extract archive
$ archiver check [archive_dir] # Check integrity of archive
```

## Testing

```
# run in project root
python3 -m pytest tests/ -s
```

## Issues

Tar archive has inconsistent relative paths that are dependent on where the script will be executed from
