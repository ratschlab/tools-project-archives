# Project Archiver

Simple and easy command line tool to archive files at the end of a (research)
project (for example for compliance reasons).

It supports:
   * creating md5 hashes for archived files as well as the archives themselves
   * creating a listing of the archived files
   * compression using plzip (LZMA)
   * splitting large archives (several TBs) into smaller, more manageable parts
   * optional encryption using gpg
   * integrity checks of existing archives
   * a good level of parallelization to significantly speed up operations on
     large archives, in particular on a high performance cluster (HPC).


## Installation

### Requirements

- python >= 3.8
- [plzip](https://www.nongnu.org/lzip/plzip.html) (available for some package
  management systems like `apt` or `brew`)
- gnupg (optional, only required for encryption)
- [jdupes](https://codeberg.org/jbruchon/jdupes) (optional, for preparation checks)

### Install Python Package

```
pip install project-archiver
```

For nicer output on the console, you can optionally install the `coloredlogs` package

```
pip install coloredlogs
```

## Usage

### Quickstart

#### Archive Creation

Optionally, verify directory structure before archiving - see more details in [Prepare Files for Archiving](#prepare-files-for-archiving) section
```sh
archiver preparation-checks SOURCE_DIR
```

Create archive
```sh
archiver archive --threads 4 SOURCE_DIR ARCHIVE_DIR
```

Create archives in parts with a part size of at most 500GB (before compression):
```sh
archiver archive --threads 4 --part-size 500G SOURCE_DIR ARCHIVE_DIR
```

For archiving large directories (>few TBs) `archiver create` allows running the archiving step by step - see 
section [Optimally Creating Large Split Archives](#optimally-creating-large-split-archives)


#### Listing and Extraction
List archive content
```sh
archiver list ARCHIVE_DIR
```

Extract entire archive
```sh
archiver extract ARCHIVE_DIR DESTINATION_DIR
```

Extract single file from archive
```sh
archiver extract --subpath testdir/testfile ARCHIVE_DIR DESTINATION_DIR
```

#### Integrity Check
Quick integrity check on archive: checking hash of compressed archives match
```sh
archiver check ARCHIVE_DIR
```

Deep integrity check on archive: extracting files and verifying all file hashes match
```sh
archiver check --deep --threads 4 ARCHIVE_DIR
```


### Creating an Archive

In the next few sections some more details and recommendations on how to create an archive

#### Prepare Files for Archiving

First, prepare files for archiving by moving relevant files to a directory. Relevant files
may include raw data, intermediate data artifacts, figures, publications, code, container images (e.g. docker or singularity)

##### README.txt

It is recommended to add a README.txt file to the archive destination directory
containing some information about the project.

Here an example template:

```
[project name]
[short project abstract]

Key People:
[list of collaborators and authors]

Duration:
[start and end year]

Publications:
[publication list]

Relevant Code:
[if not included in archive, reference to where code is located]

Directory Structure:
[overview over directory structure]
e.g. (adapted output of `tree -L 2 -d`)

├── conda      <- conda environments
├── data
│   ├── preprocessed
│   └── varia
├── models
└── reports

```

##### Check File Structure

Before attempting to create an archive, it is recommended to verify the file structure to
avoid issues when creating the archive or later on using it:

```sh
archiver preparation-checks SOURCE_DIR
```

Among other points, the above command
 * checks you have read access to all files, fix if necessary. Otherwise, the archiving step will fail
 * checks if there are unnecessary files or duplicates
 * checks for broken symlinks
 * looks for absolute symlinks (e.g pointing to a file like `/data/myproject/samples/myfile.txt`) 
   which should be replaced by relative symlinks (e.g. `samples/myfile.txt`)

If some check fails, look in the output for suggestions on how to fix it.



#### Creating the Archive

Not too large archives can directly be created using `archiver archive`:

```sh
archiver archive --threads 4 SOURCE_DIR ARCHIVE_DIR | tee archiving.log
```

where `SOURCE_DIR` is the directory tree to be archived and `ARCHIVE_DIR` is the 
destination directory for the archive files - see section [Archive Package Structure](#archive-package-structure) 
for details on the files generated during archiving. 

Larger archives (maybe >1TB) can be split into parts, that is, instead of creating one huge
compressed tar file, several tar files are generated. Splitting the archive into parts can simplify file
handling as moving large files between systems can be painful. There may also be
file size limits on the target system. Furthermore, archive creation, integrity
checks and partial extractions can be done faster with a split archive due to parallelization.

Splitting can be done by adding
the `--part-size` argument. The part size is with respect to the uncompressed size. Note, that for
already highly compressed data, it is possible that the final compressed files can be slightly larger (e.g + ~1%) than 
the size specified in `--part-size` due to the overhead of the compression format.

Refer to `archiver archive --help` for more details.

##### Optimally Creating Large Split Archives

For really large archives (perhaps several TBs upwards) it may be beneficial to execute the
archive creation workflow step by step. This can help to use available
processing resources optimally as the different steps have different
resource usage characteristics (I/O and CPU). Also, if a steps fails for some reason, starting from scratch may
not be necessary.

The creation workflow looks like this:
 1. `archiver create filelist`: collects the files to be archived and generates
    the hash for every file. Parallelization is at file level.
 2. `archiver create tar`: creates a tar archive and a listing for every part independently.
    The parallelization is hence over parts.
 3. `archiver create compressed-tar`: compresses the tar archive. This is very
    CPU bound and parallelization is over file chunks, where the different parts
    are processed sequentially. Use as many CPUs as you can spare.

Note, that the `create tar` and `create compressed-tar` commands can be invoked
to work on a single part only using the `--part` argument. This can be useful to schedule the processing on
different machines.

Here an execution example. Assume you like to archive 2.5TB of data before compression 
on a machine with 8 available cores using a part size of 500GB (resulting in 5 parts):
```sh
archiver create filelist --threads 5 --part-size 500G SOURCE_DIR ARCHIVE_DIR | tee archiving.log
archiver create tar --threads 5 SOURCE_DIR ARCHIVE_DIR | tee -a archiving.log
archiver create compressed-tar --threads 8 ARCHIVE_DIR | tee -a archiving.log
```

### Archive Package Structure

A standard archive directory generated with this CLI-Tool consists of the following files in
a new directory:

- Base archive: project_name.tar.lz
- Content listing: project_name.tar.lst
- Content md5 hashes: project_name.md5
- Archive md5 hash: project_name.tar.md5
- Compressed archive hash: project_name.tar.lz.md5

Split archives have a similar structure for every part, but contain a 'partX.'
as suffix, where X is the part number. So the archive of part 1 would be called
`project_name.part1.tar.lz`. For split archive, there is also a file
`project_name.parts.txt` containing the total number of parts.


### Handling of Links

#### Symlinks

Symlinks are included as is by `tar`. However, the `archiver` tool will emit
warnings in case of broken symlinks or absolute symlinks. Absolute symlinks are
problematic, as in case the archive gets extracted on a different system, absoulte symlinks
will likely be broken. It is therefore recommendable to replace absolute symlinks
with relative symlinks where the target is expressed relative to the symlink location.


#### Hardlinks

For standard archives consisting of a single part, hardlinked files are
considered separate files in the listings, but as single files by `tar`.

For split archives, it may be that two hardlinked files end up in different
parts and hence appearing in two different tar files. For
this reason, it is recommended to replace hardlinks with symlinks to avoid a
possible duplication of data.

### Compression

Currently, only lzip (LZMA) is supported. It was chosen for its design for long-term archiving 
providing additional integrity checks and recovery mechansims, see also 
[lzip documentation](https://www.nongnu.org/lzip/lzip.html)

### GPG encryption

All key-handling is done by the user using GPG. This tool assumes a private key to decrypt an archive exists in the GPG keychain.

### Cluster Integration

#### Parallelism

In case the number of threads/workers is not specified on the command line, the
function `multiprocessing.cpu_count()` is used to determine the number of workers used.

In some environments, this value is not determined correctly. For instance, on some
HPC scheduler (e.g. LSF) the value does not represent the amount of CPUs reserved for
a job but CPUs available on the whole machine. The correct value may be specified in an environment 
variable though (on LSF it is `LSB_MAX_NUM_PROCESSOR`).
Setting the environment variable `ARCHIVER_MAX_CPUS_ENV_VAR` to e.g. `LSB_MAX_NUM_PROCESSOR`
instructs the `archiver` tool to go look whether the `LSB_MAX_NUM_PROCESSOR` variable is set
and take this number instead.


## Development

### Testing

```
# run in project root
python3 -m pytest tests/ -s
```

### Version Bumping

Currently, the example config of bumpversion is used as is, 
see [example commands](https://github.com/c4urself/bump2version/tree/master/docs/examples/semantic-versioning) in bumpversion documentation.
