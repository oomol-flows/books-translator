import re
import json

from lxml import etree

from ..transalter import Translate
from .group import ParagraphsGroup
from .utils import create_node, escape_ascii

class _XML:
  def __init__(self, page_content: str, parser: etree.HTMLParser):
    regex = r"^<\?xml.*\?>"
    match = re.match(regex, page_content)
    xml = re.sub(regex, "", page_content)

    if match:
      self.head = match.group()
    else:
      self.head = ""

    self.root = etree.fromstring(xml, parser=parser)
    self.nsmap: dict = self.root.nsmap.copy()
    self.root.nsmap.clear()

  def encode(self) -> str:
    for key, value in self.nsmap.items():
      self.root.nsmap[key] = value

    text = etree.tostring(self.root, method="html", encoding="utf-8")
    text = text.decode("utf-8")

    # HTML 规定了一系列自闭标签，这些标签需要改成非自闭的，因为 EPub 格式不支持
    # https://www.tutorialspoint.com/which-html-tags-are-self-closing
    text = re.sub(r"<((img|br|hr|input|col|base|meta|link|area)[^>]*?)(?<!/)>", r"<\1/>", text)
    text = self.head + text

    return text

class EpubHandler:
  def __init__(
    self,
    translate: Translate,
    max_paragraph_characters: int,
    clean_format: bool,
  ):
    self._translate: Translate = translate
    self.parser = etree.HTMLParser(recover=True)
    self.clean_format = clean_format
    self.group = ParagraphsGroup(
      max_paragraph_len=max_paragraph_characters,
      # https://support.google.com/translate/thread/18674882/how-many-words-is-maximum-in-google?hl=en
      max_group_len=5000,
    )

  def translate(self, text_list: list[str]):
    to_text_list: list[str] = []
    for text_list in self.group.split_text_list(text_list):
      for text in self._emit_translation_task(text_list):
        to_text_list.append(text)
    return to_text_list

  def translate_page(self, file_path: str, page_content: str):
    xml = _XML(page_content, self.parser)
    source_dom_text_list: list[str] = []
    p_doms = list(xml.root.xpath('//p'))

    for p_dom in p_doms:
      bin_text = etree.tostring(p_dom, method="html", encoding="utf-8")
      source_dom_text_list.append(bin_text.decode("utf-8"))

    translated_group_list = self._translate_group_by_group(file_path, source_dom_text_list)
    to_target_text_pair_map: dict[int, list[list[str]]] = {}

    for (source_text_list, target_text_list, index_list) in translated_group_list:
      for i, target_text in enumerate(target_text_list):
        source_text = source_text_list[i]
        index = index_list[i]

        if target_text != "":
          if self.clean_format:
            target_text = escape_ascii(target_text)
          else:
            target_text = self._clean_p_tag(target_text)

        pair = [source_text, target_text]

        if index in to_target_text_pair_map:
          to_target_text_pair_map[index].append(pair)
        else:
          to_target_text_pair_map[index] = [pair]

    for index, p_dom in enumerate(p_doms):
      if index in to_target_text_pair_map:
        new_p_doms = []
        for pair in to_target_text_pair_map[index]:
          for text in pair:
            if text != "":
              new_p_text = self._wrap_with_p(p_dom, text)
              new_p_dom = create_node(new_p_text, parser=self.parser)
              new_p_doms.append(new_p_dom)
    
        parent_dom = p_dom.getparent()
        index_at_parent = parent_dom.index(p_dom)

        for new_p_dom in reversed(new_p_doms):
          parent_dom.insert(index_at_parent, new_p_dom)
        parent_dom.remove(p_dom)

    return xml.encode()

  def _translate_group_by_group(self, file_path: str, source_text_list: list[str]):
    target_list = []
    paragraph_group_list = self.group.split_paragraphs(source_text_list)

    for index, paragraph_list in enumerate(paragraph_group_list):
      source_text_list = list(map(lambda x: self._clean_p_tag(x.text), paragraph_list))
      target_text_list = self._translate_text_list(source_text_list)
      index_list = list(map(lambda x: x.index, paragraph_list))

      # 长度为 2 的数组来源于裁剪，不得已，此时它的后继的首位不会与它重复，故不必裁剪
      if index > 0 and len(paragraph_group_list[index - 1]) > 2:
        source_text_list.pop(0)
        target_text_list.pop(0)
        index_list.pop(0)

      if index < len(paragraph_group_list) - 1 and len(paragraph_list) > 2:
        source_text_list.pop()
        target_text_list.pop()
        index_list.pop()

      target_list.append((source_text_list, target_text_list, index_list))
      print(f"Translate completed: {file_path} task {index + 1}/{len(paragraph_group_list)}")

    return target_list

  def _translate_text_list(self, source_text_list):
    target_text_list = [""] * len(source_text_list)
    to_translated_text_list = []
    index_list = []

    for index, text in enumerate(source_text_list):
      if self._is_not_empty(text):
        text = f"<p>{text}</p>"
        dom = create_node(text, parser=self.parser)

        if self.clean_format:
          unformat_text = self._unformat(dom)
          text = unformat_text
        else:
          # 一些英语书籍会用 span 进行缩进排版，这些会影响翻译，应该删除
          changed = self._try_to_clean_space(dom)
          if changed:
            bin_text = etree.tostring(dom, method="html", encoding="utf-8")
            text = bin_text.decode("utf-8")
          unformat_text = self._unformat(dom)

        if self._is_not_empty(unformat_text):
          to_translated_text_list.append(text)
          index_list.append(index)

    for i, text in enumerate(self._emit_translation_task(to_translated_text_list)):
      index = index_list[i]
      target_text_list[index] = text

    return target_text_list

  def _emit_translation_task(self, source_text_list) -> list[str]:
    indexes = []
    contents = []

    for index, source_text in enumerate(source_text_list):
      if source_text != "" and not re.match(r"^[\s\n]+$", source_text):
        indexes.append(index)
        contents.append(source_text)
    
    target_text_list = [""] * len(source_text_list)

    if len(contents) > 0:
      try:
        for i, text in enumerate(self._translate(contents)):
          index = indexes[i]
          target_text_list[index] = text

      except Exception as e:
        print("translate contents failed:")
        for content in contents:
          print(content)
        raise e

    return target_text_list

  def _try_to_clean_space(self, dom):
    span_list = []
    changed = False
    for dom in dom.xpath(".//span"):
      span_list.append(dom)
    for dom in span_list:
      text_bin = etree.tostring(dom, method="text", encoding="utf-8", pretty_print=False)
      if self._is_not_empty(text_bin.decode("utf-8")):
        continue
      tail = dom.tail
      if tail is None:
        tail = " "
      else:
        tail = f" {tail}"
      dom.tail = tail
      dom.getparent().remove(dom)
      changed = True
    return changed

  def _unformat(self, dom):
    return etree.tostring(dom, method="text", encoding="utf-8", pretty_print=False).decode("utf-8")

  def _is_not_empty(self, text: str) -> bool:
    return not re.match(r"^[\s\n]*$", text)

  def _wrap_with_p(self, p_dom, text: str) -> str:
    attributes_list = []
    for key, value in p_dom.attrib.items():
      json_value = json.dumps(value)
      attributes_list.append(f"{key}={json_value}")
    if len(attributes_list) > 1:
      attributes = " ".join(attributes_list)
      return f"<p {attributes}>{text}</p>"
    else:
      return f"<p>{text}</p>"

  def _clean_p_tag(self, text: str) -> str:
    text = re.sub(r"^[\s\n]*<p[^>]*>", "", text)
    text = re.sub(r"</\s*p>[\s\n]*$", "", text)
    text = re.sub(r"[\s\n]+", " ", text)
    return text