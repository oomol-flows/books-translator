from dataclasses import dataclass
from oocana import Context
from shared.translater import LLM_API

@dataclass
class LLMDescription:
  api: LLM_API
  key: str
  url: str
  model: str

def parse(params: dict, context: Context) -> LLMDescription:
  llm_api: str = params["llm_api"]
  if llm_api == "oomol":
    env = context.oomol_llm_env
    return LLMDescription(
      api=LLM_API.OpenAI,
      key=env["api_key"],
      url=env["base_url"],
      model=_default(params["model"], env["models"][0]),
    )
  else:
    api = _parse_api(params["llm_api"])
    model: str | None = params["model"]
    if model is None:
      raise ValueError("model is required")
    return LLMDescription(
      api=api,
      key=params["api_key"],
      url=params["url"],
      model=model,
    )

def _parse_api(llm_api: str) -> LLM_API:
  api: LLM_API
  if llm_api == "openai":
    api = LLM_API.OpenAI
  elif llm_api == "claude":
    api = LLM_API.Claude
  elif llm_api == "gemini":
    api = LLM_API.Gemini
  else:
    raise Exception(f"unknown llm_api: {llm_api}")
  return api


def _default(value: str | None, default_value: str) -> str:
  return value if value is not None else default_value