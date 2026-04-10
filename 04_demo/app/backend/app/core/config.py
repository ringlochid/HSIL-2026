from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False,
    )

    env: str = 'dev'
    app_name: str = 'hsil-demo-backend'
    host: str = '0.0.0.0'
    port: int = 8000
    debug: bool = True
    api_prefix: str = '/api/v1'
    allowed_origins_raw: str = Field('http://localhost:5173', alias='ALLOWED_ORIGINS')
    upload_dir: Path = Path('./data/uploads')
    max_upload_mb: int = 20
    database_url: str = 'sqlite+pysqlite:///./data/app.db'

    llm_provider: str = 'mock'
    openai_api_key: str | None = None
    openai_model: str = 'gpt-4o-mini'
    langchain_api_key: str | None = None
    langchain_tracing_v2: bool = False

    use_real_apis: bool = False
    vep_base_url: str = 'https://rest.ensembl.org'
    spliceai_base_url: str = 'https://spliceai-38-xwkwwwxdwq-uc.a.run.app/spliceai/'
    clinvar_base_url: str = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'
    franklin_base_url: str = 'https://api.genoox.com'
    franklin_parse_base_url: str = 'https://franklin.genoox.com'
    franklin_api_token: str | None = None

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins_raw.split(',') if item.strip()]

    @property
    def backend_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def fixtures_root(self) -> Path:
        return self.backend_root / 'app' / 'fixtures'


def ensure_runtime_dirs(settings: Settings) -> None:
    upload_dir = settings.upload_dir
    if not upload_dir.is_absolute():
        upload_dir = settings.backend_root / upload_dir
        settings.upload_dir = upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)

    for prefix in ('sqlite+pysqlite:///', 'sqlite:///'):
        if settings.database_url.startswith(prefix):
            db_path = Path(settings.database_url[len(prefix):])
            if not db_path.is_absolute():
                db_path = settings.backend_root / db_path
                settings.database_url = f'{prefix}{db_path.as_posix()}'
            db_path.parent.mkdir(parents=True, exist_ok=True)
            break


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    ensure_runtime_dirs(settings)
    return settings
