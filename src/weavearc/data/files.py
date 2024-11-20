from __future__ import annotations

import base64
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import mimetypes
import os
import typing
from enum import Enum
from pathlib import Path
from tempfile import SpooledTemporaryFile


class ContentType(str, Enum):
    """Enumeration of common content types."""

    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    APPLICATION_JSON = "application/json"
    APPLICATION_OCTET_STREAM = "application/octet-stream"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"


class RawFile:
    """Represents a raw file that may or may not be preprocessed.

    The `RawFile` class provides methods to handle file data that can be stored
    in memory or on disk, and offers utility functions for reading, writing,
    and manipulating the file content.
    """

    def __init__(
        self,
        filename: str,
        content_type: ContentType,
        file_data: typing.Optional[bytes] = None,
        headers: typing.Optional[dict[str, str]] = None,
        max_spool_size: int = 1024 * 1024,
    ) -> None:
        """Initializes a RawFile instance.

        Args:
            filename (str): The name of the file.
            content_type (ContentType): The content type of the file.
            file_data (typing.Optional[bytes]): Initial file data.
            headers (typing.Optional[dict[str, str]]): Optional headers associated with the file.
            max_spool_size (int): The maximum size (in bytes) before the file is spooled to disk.

        Example:
            >>> raw_file = RawFile(
            ...     filename='example.txt',
            ...     content_type=ContentType.TEXT_PLAIN,
            ...     file_data=b'Hello, World!',
            ... )
        """
        self.filename = filename
        self.content_type = content_type
        self.headers = headers or {}
        self.file = SpooledTemporaryFile(max_size=max_spool_size)
        if file_data:
            self.file.write(file_data)
            self.file.seek(0)

    @classmethod
    def from_litestar_upload_file(cls, upload_file: typing.Any) -> RawFile:
        """Creates a RawFile instance from an UploadFile instance.

        Args:
            upload_file (UploadFile): The UploadFile instance to create from.

        Returns:
            RawFile: The created RawFile instance.

        Example:
            >>> upload_file = UploadFile(...)
            >>> raw_file = RawFile.from_upload_file(upload_file)
        """
        litestar_spec: typing.Optional[importlib.machinery.ModuleSpec] = (
            importlib.util.find_spec("litestar")
        )

        if litestar_spec is None:
            raise ImportError("""
                              Litestar is required to use this method. Please, install with:
                              >>> pip install litestar
                              """)

        litestar = importlib.util.module_from_spec(litestar_spec)

        loader: typing.Optional[importlib.abc.Loader] = litestar_spec.loader
        if loader is None:
            raise ImportError("Loader is None")

        loader.exec_module(litestar)

        upload_file.file.seek(0)
        data = upload_file.file.read()
        # Map the content type to the ContentType enum, defaulting if necessary
        content_type_value = upload_file.content_type
        content_type = (
            ContentType(content_type_value)
            if content_type_value in ContentType._value2member_map_
            else ContentType.APPLICATION_OCTET_STREAM
        )
        return cls(
            filename=upload_file.filename,
            content_type=content_type,
            file_data=data,
            headers=upload_file.headers,
        )

    @classmethod
    def from_path(cls, path: typing.Union[str, Path]) -> RawFile:
        """Creates a RawFile instance from a file path.

        Args:
            path (typing.Union[str, Path]): The file path.

        Returns:
            RawFile: The created RawFile instance.

        Example:
            >>> raw_file = RawFile.from_path('/path/to/file.txt')
        """
        path = Path(path)
        filename = path.name
        content_type = cls._guess_content_type(path)
        with path.open("rb") as f:
            data = f.read()
        return cls(
            filename=filename, content_type=content_type, file_data=data, headers={}
        )

    @staticmethod
    def _guess_content_type(path: typing.Union[str, Path]) -> ContentType:
        """Guesses the content type based on the file extension.

        Args:
            path (typing.Union[str, Path]): The file path.

        Returns:
            ContentType: The guessed content type.

        Example:
            >>> content_type = RawFile._guess_content_type('/path/to/file.txt')
            >>> print(content_type)
            ContentType.TEXT_PLAIN
        """
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type and mime_type in ContentType._value2member_map_:
            return ContentType(mime_type)
        else:
            return ContentType.APPLICATION_OCTET_STREAM

    def read(self, size: int = -1) -> bytes:
        """Reads data from the file.

        Args:
            size (int): The number of bytes to read. Default is -1 (read all).

        Returns:
            bytes: The data read from the file.

        Example:
            >>> data = raw_file.read()
        """
        return self.file.read(size)

    def write(self, data: bytes) -> int:
        """Writes data to the file.

        Args:
            data (bytes): The data to write.

        Returns:
            int: The number of bytes written.

        Example:
            >>> raw_file.write(b'Hello World')
        """
        return self.file.write(data)

    def seek(
        self,
        offset: int,
        whence: typing.Literal[0, 1, 2] = 0,
    ) -> int:
        """Moves the file pointer to a new position.

        Args:
            offset (int): The offset to move to.
            whence (typing.Literal[os.SEEK_SET, os.SEEK_CUR, os.SEEK_END]): The reference point. Default is os.SEEK_SET.

        Returns:
            int: The new absolute position.

        Example:
            >>> raw_file.seek(0)  # Move to the beginning of the file
        """
        return self.file.seek(offset, whence)

    def close(self) -> None:
        """Closes the file.

        Returns:
            None

        Example:
            >>> raw_file.close()
        """
        self.file.close()

    def save_to_path(self, path: typing.Union[str, Path]) -> None:
        """Saves the file to the specified path.

        Args:
            path (typing.Union[str, Path]): The destination file path.

        Returns:
            None

        Example:
            >>> raw_file.save_to_path('/path/to/destination.txt')
            >>> print("File saved successfully.")
        """
        path = Path(path)
        with path.open("wb") as f:
            self.file.seek(0)
            while True:
                chunk = self.file.read(8192)
                if not chunk:
                    break
                f.write(chunk)
        self.file.seek(0)  # Reset position after saving

    def get_size(self) -> int:
        """Gets the size of the file in bytes.

        Returns:
            int: The size of the file in bytes.

        Example:
            >>> size = raw_file.get_size()
            >>> print(f"File size: {size} bytes")
        """
        current_pos = self.file.tell()
        self.file.seek(0, os.SEEK_END)
        size = self.file.tell()
        self.file.seek(current_pos)
        return size

    @property
    def rolled_to_disk(self) -> bool:
        """Indicates whether the file has been rolled to disk.

        Returns:
            bool: True if the file is on disk, False if in memory.

        Example:
            >>> if raw_file.rolled_to_disk:
            ...     print("File is on disk")
        """
        return getattr(self.file, "_rolled", False)

    def get_md5(self) -> str:
        """Calculates the MD5 hash of the file content.

        Returns:
            str: The MD5 hash as a hexadecimal string.

        Example:
            >>> md5_hash = raw_file.get_md5()
            >>> print(f"MD5: {md5_hash}")
        """
        md5 = hashlib.md5()
        self.file.seek(0)
        while chunk := self.file.read(8192):
            md5.update(chunk)
        self.file.seek(0)
        return md5.hexdigest()

    def get_sha256(self) -> str:
        """Calculates the SHA-256 hash of the file content.

        Returns:
            str: The SHA-256 hash as a hexadecimal string.

        Example:
            >>> sha256_hash = raw_file.get_sha256()
            >>> print(f"SHA-256: {sha256_hash}")
        """
        sha256 = hashlib.sha256()
        self.file.seek(0)
        while chunk := self.file.read(8192):
            sha256.update(chunk)
        self.file.seek(0)
        return sha256.hexdigest()

    def get_bytes(self) -> bytes:
        """Gets the entire file content as bytes.

        Returns:
            bytes: The file content.

        Example:
            >>> data = raw_file.get_bytes()
        """
        self.file.seek(0)
        data = self.file.read()
        self.file.seek(0)
        return data

    def get_base64(self) -> str:
        """Gets the file content encoded as a base64 string.

        Returns:
            str: The base64 encoded file content.

        Example:
            >>> b64_data = raw_file.get_base64()
            >>> print(b64_data)
        """
        data = self.get_bytes()
        b64_data = base64.b64encode(data).decode("utf-8")
        return b64_data

    def is_empty(self) -> bool:
        """Checks if the file is empty.

        Returns:
            bool: True if the file is empty, False otherwise.

        Example:
            >>> if raw_file.is_empty():
            ...     print("File is empty")
        """
        size = self.get_size()
        return size == 0

    def __repr__(self) -> str:
        """Returns the string representation of the RawFile instance.

        Returns:
            str: The string representation.

        Example:
            >>> print(raw_file)
            <RawFile filename=example.txt content_type=text/plain>
        """
        return (
            f"<RawFile filename={self.filename} content_type={self.content_type.value}>"
        )
