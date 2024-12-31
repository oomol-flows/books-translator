import tiktoken

from typing import Iterable, Generator


class Group:
  def __init__(self, group_max_tokens: int) -> None:
    self._encoder: tiktoken.Encoding = tiktoken.get_encoding("o200k_base")
    self._group_max_tokens: int = group_max_tokens

  def split(self, texts: Iterable[str]) -> Generator[list[tuple[int, str]], None, None]:
    text_pairs = [
      (text, len(self._encoder.encode(text)))
      for text in texts
    ]
    current_group: list[tuple[int, str]] = []
    current_tokens: int = 0
    last_tokens: int = 0

    for index, (text, tokens) in enumerate(text_pairs):
      if len(current_group) > 0 and current_tokens + tokens > self._group_max_tokens:
        yield current_group
        if tokens > self._group_max_tokens:
          current_group = []
          current_tokens = 0
        else:
          current_group = [current_group[-1]]
          current_tokens = last_tokens

      current_group.append((index, text))
      current_tokens += tokens
      last_tokens = tokens

    if len(current_group) > 0:
      yield current_group