from typing import Generator

from dataclasses import dataclass
from .paragraph_sliter import split_paragraph

@dataclass
class Paragraph:
  text: str
  index: int

class ParagraphsGroup:
  def __init__(self, max_paragraph_len: int, max_group_len: int):
    self._max_paragraph_len: int = max_paragraph_len
    self._max_group_len: int = max_group_len

  def split(self, text_list: list[str]) -> list[list[Paragraph]]:
    splited_paragraph_list: list[Paragraph] = []

    for index, text in enumerate(text_list):
      self._collect_text(index, text, splited_paragraph_list)

    sum_len = 0
    self_paragraphs_count = 0
    grouped_paragraph_list: list[list[Paragraph]] = []
    current_paragraph_list: list[Paragraph] = []

    for paragraph in splited_paragraph_list:
      if len(current_paragraph_list) > 0 and sum_len + len(paragraph.text) > self._max_group_len:
        grouped_paragraph_list.append(current_paragraph_list)
        sum_len = 0
        self_paragraphs_count = 0

        # make sure the first and last two paragraphs in the group are repeated in the previous and next groups respectively, 
        # so that the translation has a certain context and enhances the translation accuracy
        if len(current_paragraph_list) <= 2:
          current_paragraph_list = []
        else:
          current_paragraph_list = current_paragraph_list[-2:]
          for cell in current_paragraph_list:
            sum_len += len(cell.text)

      sum_len += len(paragraph.text)
      self_paragraphs_count += 1
      current_paragraph_list.append(paragraph)

    if self_paragraphs_count > 0:
      grouped_paragraph_list.append(current_paragraph_list)

    return grouped_paragraph_list

  def _collect_text(self, index: int, text: str, splited_paragraph_list: list[Paragraph]):
    if len(text) <= self._max_paragraph_len:
      splited_paragraph_list.append(Paragraph(text, index))
      return

    for retuned_text in self._retune_paragraph(split_paragraph(text)):
      splited_paragraph_list.append(Paragraph(
        text=retuned_text,
        index=index,
      ))

  def _retune_paragraph(self, texts: list[str]) -> Generator[str, None, None]:
    buffer: list[str] = []
    buffer_len: int = 0

    for text in texts:
      if buffer_len + len(text) <= self._max_paragraph_len:
        buffer.append(text)
        buffer_len += len(text)
      else:
        if buffer_len > 0:
          yield "".join(buffer)
          buffer.clear()
          buffer_len = 0

        while len(text) > self._max_paragraph_len:
          head_text = text[:self._max_paragraph_len]
          text = text[self._max_paragraph_len:]
          yield head_text
        
        if len(text) > 0:
          buffer.append(text)
          buffer_len += len(text)
    
    if buffer_len > 0:
      yield "".join(buffer)