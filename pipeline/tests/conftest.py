import importlib.util
import os
import sys
from pathlib import Path

# Dummy creds so pipeline.py / finance_pipeline.py can be imported without
# hitting real APIs — module-level client construction (OpenAI(), anthropic.Anthropic(),
# create_client()) never makes a network call, it just stores the key.
for _key in (
    "SERPAPI_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "SUPABASE_SERVICE_KEY", "UNSPLASH_ACCESS_KEY",
):
    os.environ.setdefault(_key, "test-dummy-value")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")

PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))  # so `from dataforseo import ...` resolves


def _load(module_name: str) -> None:
    """Load pipeline/<module_name>.py under sys.modules[module_name] explicitly,
    bypassing normal path resolution (the `pipeline/` directory itself has no
    __init__.py, so a plain `import pipeline` could ambiguously hit it as a
    namespace package instead of pipeline/pipeline.py)."""
    if module_name in sys.modules:
        return
    spec = importlib.util.spec_from_file_location(module_name, PIPELINE_DIR / f"{module_name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


_load("pipeline")
_load("finance_pipeline")
