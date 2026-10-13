import hashlib
import hmac
import json
import os
import re
import shutil
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib

from .exceptions import ConfigurationError, ModelIntegrityError, ModelNotFoundError
from .logging import get_logger

logger = get_logger(__name__)

_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
_VERSION_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _sign(key: str, payload: str) -> str:
    return hmac.new(
        key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


class ModelRegistry:
    def __init__(
        self,
        root: Path,
        signing_key: Optional[str],
        keep_versions: int = 5,
        require_key: bool = False,
    ) -> None:
        self.root = Path(root)
        self.keep_versions = max(1, keep_versions)
        if not signing_key:
            if require_key:
                raise ConfigurationError(
                    "A signing key is required to persist or load model artifacts"
                )
            signing_key = "flowlet-development-signing-key"
            logger.warning("Model registry is using the development signing key")
        self._key = signing_key
        self._lock = threading.RLock()

    def _model_dir(self, name: str) -> Path:
        if not _NAME_PATTERN.match(name):
            raise ValueError(f"Invalid model name: {name}")
        return self.root / name

    def _version_dir(self, name: str, version: str) -> Path:
        if not _VERSION_PATTERN.match(version):
            raise ValueError(f"Invalid model version: {version}")
        return self._model_dir(name) / version

    @staticmethod
    def new_version() -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        return f"{stamp}-{uuid.uuid4().hex[:8]}"

    def save(
        self,
        name: str,
        artifact: Any,
        metadata: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        promote: bool = True,
    ) -> str:
        with self._lock:
            version = version or self.new_version()
            target = self._version_dir(name, version)
            target.mkdir(parents=True, exist_ok=True)
            model_path = target / "model.joblib"
            temp_path = target / f"model.joblib.{uuid.uuid4().hex}.tmp"
            joblib.dump(artifact, temp_path, compress=3)
            os.replace(temp_path, model_path)
            checksum = _sha256(model_path)
            created_at = datetime.now(timezone.utc).isoformat()
            manifest = {
                "name": name,
                "version": version,
                "created_at": created_at,
                "sha256": checksum,
                "signature": _sign(self._key, f"{name}:{version}:{checksum}"),
                "metadata": metadata or {},
            }
            manifest_tmp = target / f"manifest.json.{uuid.uuid4().hex}.tmp"
            with open(manifest_tmp, "w", encoding="utf-8") as handle:
                json.dump(manifest, handle, indent=2, default=str)
            os.replace(manifest_tmp, target / "manifest.json")
            if promote:
                self._write_pointer(name, version)
            self._prune(name)
            return version

    def _write_pointer(self, name: str, version: str) -> None:
        directory = self._model_dir(name)
        directory.mkdir(parents=True, exist_ok=True)
        pointer_tmp = directory / f"CURRENT.{uuid.uuid4().hex}.tmp"
        pointer_tmp.write_text(version, encoding="utf-8")
        os.replace(pointer_tmp, directory / "CURRENT")

    def current_version(self, name: str) -> Optional[str]:
        pointer = self._model_dir(name) / "CURRENT"
        if not pointer.exists():
            return None
        version = pointer.read_text(encoding="utf-8").strip()
        return version or None

    def list_versions(self, name: str) -> List[str]:
        directory = self._model_dir(name)
        if not directory.exists():
            return []
        versions = [
            entry.name
            for entry in directory.iterdir()
            if entry.is_dir() and (entry / "manifest.json").exists()
        ]
        return sorted(versions)

    def manifest(self, name: str, version: Optional[str] = None) -> Dict[str, Any]:
        version = version or self.current_version(name)
        if not version:
            raise ModelNotFoundError(f"No version available for model {name}")
        path = self._version_dir(name, version) / "manifest.json"
        if not path.exists():
            raise ModelNotFoundError(f"Model {name} version {version} not found")
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def load(
        self, name: str, version: Optional[str] = None
    ) -> Tuple[Any, Dict[str, Any]]:
        with self._lock:
            manifest = self.manifest(name, version)
            version = manifest["version"]
            model_path = self._version_dir(name, version) / "model.joblib"
            if not model_path.exists():
                raise ModelNotFoundError(f"Artifact missing for {name} {version}")
            checksum = _sha256(model_path)
            if not hmac.compare_digest(checksum, manifest.get("sha256", "")):
                raise ModelIntegrityError(f"Checksum mismatch for {name} {version}")
            expected = _sign(self._key, f"{name}:{version}:{checksum}")
            if not hmac.compare_digest(expected, manifest.get("signature", "")):
                raise ModelIntegrityError(f"Signature mismatch for {name} {version}")
            artifact = joblib.load(model_path)
            return artifact, manifest

    def promote(self, name: str, version: str) -> None:
        with self._lock:
            self.manifest(name, version)
            self._write_pointer(name, version)

    def _prune(self, name: str) -> None:
        versions = self.list_versions(name)
        current = self.current_version(name)
        excess = len(versions) - self.keep_versions
        if excess <= 0:
            return
        for version in versions:
            if excess <= 0:
                break
            if version == current:
                continue
            shutil.rmtree(self._version_dir(name, version), ignore_errors=True)
            excess -= 1
