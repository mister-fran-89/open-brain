from typing import Optional

from src.config import settings

# Singletons (lazily initialized)
_vault = None
_index = None


async def get_vault():
    from src.storage import MarkdownVault
    global _vault
    if _vault is None:
        _vault = MarkdownVault(settings.vault_path)
    return _vault


async def get_index():
    from src.storage import MetadataIndex
    global _index
    if _index is None:
        db_path = settings.vault_path / "_index" / "brain.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _index = MetadataIndex(db_path)
        await _index.initialize()
    return _index


def get_capture_service():
    from src.storage import MarkdownVault, MetadataIndex
    from src.ai import get_provider_for_task
    from src.core import CaptureService
    vault = MarkdownVault(settings.vault_path)
    db_path = settings.vault_path / "_index" / "brain.db"
    index = MetadataIndex(db_path)
    ai = get_provider_for_task("classify")
    pre = get_provider_for_task("preprocess")
    return CaptureService(vault=vault, index=index, ai_provider=ai, preprocess_provider=pre)


def get_query_service():
    from src.storage import MarkdownVault, MetadataIndex
    from src.ai import get_provider_for_task
    from src.core import QueryService
    vault = MarkdownVault(settings.vault_path)
    db_path = settings.vault_path / "_index" / "brain.db"
    index = MetadataIndex(db_path)
    ai = get_provider_for_task("query")
    return QueryService(vault=vault, index=index, ai_provider=ai)


def get_digest_service():
    from src.storage import MarkdownVault, MetadataIndex
    from src.ai import get_provider_for_task
    from src.core import DigestService
    vault = MarkdownVault(settings.vault_path)
    db_path = settings.vault_path / "_index" / "brain.db"
    index = MetadataIndex(db_path)
    ai = get_provider_for_task("summarize")
    return DigestService(vault=vault, index=index, ai_provider=ai)
