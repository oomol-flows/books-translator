import re
import os
import json

from lxml import etree
from google.cloud import translate
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

    # TODO: 替换成更完善的自闭检测
    # link 可能生成非自闭 tag，对 epub 是非法，此处用正则替换掉非自闭型
    text = re.sub(r"<((link|meta)[^>]*?)(?<!/)>", r"<\1/>", text)
    text = self.head + text

    return text

# https://cloud.google.com/translate/docs/advanced/translate-text-advance?hl=zh-cn
class Translator:
  def __init__(
    self, 
    project_id: str, 
    source_language_code: str, 
    target_language_code: str,
    max_paragraph_characters: int,
    clean_format: bool,
  ):
    self.client = translate.TranslationServiceClient()
    self.parser = etree.HTMLParser(recover=True)
    self.project_id = project_id
    self.source_language_code = source_language_code
    self.target_language_code = target_language_code
    self.max_paragraph_characters = max_paragraph_characters
    self.clean_format = clean_format

  def translate(self, text):
    translated_text_list = self._translate_by_google([text], "text/plain")
    if len(translated_text_list) > 0:
      return translated_text_list[0]
    else:
      return text

  def translate_page(self, file_path: str, page_content: str):
    xml = _XML(page_content, self.parser)
    source_dom_text_list: list[str] = []
    p_doms = list(xml.root.xpath('//p'))

    __debug_duplicated_texts_set = set()
    __debug_found_duplicated_set = set()

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

        if target_text != "":
          if target_text in __debug_duplicated_texts_set:
              __debug_found_duplicated_set.add(target_text)
          __debug_duplicated_texts_set.add(target_text)

    for index, p_dom in enumerate(p_doms):
      if index in to_target_text_pair_map:
        new_p_doms = []
        for pair in to_target_text_pair_map[index]:
          for text in pair:
            if text != "":
              new_p_dom = create_node(f"<p>{text}</p>", parser=self.parser)
              new_p_doms.append(new_p_dom)
    
        parent_dom = p_dom.getparent()
        index_at_parent = parent_dom.index(p_dom)

        for new_p_dom in reversed(new_p_doms):
          parent_dom.insert(index_at_parent, new_p_dom)
        parent_dom.remove(p_dom)

    if len(__debug_found_duplicated_set) > 0:
      file_name = os.path.basename(file_path)
      log_path = f"/app/workspace/source/{file_name}.json"
      json_str = json.dumps(
        {
          "duplicated": list(__debug_found_duplicated_set),
          "source": source_text_list,
        }, 
        indent=4,
      )
      with open(log_path, "w") as file:
          file.write(json_str)

    return xml.encode()

  def _translate_group_by_group(self, file_path: str, source_text_list: list[str]):
    group = ParagraphsGroup(
      max_paragraph_len=self.max_paragraph_characters,
      # https://support.google.com/translate/thread/18674882/how-many-words-is-maximum-in-google?hl=en
      max_group_len=5000,
    )
    target_list = []
    paragraph_group_list = group.split(source_text_list)

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
        check_again = False

        if self.clean_format:
          dom = create_node(text, parser=self.parser)
          text = etree.tostring(dom, method="text", encoding="utf-8", pretty_print=False)
          text = text.decode("utf-8")
          check_again = True

        if not check_again or self._is_not_empty(text):
          to_translated_text_list.append(text)
          index_list.append(index)
    
    if self.clean_format:
      mime_type = "text/plain"
    else:
      mime_type = "text/html"

    for i, text in enumerate(self._translate_by_google(to_translated_text_list, mime_type)):
      index = index_list[i]
      target_text_list[index] = text

    return target_text_list

  def _is_not_empty(self, text: str) -> bool:
    return not re.match(r"^[\s\n]*$", text)

  def _clean_p_tag(self, text: str) -> str:
    text = re.sub(r"^[\s\n]*<p[^>]*>", "", text)
    text = re.sub(r"</\s*p>[\s\n]*$", "", text)
    text = re.sub(r"[\s\n]+", " ", text)
    return text

  def _translate_by_google(self, source_text_list, mime_type) -> list[str]:
    indexes = []
    contents = []

    for index, source_text in enumerate(source_text_list):
      if source_text != "" and not re.match(r"^[\s\n]+$", source_text):
        indexes.append(index)
        contents.append(source_text)
    
    target_text_list = [""] * len(source_text_list)

    if len(contents) > 0:
      location = "global"
      parent = f"projects/{self.project_id}/locations/{location}"

      try:
        response = self.client.translate_text(
          request={
            "parent": parent,
            "contents": contents,
            "mime_type": mime_type,
            "source_language_code": self.source_language_code,
            "target_language_code": self.target_language_code,
          }
        )
      except Exception as e:
        print("translate contents failed:")
        for content in contents:
          print(content)
        raise e

      for i, translation in enumerate(response.translations):
        index = indexes[i]
        target_text_list[index] = translation.translated_text
    
    return target_text_list