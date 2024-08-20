import io

from .paragraph_sliter import split_paragraph

class Paragraph:
  def __init__(self, text: str, index: int):
    self.text: str = text
    self.index: int = index

class ParagraphsGroup:
  def __init__(self, max_paragraph_len: int, max_group_len: int):
    self.max_paragraph_len: int = max_paragraph_len
    self.max_group_len: int = max_group_len

  def split_text_list(self, text_list: list[str]) -> list[list[str]]:
    splited_text_list: list[list[str]] = []
    current_text_list: list[str] = []
    current_len = 0

    for text in text_list:
      if len(text) > self.max_group_len:
        text = text[:self.max_group_len]

      if current_len + len(text) > self.max_group_len:
        splited_text_list.append(current_text_list)
        current_text_list = []
        current_len = 0
      
      current_text_list.append(text)
      current_len += len(text)

    if len(current_text_list) > 0:
      splited_text_list.append(current_text_list)

    return splited_text_list

  def split_paragraphs(self, text_list: list[str]) -> list[list[Paragraph]]:
    splited_paragraph_list: list[Paragraph] = []

    for index, text in enumerate(text_list):
      self._collect_text(index, text, splited_paragraph_list)

    sum_len = 0
    self_paragraphs_count = 0
    grouped_paragraph_list: list[list[Paragraph]] = []
    current_paragraph_list: list[Paragraph] = []

    for paragraph in splited_paragraph_list:
      if len(current_paragraph_list) > 0 and sum_len + len(paragraph.text) > self.max_group_len:
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
    if len(text) <= self.max_paragraph_len:
      splited_paragraph_list.append(Paragraph(text, index))
      return

    buffer = io.StringIO()
    buffer_len = 0

    for cell in split_paragraph(text):
      if len(cell) + buffer_len <= self.max_paragraph_len:
        buffer.write(cell)
        buffer_len += len(cell)
      else: 
        if buffer_len > 0:
          buffer.flush()
          splited_paragraph_list.append(Paragraph(
            text=buffer.getvalue(), 
            index=index,
          ))
          buffer.close()
          buffer = io.StringIO()
          buffer_len = 0
        while len(cell) > self.max_group_len:
          splited_paragraph_list.append(Paragraph(
            text=cell[:self.max_group_len], 
            index=index,
          ))
          cell = cell[self.max_group_len:]
        if len(cell) > 0:
          buffer.write(cell)

    if buffer_len > 0:
        buffer.flush()
        splited_paragraph_list.append(Paragraph(
          text=buffer.getvalue(), 
          index=index,
        ))
    buffer.close()