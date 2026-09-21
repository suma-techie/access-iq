
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.config import get_settings

settings = get_settings()


class StorageBackend(ABC):
    @abstractmethod
    def save(self, content: bytes, filename: str) -> str:
        pass

    @abstractmethod
    def load(self, storage_url: str) -> bytes:
        ...

    @abstractmethod
    def delete(self, storage_url: str) -> None:
        ...


class LocalStorageBackend(StorageBackend):
    def __init__(self, base_dir: str) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, filename: str) -> str:
        return f"{uuid.uuid4()}-{filename}"

    def save(self, content: bytes, filename: str) -> str:
        key = self._key(filename)
        path = self.base_dir / key
        path.write_bytes(content)
        return f"local://{key}"

    def load(self, storage_url: str) -> bytes:
        key = storage_url.removeprefix("local://")
        return (self.base_dir / key).read_bytes()

    def delete(self, storage_url: str) -> None:
        key = storage_url.removeprefix("local://")
        path = self.base_dir / key
        if path.exists():
            path.unlink()


class S3StorageBackend(StorageBackend):
    def __init__(self) -> None:
        import boto3

        self.bucket = settings.storage_bucket_name
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.aws_endpoint_url_s3,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region or None,
        )

    def _key(self, filename: str) -> str:
        return f"{uuid.uuid4()}-{filename}"

    def save(self, content: bytes, filename: str) -> str:
        key = self._key(filename)
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        return f"s3://{self.bucket}/{key}"

    def load(self, storage_url: str) -> bytes:
        _, _, rest = storage_url.partition("s3://")
        bucket, _, key = rest.partition("/")
        obj = self.client.get_object(Bucket=bucket, Key=key)
        return obj["Body"].read()

    def delete(self, storage_url: str) -> None:
        _, _, rest = storage_url.partition("s3://")
        bucket, _, key = rest.partition("/")
        self.client.delete_object(Bucket=bucket, Key=key)


def get_storage_backend() -> StorageBackend:
    if settings.storage_backend == "s3":
        return S3StorageBackend()
    return LocalStorageBackend(settings.document_storage_dir)
