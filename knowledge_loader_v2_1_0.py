#!/usr/bin/env python3
"""
knowledge_loader_v2_1_0.py
ATTI Agent Template — Knowledge Package Loader
Version: 2.1.0 | Core Compatibility: v2.0.0

BACKWARD COMPATIBILITY GUARANTEE:
- Does NOT modify SoulX
- Does NOT modify Rule Engine
- Does NOT modify platform_connector.py
- Does NOT modify Analytics Engine
- Does NOT break existing APIs
- Additive only — all new functionality is opt-in

Usage:
    from knowledge_loader_v2_1_0 import KnowledgeLoader
    loader = KnowledgeLoader()
    loader.load_all_packages()
"""

import json
import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from functools import lru_cache

logger = logging.getLogger(__name__)


class KnowledgeLoaderError(Exception):
    """Base exception for KnowledgeLoader errors."""
    pass


class IntegrityError(KnowledgeLoaderError):
    """Raised when package integrity check fails."""
    pass


class KnowledgeLoader:
    """
    RAG-ready Knowledge Package Loader for ATTI Agent Template.

    Compatible with Core v2.0.0. Designed to be additive — does not
    interfere with SoulX, Rule Engine, Analytics or platform_connector.

    Attributes:
        base_path (Path): Root path of atti-agent-template repository.
        manifest (dict): Loaded manifest index.
        packages (dict): Loaded knowledge packages keyed by segment name.
        _blocks_cache (list): Flat list of all blocks (populated on demand).
    """

    VERSION = "2.1.0"
    CORE_COMPATIBILITY = "v2.0.0"

    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
        validate_integrity: bool = True,
        auto_load: bool = False,
    ):
        """
        Initialize the KnowledgeLoader.

        Args:
            base_path: Root of atti-agent-template. Defaults to directory
                       containing this file.
            validate_integrity: If True, validates SHA256 hashes on load.
            auto_load: If True, loads all packages on init.
        """
        if base_path is None:
            base_path = Path(__file__).parent
        self.base_path = Path(base_path)
        self.validate_integrity = validate_integrity
        self._manifest: Optional[dict] = None
        self._packages: Dict[str, dict] = {}
        self._blocks_cache: Optional[List[dict]] = None

        logger.info(
            f"KnowledgeLoader v{self.VERSION} initialized | "
            f"base_path={self.base_path} | "
            f"core_compat={self.CORE_COMPATIBILITY}"
        )

        if auto_load:
            self.load_all_packages()

    # ──────────────────────────────────────────
    # MANIFEST
    # ──────────────────────────────────────────

    @property
    def manifest(self) -> dict:
        if self._manifest is None:
            self._manifest = self._load_manifest()
        return self._manifest

    def _load_manifest(self) -> dict:
        manifest_path = self.base_path / "knowledge_manifest_v2_1_0.json"
        if not manifest_path.exists():
            raise KnowledgeLoaderError(
                f"Manifest not found: {manifest_path}. "
                "Ensure knowledge_manifest_v2_1_0.json is present."
            )
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        logger.info(
            f"Manifest loaded: v{manifest.get('version')} | "
            f"{manifest.get('total_packages')} packages | "
            f"{manifest.get('total_blocks')} blocks"
        )
        return manifest

    # ──────────────────────────────────────────
    # LOAD PACKAGES
    # ──────────────────────────────────────────

    def load_all_packages(self) -> Dict[str, dict]:
        """
        Load all knowledge packages listed in the manifest.

        Returns:
            Dict mapping segment name → package dict.

        Raises:
            IntegrityError: If integrity validation fails.
            KnowledgeLoaderError: If a package file is missing.
        """
        self._blocks_cache = None  # Invalidate cache
        for pkg_meta in self.manifest.get("packages", []):
            segment = pkg_meta["segmento"]
            file_rel = pkg_meta["file"]
            pkg_path = self.base_path / file_rel

            if not pkg_path.exists():
                raise KnowledgeLoaderError(
                    f"Package file not found: {pkg_path}"
                )

            if self.validate_integrity:
                self._validate_hash(pkg_path, pkg_meta["hash_integridade"], segment)

            with open(pkg_path, "r", encoding="utf-8") as f:
                package = json.load(f)

            self._packages[segment] = package
            logger.info(
                f"  ✓ Loaded: {segment} | "
                f"{len(package.get('knowledge_blocks', []))} blocks"
            )

        logger.info(f"All {len(self._packages)} packages loaded successfully.")
        return self._packages

    def load_package(self, segment: str) -> dict:
        """
        Load a single package by segment name.

        Args:
            segment: Segment name as defined in the manifest.

        Returns:
            Package dict with metadata and knowledge_blocks.
        """
        for pkg_meta in self.manifest.get("packages", []):
            if pkg_meta["segmento"] == segment:
                if segment not in self._packages:
                    pkg_path = self.base_path / pkg_meta["file"]
                    if self.validate_integrity:
                        self._validate_hash(
                            pkg_path, pkg_meta["hash_integridade"], segment
                        )
                    with open(pkg_path, "r", encoding="utf-8") as f:
                        self._packages[segment] = json.load(f)
                    self._blocks_cache = None
                return self._packages[segment]

        raise KnowledgeLoaderError(
            f"Segment '{segment}' not found in manifest. "
            f"Available: {self.list_segments()}"
        )

    # ──────────────────────────────────────────
    # QUERY METHODS
    # ──────────────────────────────────────────

    def _all_blocks(self) -> List[dict]:
        """Return flat list of all blocks across all loaded packages."""
        if self._blocks_cache is None:
            self._blocks_cache = []
            for pkg in self._packages.values():
                self._blocks_cache.extend(
                    pkg.get("knowledge_blocks", [])
                )
        return self._blocks_cache

    def get_blocks_by_segment(self, segment: str) -> List[dict]:
        """
        Get all knowledge blocks for a specific segment.

        Args:
            segment: Segment name (e.g. "Hospital Privado").

        Returns:
            List of knowledge block dicts.
        """
        if segment not in self._packages:
            self.load_package(segment)
        return self._packages[segment].get("knowledge_blocks", [])

    def get_blocks_by_complexity(
        self,
        complexity: str,
        segment: Optional[str] = None
    ) -> List[dict]:
        """
        Get blocks filtered by complexity level.

        Args:
            complexity: "basico", "intermediario" or "avancado".
            segment: Optional — restrict to a specific segment.

        Returns:
            List of matching knowledge block dicts.
        """
        valid = {"basico", "intermediario", "avancado"}
        if complexity not in valid:
            raise ValueError(
                f"Invalid complexity '{complexity}'. Must be one of {valid}."
            )
        source = (
            self.get_blocks_by_segment(segment) if segment
            else self._all_blocks()
        )
        return [
            b for b in source
            if b.get("nivel_complexidade") == complexity
        ]

    def get_regulatory_blocks(
        self,
        segment: Optional[str] = None
    ) -> List[dict]:
        """
        Get all blocks flagged as regulatory.

        Args:
            segment: Optional — restrict to a specific segment.

        Returns:
            List of blocks where regulatory_flag is True.
        """
        source = (
            self.get_blocks_by_segment(segment) if segment
            else self._all_blocks()
        )
        return [b for b in source if b.get("regulatory_flag") is True]

    def get_blocks_by_tag(
        self,
        tag: str,
        segment: Optional[str] = None
    ) -> List[dict]:
        """
        Get blocks containing a specific tag.

        Args:
            tag: Tag string to search for.
            segment: Optional segment filter.

        Returns:
            List of matching blocks.
        """
        source = (
            self.get_blocks_by_segment(segment) if segment
            else self._all_blocks()
        )
        tag_lower = tag.lower()
        return [
            b for b in source
            if tag_lower in [t.lower() for t in b.get("tags", [])]
        ]

    def get_blocks_by_persona(
        self,
        persona: str,
        segment: Optional[str] = None
    ) -> List[dict]:
        """
        Get blocks targeted at a specific persona.

        Args:
            persona: Target persona (e.g. "gestor", "estudante", "institucional").
            segment: Optional segment filter.

        Returns:
            List of matching blocks.
        """
        source = (
            self.get_blocks_by_segment(segment) if segment
            else self._all_blocks()
        )
        return [
            b for b in source
            if b.get("persona_alvo", "").lower() == persona.lower()
        ]

    def get_top_blocks_by_priority(
        self,
        n: int = 10,
        segment: Optional[str] = None
    ) -> List[dict]:
        """
        Get top N blocks by embedding_priority.

        Args:
            n: Number of blocks to return.
            segment: Optional segment filter.

        Returns:
            Top N blocks sorted by embedding_priority descending.
        """
        source = (
            self.get_blocks_by_segment(segment) if segment
            else self._all_blocks()
        )
        return sorted(
            source,
            key=lambda b: float(b.get("embedding_priority", 0)),
            reverse=True
        )[:n]

    def search_blocks(
        self,
        query: str,
        segment: Optional[str] = None,
        top_k: int = 5
    ) -> List[dict]:
        """
        Keyword-based fallback search (pre-vector retrieval).

        This method provides Rule Engine compatible retrieval without
        requiring a vector index. Suitable for deterministic lookups
        and as fallback when vector store is unavailable.

        Args:
            query: Search string.
            segment: Optional segment filter.
            top_k: Maximum results to return.

        Returns:
            List of matching blocks sorted by relevance score.
        """
        source = (
            self.get_blocks_by_segment(segment) if segment
            else self._all_blocks()
        )
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        scored = []
        for block in source:
            content = block.get("conteudo", "").lower()
            tags = " ".join(block.get("tags", [])).lower()
            subcat = block.get("subcategoria", "").lower()
            combined = f"{content} {tags} {subcat}"

            # Score: exact match + term frequency
            score = 0.0
            if query_lower in combined:
                score += 2.0
            for term in query_terms:
                score += combined.count(term) * 0.1
            score *= float(block.get("retrieval_weight", 0.7))

            if score > 0:
                scored.append((score, block))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [b for _, b in scored[:top_k]]

    # ──────────────────────────────────────────
    # VECTOR PREPARATION (FAISS-READY)
    # ──────────────────────────────────────────

    def prepare_for_vectorization(
        self,
        segment: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepare blocks for embedding / vectorization.

        Returns a list of dicts ready to be passed to an embedding model.
        Does NOT perform actual embedding computation.

        Compatible with:
        - OpenAI text-embedding-3-large
        - sentence-transformers
        - FAISS IndexFlatIP
        - Pinecone upsert format

        Args:
            segment: Optional segment filter.

        Returns:
            List of dicts with keys: id, text, metadata.
        """
        source = (
            self.get_blocks_by_segment(segment) if segment
            else self._all_blocks()
        )
        vector_docs = []
        for block in source:
            if not block.get("vector_ready", False):
                continue
            doc = {
                "id": block["id"],
                "text": block.get("conteudo", ""),
                "metadata": {
                    "segment": block.get("categoria_macro", ""),
                    "subcategoria": block.get("subcategoria", ""),
                    "nivel_complexidade": block.get("nivel_complexidade", ""),
                    "persona_alvo": block.get("persona_alvo", ""),
                    "tags": block.get("tags", []),
                    "embedding_priority": block.get("embedding_priority", 0.5),
                    "retrieval_weight": block.get("retrieval_weight", 0.7),
                    "regulatory_flag": block.get("regulatory_flag", False),
                    "cross_package_reference": block.get(
                        "cross_package_reference", []
                    ),
                    "knowledge_version": block.get("knowledge_version", "2.1.0"),
                },
            }
            vector_docs.append(doc)
        return vector_docs

    # ──────────────────────────────────────────
    # UTILITY METHODS
    # ──────────────────────────────────────────

    def list_segments(self) -> List[str]:
        """Return list of available segment names."""
        return [p["segmento"] for p in self.manifest.get("packages", [])]

    def get_statistics(self) -> dict:
        """Return loading statistics."""
        loaded_blocks = self._all_blocks() if self._packages else []
        return {
            "loader_version": self.VERSION,
            "core_compatibility": self.CORE_COMPATIBILITY,
            "total_segments_available": len(
                self.manifest.get("packages", [])
            ),
            "segments_loaded": len(self._packages),
            "total_blocks_loaded": len(loaded_blocks),
            "regulatory_blocks": sum(
                1 for b in loaded_blocks if b.get("regulatory_flag")
            ),
            "vector_ready_blocks": sum(
                1 for b in loaded_blocks if b.get("vector_ready")
            ),
            "segments": list(self._packages.keys()),
        }

    def _validate_hash(
        self,
        path: Path,
        expected_hash: str,
        segment: str
    ) -> None:
        """Validate SHA256 hash of a package file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        actual = h.hexdigest()
        if actual != expected_hash:
            raise IntegrityError(
                f"Integrity check FAILED for segment '{segment}'.\n"
                f"  Expected: {expected_hash}\n"
                f"  Got:      {actual}\n"
                f"  File:     {path}\n"
                "Package may have been corrupted or tampered with."
            )
        logger.debug(f"  Integrity OK: {segment}")

    def reload(self) -> None:
        """Force reload of all packages and manifest."""
        self._manifest = None
        self._packages = {}
        self._blocks_cache = None
        self.load_all_packages()


# ──────────────────────────────────────────────
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# (Core v2.0 compatible — additive only)
# ──────────────────────────────────────────────

_default_loader: Optional[KnowledgeLoader] = None


def _get_loader() -> KnowledgeLoader:
    global _default_loader
    if _default_loader is None:
        _default_loader = KnowledgeLoader(auto_load=True)
    return _default_loader


def load_all_packages() -> Dict[str, dict]:
    """Load all knowledge packages. Returns dict keyed by segment name."""
    return _get_loader().load_all_packages()


def get_blocks_by_segment(segment: str) -> List[dict]:
    """Get all blocks for a given segment name."""
    return _get_loader().get_blocks_by_segment(segment)


def get_blocks_by_complexity(
    complexity: str,
    segment: Optional[str] = None
) -> List[dict]:
    """Get blocks filtered by complexity: basico | intermediario | avancado."""
    return _get_loader().get_blocks_by_complexity(complexity, segment)


def get_regulatory_blocks(segment: Optional[str] = None) -> List[dict]:
    """Get all blocks with regulatory_flag=True."""
    return _get_loader().get_regulatory_blocks(segment)


def prepare_for_vectorization(segment: Optional[str] = None) -> List[dict]:
    """Prepare blocks in FAISS/Pinecone-ready format."""
    return _get_loader().prepare_for_vectorization(segment)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    loader = KnowledgeLoader(auto_load=True)
    stats = loader.get_statistics()

    print("\n" + "=" * 60)
    print("ATTI Knowledge Loader v2.1.0 — Diagnostic Report")
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("=" * 60)
