from __future__ import annotations

import base64
import hashlib
import logging
import mimetypes
import sys
from http.cookiejar import CookieJar
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    BinaryIO,
    Callable,
    Iterable,
    Literal,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    TypeAlias,
    overload,
)

import magic
import msgspec
import requests
from requests import Response
from requests.auth import AuthBase
from requests.models import PreparedRequest
from typing_extensions import Self

from architecture.log import create_logger
from architecture.utils.decorators import ensure_module_installed

if TYPE_CHECKING:
    from _typeshed import SupportsItems, SupportsRead
    from fastapi import UploadFile as FastAPIUploadFile
    from litestar.datastructures import UploadFile as LitestarUploadFile

    _TextMapping: TypeAlias = MutableMapping[str, str]
    _HeadersMapping: TypeAlias = Mapping[str, str | bytes | None]

    _Data: TypeAlias = (
        # used in requests.models.PreparedRequest.prepare_body
        #
        # case: is_stream
        # see requests.adapters.HTTPAdapter.send
        # will be sent directly to http.HTTPConnection.send(...) (through urllib3)
        Iterable[bytes]
        # case: not is_stream
        # will be modified before being sent to urllib3.HTTPConnectionPool.urlopen(body=...)
        # see requests.models.RequestEncodingMixin._encode_params
        # see requests.models.RequestEncodingMixin._encode_files
        # note that keys&values are converted from Any to str by urllib.parse.urlencode
        | str
        | bytes
        | SupportsRead[str | bytes]
        | list[tuple[Any, Any]]
        | tuple[tuple[Any, Any], ...]
        | Mapping[Any, Any]
    )

    _ParamsMappingKeyType: TypeAlias = str | bytes | int | float
    _ParamsMappingValueType: TypeAlias = (
        str | bytes | int | float | Iterable[str | bytes | int | float] | None
    )
    _Params: TypeAlias = (
        SupportsItems[_ParamsMappingKeyType, _ParamsMappingValueType]
        | tuple[_ParamsMappingKeyType, _ParamsMappingValueType]
        | Iterable[tuple[_ParamsMappingKeyType, _ParamsMappingValueType]]
        | str
        | bytes
    )
    _Verify: TypeAlias = bool | str
    _Timeout: TypeAlias = float | tuple[float, float] | tuple[float, None]
    _Cert: TypeAlias = str | tuple[str, str]
    Incomplete: TypeAlias = Any
    _Hook: TypeAlias = Callable[[Response], Any]
    _HooksInput: TypeAlias = Mapping[str, Iterable[_Hook] | _Hook]
    _FileContent: TypeAlias = SupportsRead[str | bytes] | str | bytes
    _FileName: TypeAlias = str | None
    _FileContentType: TypeAlias = str
    _FileSpecTuple2: TypeAlias = tuple[_FileName, _FileContent]
    _FileSpecTuple3: TypeAlias = tuple[_FileName, _FileContent, _FileContentType]
    _FileCustomHeaders: TypeAlias = Mapping[str, str]
    _FileSpecTuple4: TypeAlias = tuple[
        _FileName, _FileContent, _FileContentType, _FileCustomHeaders
    ]
    _FileSpec: TypeAlias = (
        _FileContent | _FileSpecTuple2 | _FileSpecTuple3 | _FileSpecTuple4
    )
    _Files: TypeAlias = Mapping[str, _FileSpec] | Iterable[tuple[str, _FileSpec]]
    _Auth: TypeAlias = (
        tuple[str, str] | AuthBase | Callable[[PreparedRequest], PreparedRequest]
    )

debug_logger = create_logger(__name__, level=logging.DEBUG)


def find_extension(
    *,
    filename: Optional[str] = None,
    content_type: Optional[str] = None,
    contents: Optional[bytes] = None,
    url: Optional[str] = None,
) -> str:
    if filename and (ext := get_extension_from_filename(filename)):
        return ext
    if content_type and (ext := mime_to_ext(content_type)):
        return ext
    if contents and (ext := get_extension_agressivelly(contents)):
        return ext
    if url and (ext := get_extension_from_url(url)):
        return ext

    raise ValueError("Unable to determine the file extension.")


def get_extension_from_url(url: str) -> str:
    """Extracts the file extension from a URL."""
    from urllib.parse import urlparse

    parsed_url = urlparse(url)
    path = parsed_url.path
    if not path:
        raise ValueError("The URL does not contain a path.")
    name = path.split("/")[-1]
    if "." not in name:
        raise ValueError("The URL does not contain a file extension.")

    return get_extension_from_filename(name)


def get_extension_from_filename(filename: str) -> str:
    ext = filename.split(".")[-1]
    return ext


def get_extension_agressivelly(contents: bytes) -> str:
    def _detect_mime_type_manually(content: bytes) -> str:
        # Ordered by category and signature specificity (longer/more specific first)
        signature_map = [
            # Images
            ("image/jp2", [(0, bytes.fromhex("00 00 00 0C 6A 50 20 20"))]),
            ("image/png", [(0, bytes.fromhex("89 50 4E 47 0D 0A 1A 0A"))]),
            ("image/tiff", [(0, b"II*\x00"), (0, b"MM\x00*")]),
            ("image/webp", [(8, b"WEBP")]),  # After 'RIFF' header
            ("image/jpeg", [(0, bytes.fromhex("FF D8 FF"))]),
            ("image/gif", [(0, b"GIF87a"), (0, b"GIF89a")]),
            ("image/bmp", [(0, b"BM")]),
            ("image/x-icon", [(0, bytes.fromhex("00 00 01 00"))]),
            # Documents
            ("application/pdf", [(0, b"%PDF")]),
            ("application/msword", [(0, bytes.fromhex("D0 CF 11 E0 A1 B1 1A E1"))]),
            (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                [(0, b"PK\x03\x04"), (30, b"word/")],
            ),
            (
                "application/vnd.ms-excel",
                [(0, bytes.fromhex("D0 CF 11 E0 A1 B1 1A E1"))],
            ),
            (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                [(0, b"PK\x03\x04"), (30, b"xl/")],
            ),
            (
                "application/vnd.ms-powerpoint",
                [(0, bytes.fromhex("D0 CF 11 E0 A1 B1 1A E1"))],
            ),
            (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                [(0, b"PK\x03\x04"), (30, b"ppt/")],
            ),
            ("application/rtf", [(0, b"{\\rtf")]),
            # Archives
            ("application/zip", [(0, b"PK\x03\x04")]),
            ("application/x-rar-compressed", [(0, b"Rar!\x1a\x07\x00")]),
            ("application/x-7z-compressed", [(0, bytes.fromhex("37 7A BC AF 27 1C"))]),
            ("application/gzip", [(0, bytes.fromhex("1F 8B"))]),
            ("application/x-xz", [(0, bytes.fromhex("FD 37 7A 58 5A 00"))]),
            ("application/x-bzip2", [(0, b"BZh")]),
            # Audio/Video
            ("audio/mpeg", [(0, b"ID3")]),
            ("audio/flac", [(0, b"fLaC")]),
            ("audio/ogg", [(0, b"OggS")]),
            ("audio/x-wav", [(8, b"WAVE")]),  # After 'RIFF' header
            ("video/mp4", [(4, b"ftyp")]),
            ("video/x-msvideo", [(8, b"AVI ")]),  # After 'RIFF' header
            ("video/quicktime", [(4, b"ftypqt")]),
            # System/Executables
            ("application/x-msdownload", [(0, b"MZ")]),
            ("application/vnd.ms-cab-compressed", [(0, b"MSCF")]),
            ("application/x-shockwave-flash", [(0, b"FWS"), (0, b"CWS")]),
            # Databases
            ("application/vnd.sqlite3", [(0, b"SQLite format 3\x00")]),
            # Text Formats
            ("text/xml", [(0, b"<?xml")]),
            ("application/json", [(0, b"{"), (0, b"[")]),  # Best-effort detection
        ]

        # Check magic numbers
        for mime_type, signatures in signature_map:
            for offset, sig in signatures:
                if len(content) >= offset + len(sig):
                    if content[offset : offset + len(sig)] == sig:
                        return mime_type

        # Special text detection
        text_mimes = [
            (b"\xef\xbb\xbf", "text/plain"),  # UTF-8 BOM
            (b"\xfe\xff", "text/plain"),  # UTF-16 BE
            (b"\xff\xfe", "text/plain"),  # UTF-16 LE
            (b"\x00\x00\xfe\xff", "text/plain"),  # UTF-32 BE
            (b"\xff\xfe\x00\x00", "text/plain"),  # UTF-32 LE
        ]

        for bom, mime in text_mimes:
            if content.startswith(bom):
                return mime

        try:
            content.decode("utf-8")
            return "text/plain"
        except UnicodeDecodeError:
            pass

        return "application/octet-stream"

    try:
        return magic.Magic(mime=True).from_buffer(contents)
    except Exception:
        return _detect_mime_type_manually(contents)


def mime_to_ext(mime: str) -> str:
    """
    Returns the most common file extension for the given MIME type.
    Returns None if the MIME type is unknown.
    """
    _mime = mimetypes.guess_extension(mime, strict=False)
    if _mime is None:
        raise ValueError("Unable to determine the file extension.")

    return _mime.lstrip(".")


def ext_to_mime(extension: str) -> str:
    """
    Returns the MIME type associated with the given file extension.
    Returns None if the extension is unknown.
    """
    # Normalize the extension to include a leading dot
    if not extension.startswith("."):
        extension = "." + extension

    # Create a dummy filename with the given extension
    dummy_filename = f"dummy{extension}"
    mime_type, _ = mimetypes.guess_type(dummy_filename)
    if mime_type is None:
        raise ValueError("Unable to determine the MIME type.")

    return mime_type


class RawFile(msgspec.Struct, frozen=True, gc=False):
    """
    Represents an immutable raw file with its content and extension.

    The `RawFile` class is designed for efficient and immutable handling of raw file data.
    It stores file contents as immutable bytes and provides utility methods for reading,
    writing, and manipulating the file content without mutating the original data.

    **Key Features:**

    - **Immutability**: Instances of `RawFile` are immutable. Once created, their contents cannot be modified.
      This is enforced by using `msgspec.Struct` with `frozen=True`, ensuring thread-safety and predictability.
    - **Performance**: Optimized for speed and memory efficiency by disabling garbage collection (`gc=False`)
      and using immutable data structures. This reduces overhead and can significantly boost performance,
      especially when handling many instances.
    - **Compactness**: Stores file content in memory as bytes, leading to fast access and manipulation.
      The absence of mutable state allows for leaner objects.
    - **Garbage Collection**: By setting `gc=False`, the class instances are excluded from garbage collection tracking.
      This improves performance when creating many small objects but requires careful management of resources.
    - **Compression Support**: Provides methods for compressing and decompressing file contents using gzip,
      returning new `RawFile` instances without altering the original data.
    - **Versatile Creation Methods**: Offers multiple class methods to create `RawFile` instances from various sources,
      such as file paths, bytes, base64 strings, strings, streams, URLs, and cloud storage services.

    **Important Notes:**

    - **Memory Usage**: Since the entire file content is stored in memory, handling very large files may lead
      to high memory consumption. Ensure that file sizes are manageable within the available system memory.
    - **Resource Management**: As garbage collection is disabled, it's crucial to manage resources appropriately.
      While the class is designed to be immutable and not require cleanup, be cautious when handling external resources.
    - **Thread-Safety**: Immutability ensures that instances of `RawFile` are inherently thread-safe.

    **Example Usage:**

    ```python
    # Create a RawFile instance from a file path
    raw_file = RawFile.from_file_path('example.pdf')

    # Access the file extension
    print(raw_file.extension)  # Output: "pdf"

    # Get the size of the file content
    print(raw_file.get_size())  # Output: Size of the file in bytes

    # Compute checksums
    md5_checksum = raw_file.compute_md5()
    sha256_checksum = raw_file.compute_sha256()

    # Save the content to a new file
    raw_file.save_to_file('copy_of_example.pdf')

    # Compress the file content
    compressed_file = raw_file.compress()

    # Decompress the file content
    decompressed_file = compressed_file.decompress()
    ```

    **Methods Overview:**

    - Creation:
      - `from_file_path(cls, file_path: str)`: Create from a file path.
      - `from_bytes(cls, data: bytes, extension: str)`: Create from bytes.
      - `from_base64(cls, b64_string: str, extension: str)`: Create from a base64 string.
      - `from_string(cls, content: str, extension: str, encoding: str = "utf-8")`: Create from a string.
      - `from_stream(cls, stream: BinaryIO, extension: str)`: Create from a binary stream.
      - `from_url(cls, url: str, ...)`: Create from a URL.
      - `from_s3(cls, bucket_name: str, object_key: str, extension: Optional[str] = None)`: Create from Amazon S3.
      - `from_azure_blob(cls, connection_string: str, container_name: str, blob_name: str, extension: Optional[str] = None)`: Create from Azure Blob Storage.
      - `from_gcs(cls, bucket_name: str, blob_name: str, extension: Optional[str] = None)`: Create from Google Cloud Storage.
      - `from_zip(cls, zip_file_path: str, inner_file_path: str, extension: Optional[str] = None)`: Create from a file within a ZIP archive.
      - `from_stdin(cls, extension: str)`: Create from standard input.

    - Utilities:
      - `save_to_file(self, file_path: str)`: Save content to a file.
      - `get_size(self) -> int`: Get the size of the content in bytes.
      - `compute_md5(self) -> str`: Compute MD5 checksum.
      - `compute_sha256(self) -> str`: Compute SHA256 checksum.
      - `get_mime_type(self) -> str`: Get MIME type based on the file extension.
      - `compress(self) -> RawFile`: Compress content using gzip.
      - `decompress(self) -> RawFile`: Decompress gzip-compressed content.
      - `read_async(self) -> bytes`: Asynchronously read the content.

    **Immutability Enforcement:**

    - The class is decorated with `msgspec.Struct` and `frozen=True`, which makes all instances immutable.
    - Any method that would traditionally modify the instance returns a new `RawFile` instance instead.
    - This design ensures that the original data remains unchanged, promoting safer and more predictable code.

    **Performance Considerations:**

    - **No Garbage Collection Overhead**: By setting `gc=False`, instances are not tracked by the garbage collector, reducing overhead.
      This is suitable when instances do not contain cyclic references.
    - **Optimized Data Structures**: Using immutable bytes and avoiding mutable state enhances performance and reduces memory footprint.
    - **Fast Access**: In-memory storage allows for rapid access and manipulation of file content.

    **Garbage Collection and Resource Management:**

    - While garbage collection is disabled for instances, Python's reference counting will still deallocate objects when they are no longer in use.
    - Be mindful when working with external resources (e.g., open files or network connections) to ensure they are properly closed.
    - Since `RawFile` instances hold data in memory, they are automatically cleaned up when references are removed.

    **Thread-Safety:**

    - Immutable objects are inherently thread-safe because their state cannot change after creation.
    - `RawFile` instances can be shared across threads without the need for synchronization mechanisms.

    **Compression Level:**

    - The `compress` and `decompress` methods use gzip with default compression levels.
    - If you need to specify a compression level, you can modify the methods to accept a parameter for the compression level.

    **Extensibility:**

    - Custom methods can be added to handle specific use cases or integrations with other services.

    **Examples of Creating `RawFile` Instances from Different Sources:**

    ```python
    # From bytes
    raw_file = RawFile.from_bytes(b"Hello, World!", "txt")

    # From a base64 string
    raw_file = RawFile.from_base64("SGVsbG8sIFdvcmxkIQ==", "txt")

    # From a URL
    raw_file = RawFile.from_url("https://example.com/data.json")

    # From Amazon S3
    raw_file = RawFile.from_s3("my-bucket", "path/to/object.json")

    # From Azure Blob Storage
    raw_file = RawFile.from_azure_blob("connection_string", "container", "blob.json")

    # From Google Cloud Storage
    raw_file = RawFile.from_gcs("my-bucket", "path/to/blob.json")

    # From standard input
    raw_file = RawFile.from_stdin("txt")
    ```

    **Disclaimer:**

    - Ensure that all necessary dependencies are installed for methods that interface with external services.
    - Handle exceptions appropriately in production code, especially when dealing with I/O operations and network requests.
    """

    name: Annotated[
        str,
        msgspec.Meta(
            title="Name", description="The name of the file", examples=["example.pdf"]
        ),
    ]
    contents: bytes
    extension: str

    @classmethod
    def from_file_path(cls, file_path: str) -> RawFile:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found at {file_path}")

        if not path.is_file():
            raise ValueError(f"{file_path} is not a file")

        with open(file_path, "rb") as f:
            data = f.read()

        return cls(
            name=path.name,
            contents=data,
            extension=path.suffix.lstrip("."),
        )

    @classmethod
    def from_bytes(cls, data: bytes, name: str, extension: str) -> RawFile:
        return cls(name=name, contents=data, extension=extension)

    @classmethod
    def from_base64(cls, b64_string: str, name: str, extension: str) -> RawFile:
        data = base64.b64decode(b64_string)
        return cls.from_bytes(data=data, name=name, extension=extension)

    @classmethod
    def from_string(
        cls, content: str, name: str, extension: str, encoding: str = "utf-8"
    ) -> RawFile:
        data = content.encode(encoding)
        return cls.from_bytes(data=data, name=name, extension=extension)

    @classmethod
    def from_stream(cls, stream: BinaryIO, name: str, extension: str) -> RawFile:
        data = stream.read()
        return cls(name=name, contents=data, extension=extension)

    @overload
    @classmethod
    def from_litestar_upload_file(
        cls, file: LitestarUploadFile, is_zip: Literal[False] = False
    ) -> RawFile: ...

    @overload
    @classmethod
    def from_litestar_upload_file(
        cls, file: LitestarUploadFile, is_zip: Literal[True]
    ) -> Sequence[RawFile]: ...

    @classmethod
    @ensure_module_installed("litestar", "litestar")
    def from_litestar_upload_file(
        cls, file: LitestarUploadFile, is_zip: bool = False
    ) -> RawFile | Sequence[RawFile]:
        filename = file.filename
        content_type = file.content_type
        file_contents = file.file.read()

        debug_logger.debug(f"File content type: {content_type}")
        debug_logger.debug(f"File name: {filename}")

        extension = find_extension(
            filename=filename,
            content_type=content_type,
            contents=file_contents,
        )

        return cls(name=file.filename, contents=file_contents, extension=extension)

    @classmethod
    @ensure_module_installed("fastapi", "fastapi")
    def from_fastapi_upload_file(cls, file: FastAPIUploadFile) -> RawFile:
        if file.content_type is None:
            raise ValueError("The content type of the file is missing.")
        file_contents = file.file.read()

        extension: str = find_extension(
            content_type=file.content_type,
            filename=file.filename,
            contents=file_contents,
        )

        filename = file.filename
        if filename is None:
            raise ValueError("The filename of the file is missing.")

        return cls(name=filename, contents=file_contents, extension=extension)

    @classmethod
    def from_url(
        cls: type[Self],
        url: str,
        *,
        params: Optional[_Params] = None,
        data: Optional[_Data] = None,
        headers: Optional[_HeadersMapping] = None,
        cookies: Optional[CookieJar | _TextMapping] = None,
        files: Optional[_Files] = None,
        auth: Optional[_Auth] = None,
        timeout: Optional[_Timeout] = None,
        allow_redirects: bool = False,
        proxies: Optional[_TextMapping] = None,
        hooks: Optional[_HooksInput] = None,
        stream: Optional[bool] = None,
        verify: Optional[_Verify] = None,
        cert: Optional[_Cert] = None,
        json: Optional[Incomplete] = None,
        extension: Optional[str] = None,
    ) -> RawFile:
        response: requests.Response = requests.get(
            url,
            params=params,
            data=data,
            headers=headers,
            cookies=cookies,
            files=files,
            auth=auth,
            timeout=timeout,
            allow_redirects=allow_redirects,
            proxies=proxies,
            hooks=hooks,
            stream=stream,
            verify=verify,
            cert=cert,
            json=json,
        )
        response.encoding = "utf-8"

        response_content: bytes | Any = response.content

        if not isinstance(response_content, bytes):
            data = str(data).encode("utf-8")

        file_extension = extension or (
            find_extension(
                content_type=response.headers.get("Content-Type", "").split(";")[0]
            )
            or "html"
        )

        return cls(name=url, contents=response_content, extension=file_extension)

    @ensure_module_installed("boto3", "boto3")
    @classmethod
    def from_s3(
        cls,
        bucket_name: str,
        object_key: str,
        extension: Optional[str] = None,
    ) -> RawFile:
        import boto3

        s3 = boto3.client("s3")

        if not extension:
            extension = Path(object_key).suffix.lstrip(".")

        if not extension:
            raise ValueError(
                "Unable to determine the file extension. Please specify it explicitly."
            )

        obj = s3.get_object(Bucket=bucket_name, Key=object_key)
        data = obj["Body"].read()

        return cls(name=bucket_name, contents=data, extension=extension)

    @ensure_module_installed("azure.storage.blob", "azure-storage-blob")
    @classmethod
    def from_azure_blob(
        cls,
        connection_string: str,
        container_name: str,
        blob_name: str,
        extension: Optional[str] = None,
    ) -> RawFile:
        from azure.storage.blob import BlobServiceClient

        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_name
        )

        if not extension:
            extension = Path(blob_name).suffix.lstrip(".")

        if not extension:
            raise ValueError(
                "Unable to determine the file extension. Please specify it explicitly."
            )

        stream = blob_client.download_blob()
        data = stream.readall()

        return cls(name=container_name, contents=data, extension=extension)

    @ensure_module_installed("google.cloud.storage", "google-cloud-storage")
    @classmethod
    def from_gcs(
        cls, bucket_name: str, blob_name: str, extension: Optional[str] = None
    ) -> RawFile:
        from google.cloud.storage import Client

        client = Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        if not extension:
            extension = Path(blob_name).suffix.lstrip(".")

        if not extension:
            raise ValueError(
                "Unable to determine the file extension. Please specify it explicitly."
            )

        data = blob.download_as_bytes()

        return cls(name=bucket_name, contents=data, extension=extension)

    @classmethod
    def from_zip(
        cls,
        zip_file_path: str,
    ) -> RawFile:
        """
        Creates a RawFile instance from a ZIP archive. The content of the RawFile
        will be the bytes of the entire ZIP archive itself.

        Args:
            zip_file_path: The path to the ZIP archive file.

        Returns:
            A RawFile instance where the contents are the bytes of the ZIP archive
            and the extension is "zip".
        """
        with open(zip_file_path, "rb") as f:
            data = f.read()

        return cls(name=Path(zip_file_path).name, contents=data, extension="zip")

    @classmethod
    def from_database_blob(cls, blob_data: bytes, extension: str) -> RawFile:
        return cls.from_bytes(name="database_blob", data=blob_data, extension=extension)

    @classmethod
    def from_stdin(cls, extension: str) -> RawFile:
        data = sys.stdin.buffer.read()
        return cls.from_bytes(name="stdin", data=data, extension=extension)

    @classmethod
    def from_ftp(
        cls,
        host: str,
        filepath: str,
        username: str = "",
        password: str = "",
        extension: Optional[str] = None,
    ) -> RawFile:
        import ftplib

        ftp = ftplib.FTP(host)
        ftp.login(user=username, passwd=password)
        data = bytearray()
        ftp.retrbinary(f"RETR {filepath}", data.extend)
        ftp.quit()
        if not extension:
            extension = Path(filepath).suffix.lstrip(".")

        return cls(name=filepath, contents=bytes(data), extension=extension)

    def save_to_file(self, file_path: str) -> None:
        with open(file_path, "wb") as f:
            f.write(self.contents)

    def get_size(self) -> int:
        return len(self.contents)

    def compute_md5(self) -> str:
        md5 = hashlib.md5()
        md5.update(self.contents)
        return md5.hexdigest()

    def compute_sha256(self) -> str:
        sha256 = hashlib.sha256()
        sha256.update(self.contents)
        return sha256.hexdigest()

    def get_mime_type(self) -> str:
        mime_type, _ = mimetypes.guess_type(f"file.{self.extension}")
        if mime_type is None:
            mime_type = magic.Magic(mime=True).from_buffer(self.contents)
        return mime_type

    def compress(self) -> RawFile:
        import gzip

        compressed_data = gzip.compress(self.contents)
        return RawFile(
            name="compressed.zip", contents=compressed_data, extension=self.extension
        )  # TODO

    def decompress(self) -> RawFile:
        import gzip

        decompressed_data = gzip.decompress(self.contents)
        return RawFile(
            name=self.name, contents=decompressed_data, extension=self.extension
        )

    async def read_async(self) -> bytes:
        return self.contents

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass  # Nothing to close since we're using bytes

    def __del__(self):
        pass  # No cleanup needed
