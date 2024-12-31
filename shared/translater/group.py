import tiktoken

from dataclasses import dataclass
from typing import Generator
from .nlp import NLP


@dataclass
class Fragment:
  id: int
  origin: str
  target: str
  tokens: int
  index: int
  sentence_index: int
  sentences: int

class Group:
  def __init__(self, group_max_tokens: int, interval_max_tokens: int) -> None:
    self._encoder: tiktoken.Encoding = tiktoken.get_encoding("o200k_base")
    self._nlp: NLP = NLP("en")
    self._group_max_tokens: int = group_max_tokens
    self._interval_max_tokens: int = interval_max_tokens

  def split(self, texts: list[str]) -> list[list[Fragment]]:
    matrix: list[list[Fragment]] = []
    all_fragments = self._transform_to_fragments(texts)
    for id, fragment in enumerate(all_fragments):
      fragment.id = id
    for fragments in self._split_fragments(all_fragments):
      matrix.append(fragments)
    return matrix

  def _transform_to_fragments(self, texts: list[str]) -> list[Fragment]:
    fragments: list[Fragment] = []
    for index, text in enumerate(texts):
      tokens: int = len(self._encoder.encode(text))
      if tokens < self._group_max_tokens:
        fragments.append(Fragment(
          id=0,
          origin=text,
          target="",
          tokens=tokens,
          index=index,
          sentence_index=0,
          sentences=1,
        ))
      else:
        for fragment in self._split_large_text(index, text):
          fragments.append(fragment)
    return fragments

  def _split_large_text(self, index: int, text: str) -> Generator[Fragment, None, None]:
    text_index_list: list[tuple[str, int]] = []
    for sentence in self._nlp.split_into_sents(text):
      text = sentence.text
      tokens = self._encoder.encode(text)
      while len(tokens) > self._group_max_tokens:
        head_tokens = tokens[:self._group_max_tokens]
        tokens = tokens[self._group_max_tokens:]
        head_text = self._encoder.decode(head_tokens)
        text_index_list.append((head_text, len(head_tokens)))
      if len(tokens) > 0:
        tail_text = self._encoder.decode(tokens)
        text_index_list.append((tail_text, len(tokens)))

    for sentence_index, (text, tokens) in enumerate(text_index_list):
      yield Fragment(
        id=0,
        origin=text,
        target="",
        tokens=tokens,
        index=index, 
        sentence_index=sentence_index, 
        sentences=len(text_index_list),
      )

  def _split_fragments(self, fragments: list[Fragment]) -> Generator[list[Fragment], None, None]:
    current_group: list[Fragment] = []
    current_tokens: int = 0

    for fragment in fragments:
      next_tokens: int = current_tokens + fragment.tokens
      if len(current_group) > 0 and next_tokens > self._group_max_tokens:
        yield current_group
        current_group, current_tokens = self._keep_interval(current_group)

      current_group.append(fragment)
      current_tokens += fragment.tokens

    if len(current_group) > 0:
      yield current_group

  def _keep_interval(self, group: list[Fragment]):
    keep_group: list[Fragment] = []
    keep_tokens: int = 0
    for fragment in reversed(group):
      next_tokens = keep_tokens + fragment.tokens
      if len(keep_group) > 0 and next_tokens > self._interval_max_tokens:
        break
      keep_tokens += fragment.tokens
      keep_group.append(fragment)
    keep_group.reverse()
    return keep_group, keep_tokens