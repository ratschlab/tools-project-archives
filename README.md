# tools-project-archives

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

- python >= 3.6
- [plzip](https://www.nongnu.org/lzip/plzip.html) (available for some package
  management systems like `apt` or `brew`)
- gnupg (optional, only required for encryption)


### Install Python Package
 #TODO: pip install


## Usage

 # TODO: change/automate
```
$ archiver archive [src] [archive_dir] [-p --part <maximum size of each archive part>] [-n --threads] [-k --key <public key>] [-c --compression] # Create a new archive
$ archiver extract [archive_dir] [dest] [--subdir <path in archive>] [-n --threads] # Extract archive
$ archiver list [archive_dir] [<subdir>] [-d --deep] # List content of archive
$ archiver check [archive_dir] [-d --deep] # Check integrity of archive
$ archiver encrypt [archive_dir] [-k --key <public key>] # Encrypts existing archive. When creating new archive, use 'archive' command
```

### Creating an Archive

In the next few sections some details and recommendations on how to create an archive

#### Prepare Files for Archiving

First, prepare files for archiving by moving relevant files to a directory.

A few things you may want to check before proceding with the archive creation:
 * check you have read access to all files, fix if necessary. The following
   command returns non readable files, excluding broken links: `find . !-readable ! -type l`
 * check if there are unnecessary files, for example
   * temporary files or directories
   * duplicate files. You can use [jdupes](https://github.com/jbruchon/jdupes) to find and symlink duplicate files (TODO: test and explain how to use `jdupes`)
 * check for broken symlinks: `find . -xtype l`
 * replace absolute symlinks (e.g pointing to a file like
     `/data/myproject/samples/myfile.txt`) with relative symlinks (e.g.
     `samples/myfile.txt`) (TODO, `find . -type l -lname '/*'`, use [symlinks](https://github.com/brandt/symlinks)
 * in case you want to create split archives, it is recommended to replace
   hardlinks with symlinks (see section "Handling of Links") command for this? TODO
               find . -type f -links +1 -printf '%i %n %p\n' | sort [TODO iname appropriate]

##### README.txt

It is recommended to add a README.txt file to the archive destination directory
containing some information about the project.

Here an example template:

```
[project name]

[project abstract]

[list of collaborators and authors]

[start and end year]

[publications]

```


#### Creating the Archive

Not too large archives can directly be created using `archiver archive`. Refer to
`archiver archive --help` for details.
TODO make example along with `tee`

Larger archives (maybe >1TB) can be split into parts, that is, instead of creating one huge
compressed tar file, several tar files are generated. This can be done by adding
the `--part-size` argument. Note, that the part size is with respect to the uncompressed size.
Splitting the archive into parts can simplify file
handling as moving large files between systems can be painful. There may also be
file size limits on the target system. Furthermore, archive creation, integrity
checks and partial extractions can be done more efficiently with a split archive.


##### Optimally Creating Large Split Archives

For really large archives (perhaps several TBs upwards) it may be beneficial to execute the
archive creation workflow step by step. This can help to use available
processing resources optimally as the different steps have different
requirements. Also, if a steps fails for some reason, starting from scratch may
not be necessary.

The creation workflow lookd like this:
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

TODO script fragment including `tee`


### Archive Package structure

A standard archive generated with this CLI-Tool will constist of the following files in
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
problematic, as when the archive gets extracted to a different system, symlinks
will be likely broken. It is therefore recommendable to replace absolute symlinks
with relative symlinks where the target is expressed relative to the symlink location.


#### Hardlinks

For standard archives consisting of a single part, hardlinked files are
considered separate files in the listings, but as single files by `tar`.

For split archives, it may be that two hardlinked files end up in different
parts and hence appearing in two different tar files. For
this reason, it is recommended to replace hardlinks with symlinks to avoid a
possible duplication of data.


### GPG encryption

All key-handling is done by the user using GPG. This tool assumes a private key to decrypt an archive exists in the GPG keychain.


## Development

### Testing

```
# run in project root
python3 -m pytest tests/ -s
```
