import re

REQUIRED_SPACE_MULTIPLIER = 1.1
HASH_SUFFIX = ".md5"
TAR_HASH_SUFFIX = ".tar.md5"
COMPRESSED_ARCHIVE_SUFFIX = ".tar.lz"
ENCRYPTED_ARCHIVE_SUFFIX = ".tar.lz.gpg"
COMPRESSED_ARCHIVE_HASH_SUFFIX = ".tar.lz.md5"
ENCRYPTED_ARCHIVE_HASH_SUFFIX = ".tar.lz.gpg.md5"
LISTING_SUFFIX = ".tar.lst"
READ_CHUNK_BYTE_SIZE = 1000 * 1000 * 100
ENCRYPTION_ALGORITHM = "AES256"
ENV_VAR_MAPPER_MAX_CPUS = "ARCHIVER_MAX_CPUS_ENV_VAR"
DEFAULT_COMPRESSION_LEVEL = 6
ARCHIVE_SUFFIXES = ['\.part[0-9]+', '\.tar', '\.md5', '\.lz', '\.gpg', '\.lst', '\.parts', '\.txt']
ARCHIVE_SUFFIXES_REG = '$|'.join(ARCHIVE_SUFFIXES) + '$'

MD5_LINE_REGEX = re.compile(r'(\S+)\s+(\S.*)')

# for text files containing file paths (hash lists, listings): file names don't need to be valid UTF-8,
# Python represents such bytes as surrogates (PEP 383), surrogateescape writes them back as the original bytes
PATH_FILE_ENCODING = {'encoding': 'utf-8', 'errors': 'surrogateescape'}
