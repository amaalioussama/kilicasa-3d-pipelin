"""Gestion du stockage pour le pipeline KiliCasa 3D.

Implémente le design pattern Adapter : une interface commune (StorageManager)
et des implémentations concrètes interchangeables (LocalStorageAdapter,
DriveStorageAdapter, S3StorageAdapter...).
"""

from abc import ABC, abstractmethod
from pathlib import Path
import shutil


# Dossiers standard du pipeline.
PIPELINE_DIRS = ("inputs", "frames_extracted", "frames_rejected")


class StorageManager(ABC):
    """Interface de base (Adapter) pour le stockage.

    Toute implémentation concrète doit savoir initialiser l'arborescence
    du pipeline et sauvegarder un fichier. Cela permet de switcher de
    backend (local, Google Drive, S3...) sans toucher au reste du code.
    """

    @abstractmethod
    def init_structure(self):
        """Crée les dossiers du pipeline (inputs, frames_extracted, ...)."""
        raise NotImplementedError

    @abstractmethod
    def save_file(self, file_obj, filename, subdir="inputs"):
        """Sauvegarde un fichier dans le sous-dossier donné et renvoie son chemin."""
        raise NotImplementedError

    @abstractmethod
    def get_path(self, subdir):
        """Renvoie le chemin (ou la clé) d'un sous-dossier du pipeline."""
        raise NotImplementedError


class LocalStorageAdapter(StorageManager):
    """Adapter pour le système de fichiers local."""

    def __init__(self, base_dir="data"):
        self.base_dir = Path(base_dir)

    def init_structure(self):
        """Crée le dossier de base et chaque sous-dossier du pipeline."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for name in PIPELINE_DIRS:
            (self.base_dir / name).mkdir(parents=True, exist_ok=True)
        return self.base_dir

    def get_path(self, subdir):
        return self.base_dir / subdir

    def save_file(self, file_obj, filename, subdir="inputs"):
        """Écrit `file_obj` sur disque.

        `file_obj` peut être un objet de type fichier (ex: UploadedFile de
        Streamlit, qui expose .getbuffer()/.read()) ou un chemin source.
        """
        dest_dir = self.get_path(subdir)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename

        # Cas 1 : chemin source existant -> copie.
        if isinstance(file_obj, (str, Path)) and Path(file_obj).exists():
            shutil.copy(file_obj, dest_path)
            return dest_path

        # Cas 2 : objet de type fichier (upload Streamlit, BytesIO...).
        with open(dest_path, "wb") as f:
            if hasattr(file_obj, "getbuffer"):
                f.write(file_obj.getbuffer())
            elif hasattr(file_obj, "read"):
                f.write(file_obj.read())
            else:
                f.write(file_obj)
        return dest_path


class DriveStorageAdapter(StorageManager):
    """Placeholder : adapter Google Drive (à implémenter)."""

    def init_structure(self):
        raise NotImplementedError("DriveStorageAdapter n'est pas encore implémenté.")

    def save_file(self, file_obj, filename, subdir="inputs"):
        raise NotImplementedError("DriveStorageAdapter n'est pas encore implémenté.")

    def get_path(self, subdir):
        raise NotImplementedError("DriveStorageAdapter n'est pas encore implémenté.")


class S3StorageAdapter(StorageManager):
    """Placeholder : adapter AWS S3 (à implémenter)."""

    def init_structure(self):
        raise NotImplementedError("S3StorageAdapter n'est pas encore implémenté.")

    def save_file(self, file_obj, filename, subdir="inputs"):
        raise NotImplementedError("S3StorageAdapter n'est pas encore implémenté.")

    def get_path(self, subdir):
        raise NotImplementedError("S3StorageAdapter n'est pas encore implémenté.")
