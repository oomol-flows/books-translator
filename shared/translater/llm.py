from typing import Generator, cast
from io import StringIO
from enum import Enum
from pydantic import SecretStr
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessageChunk
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI


class LLM_API(Enum):
  OpenAI = 1,
  Claude = 2,
  Gemini = 3,

class LLM:
  def __init__(
      self, 
      api: LLM_API, 
      key: str | None, 
      url: str | None, 
      model: str,
      temperature: float,
      timeout: float | None,
    ) -> None:
    self._model: ChatAnthropic | ChatOpenAI | ChatVertexAI
    self._timeout: float | None = timeout

    if api == LLM_API.OpenAI:
      self._model = ChatOpenAI(
        api_key=cast(SecretStr, key),
        base_url=url,
        model=model,
        temperature=temperature,
      )
    elif api == LLM_API.Claude:
      self._model = ChatAnthropic(
        api_key=cast(SecretStr, key),
        model_name=model,
        base_url=url,
        timeout=timeout,
        stop=None,
        temperature=temperature,
      )
    elif api == LLM_API.Gemini:
      self._model = ChatVertexAI(
        model=model,
        base_url=url,
        timeout=timeout,
        temperature=temperature,
      )
  
  def invoke(self, system: str, human: str) -> str:
    resp = self._model.invoke(
      timeout=self._timeout,
      input=[
        SystemMessage(content=system),
        HumanMessage(content=human),
      ],
    )
    return str(resp.content)

  def invoke_response_lines(self, system: str, human: str) -> Generator[str, None, None]:
    stream = self._model.stream(
      timeout=self._timeout,
      input=[
        SystemMessage(content=system),
        HumanMessage(content=human),
      ],
    )
    line_buffer = StringIO()
    aggregate: BaseMessageChunk | None = None

    for chunk in stream:
      fragment = str(chunk.content)
      aggregate = chunk if aggregate is None else aggregate + chunk
      lines = fragment.split("\n")
      if len(lines) > 0:
        line_buffer.write(lines[0])
        for line in lines[1:]:
          yield line_buffer.getvalue()
          line_buffer = StringIO()
          line_buffer.write(line)

    # TODO: aggregate.usage_metadata
    yield line_buffer.getvalue()