import tiktoken
import spacy

from typing import Generator
from dataclasses import dataclass
from enum import Enum
from .nlp import NLP

@dataclass
class Paragraph:
  text: str
  index: int
  count: int

class CountUnit(Enum):
  Char = 1
  Token = 2

class ParagraphsGroup:
  def __init__(
      self,
      max_translating_group: int,
      max_translating_group_unit: CountUnit,
    ):
    self._nlp: NLP = NLP(default_lan="en")
    self._max_translating_group: int = max_translating_group
    self._max_translating_group_unit: CountUnit = max_translating_group_unit
    self._token_encoder: tiktoken.Encoding = tiktoken.get_encoding("o200k_base")
    self._token_encoder.encode("Hello World") # to setup the model

  def split(self, text_list: list[str]) -> list[list[Paragraph]]:
    splited_paragraph_list: list[Paragraph] = []
    for index, text in enumerate(text_list):
      for paragraph in self._collect_text(index, text):
        splited_paragraph_list.append(paragraph)

    sum_count: int = 0
    self_paragraphs_count = 0
    grouped_paragraph_list: list[list[Paragraph]] = []
    current_paragraph_list: list[Paragraph] = []

    for paragraph in splited_paragraph_list:
      if len(current_paragraph_list) > 0 and \
         sum_count + paragraph.count > self._max_translating_group:

        grouped_paragraph_list.append(current_paragraph_list)
        sum_count = 0
        self_paragraphs_count = 0

        # make sure the first and last two paragraphs in the group are repeated in the previous and next groups respectively, 
        # so that the translation has a certain context and enhances the translation accuracy
        if len(current_paragraph_list) <= 2:
          current_paragraph_list = []
        else:
          current_paragraph_list = current_paragraph_list[-2:]
          for paragraph in current_paragraph_list:
            sum_count += paragraph.count

      sum_count += paragraph.count
      self_paragraphs_count += 1
      current_paragraph_list.append(paragraph)

    if self_paragraphs_count > 0:
      grouped_paragraph_list.append(current_paragraph_list)

    return grouped_paragraph_list

  def _collect_text(self, index: int, text: str) -> Generator[Paragraph, None, None]:
    buffer: list[str] = []
    buffer_count: int = 0

    for sent in self._nlp.split_into_sents(text):
      text = sent.text
      count = self._text_count(text)
      if buffer_count + count <= self._max_translating_group:
        buffer.append(text)
        buffer_count += count
      else:
        if buffer_count > 0:
          yield Paragraph(
            text="".join(buffer),
            index=index,
            count=buffer_count
          )
          buffer.clear()
          buffer_count = 0
        
        while count > self._max_translating_group:
          head_text = text[:self._max_translating_group]
          text = text[self._max_translating_group:]
          yield Paragraph(
            text=head_text,
            index=index,
            count=self._text_count(head_text)
          )
        
        count = self._text_count(text)
        if count > 0:
          buffer.append(text)
          buffer_count += count
    
    if buffer_count > 0:
      yield Paragraph(
        text="".join(buffer),
        index=index,
        count=buffer_count
      )

  def _text_count(self, text: str) -> int:
    if self._max_translating_group_unit == CountUnit.Token:
      return len(self._token_encoder.encode(text))
    else:
      return len(text)