from .paragraph_sliter import split_paragraph

class ParagraphsGroup:
  def __init__(self, max_paragraph_len: int, max_group_len: int):
    self.max_paragraph_len: int = max_paragraph_len
    self.max_group_len: int = max_group_len

  def split(self, paragraph_list: list):
    splited_paragraph_list = []

    for paragraph in paragraph_list:
      if len(paragraph) > self.max_paragraph_len:
        for cell in split_paragraph(paragraph):
          splited_paragraph_list.append(cell)
      else:
        while len(paragraph) > self.max_group_len:
          splited_paragraph_list.append(paragraph[:self.max_group_len])
          paragraph = paragraph[self.max_group_len:]
        if len(paragraph) > 0:
          splited_paragraph_list.append(paragraph)

    sum_len = 0
    self_paragraphs_count = 0
    grouped_paragraph_list = []
    current_paragraph_list = []

    for paragraph in splited_paragraph_list:
      paragraph_len = len(paragraph)

      if len(current_paragraph_list) > 0 and sum_len + paragraph_len > self.max_group_len:
        grouped_paragraph_list.append(current_paragraph_list)
        sum_len = 0
        self_paragraphs_count = 0

        # 确保分组中有首尾 2 段分别与上一组、下一组重复，以让翻译具有一定上下文，增强翻译准确性
        if len(current_paragraph_list) <= 2:
          current_paragraph_list = []
        else:
          current_paragraph_list = current_paragraph_list[-2:]
          for cell in current_paragraph_list:
            sum_len += len(cell)

      sum_len += paragraph_len
      self_paragraphs_count += 1
      current_paragraph_list.append(paragraph)

    if self_paragraphs_count > 0:
      grouped_paragraph_list.append(current_paragraph_list)

    return grouped_paragraph_list
