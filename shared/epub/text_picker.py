from __future__ import annotations
from typing import Any, Literal
from lxml.etree import tostring, Element

_TEXT_TAG = (
  "h1", "h2", "h3", "h4", "h5", "h6",
  "a", "p", "span", "em", "strong", "blockquote", 
  "pre", "code", "hr", "label",
)
_BAN_TO_STRING_TAG = (
  "title", "style", "css", "script", "metadata"
)

class _BaseDom:
  def __init__(self, dom, children: list[WrappedDom] = []):
    self.dom: Any = dom
    self.children: list[WrappedDom] = children
    self._should_child_dom_to_string: bool | None = None

  def to_string(self, method: Literal["html", "text"]) -> str:
    bin = tostring(self.dom, method=method, encoding="utf-8", pretty_print=False)
    return bin.decode("utf-8")

  @property
  def should_child_dom_to_string(self) -> bool:
    if self._should_child_dom_to_string is None:
      self._should_child_dom_to_string = self._check_should_child_dom_to_string()
    return self._should_child_dom_to_string

  def _check_should_child_dom_to_string(self) -> bool:
    if isinstance(self, TextDom):
      return True
    else:
      has_child = False
      for child in self.children:
        has_child = True
        if isinstance(child, TreeDom):
          return False
      return has_child

class TreeDom(_BaseDom):
  pass

class TextDom(_BaseDom):
  pass

WrappedDom = str | _BaseDom

class TextPicker:
  def __init__(self, root, method: Literal["html", "text"]):
    self._root = root
    self._method: Literal["html", "text"] = method
    self._wrapped_root: _BaseDom | None = None
    self._inserted_none_counts: list[int] = []

  def pick_texts(self) -> list[str]:
    texts: list[str] = []

    self._wrapped_root = self._wrap_dom(self._root)
    self._collect_texts(self._wrapped_root, texts)

    inserted_none_count: int = 0
    picked_texts: list[str] = []

    for text in texts:
      if self._is_not_empty_str(text):
        picked_texts.append(text)
        self._inserted_none_counts.append(inserted_none_count)
        inserted_none_count = 0
      else:
        inserted_none_count += 1

    if inserted_none_count > 0:
      self._inserted_none_counts.append(inserted_none_count)

    return picked_texts

  def append_texts(self, texts: list[str]):
    if self._wrapped_root is None:
      raise Exception("should call pick_texts before")

    target_texts: list[str | None] = []

    for i, count in enumerate(self._inserted_none_counts):
      for _ in range(count):
        target_texts.append(None)
      if i < len(texts):
        target_texts.append(texts[i])

    target_texts.reverse() # to pop text from last to first
    self._append_texts_after_dom(target_texts, self._wrapped_root)

  def to_string(self) -> str:
    bin = tostring(self._root, method="html", encoding="utf-8", pretty_print=False)
    return bin.decode("utf-8")

  def _wrap_dom(self, dom) -> _BaseDom:
    children: list[WrappedDom] = []
    has_tree_children: bool = False

    if self._is_not_empty_str(dom.text):
      children.append(dom.text)

    for child in dom.getchildren():
      wraped_child = self._wrap_dom(child)
      children.append(wraped_child)
      if isinstance(wraped_child, TreeDom):
        has_tree_children = True
      if self._is_not_empty_str(child.tail):
        children.append(child.tail)

    if not has_tree_children and \
       self._is_text_tag(dom.tag):
      return TextDom(dom, children)
    else:
      return TreeDom(dom, children)

  def _collect_texts(self, wrapped_dom: _BaseDom, texts: list[str]):
    if self._is_ban_to_string_tag(wrapped_dom.dom.tag):
      return
    if wrapped_dom.should_child_dom_to_string:
      texts.append(wrapped_dom.to_string(self._method))
    else:
      for child in wrapped_dom.children:
        if isinstance(child, str):
          texts.append(child)
        else:
          self._collect_texts(child, texts)

  def _append_texts_after_dom(self, texts: list[str | None], wrapped_dom: _BaseDom) -> Any | None:
    if self._is_ban_to_string_tag(wrapped_dom.dom.tag):
      return None

    if wrapped_dom.should_child_dom_to_string:
      text = texts.pop()
      if text is None:
        return None
      return self._append_text_after_dom(wrapped_dom.dom, text)

    else:
      last_child = None
      for child in wrapped_dom.children:
        if isinstance(child, str):
          text = texts.pop()
          if text is None:
            text = child
          else:
            text = f"{child}\n{text}"
          if last_child is None:
            wrapped_dom.dom.text = text # html safety
          else:
            last_child.tail = text
        else:
          append_dom = self._append_texts_after_dom(texts, child)
          if append_dom is not None:
            last_child = append_dom

      return wrapped_dom.dom

  def _append_text_after_dom(self, dom, text: str) -> Any | None:
    new_dom = Element(dom.tag)
    new_dom.text = text  # html safety
    for key, value in dom.attrib.items():
      new_dom.attrib[key] = value

    parent = dom.getparent()
    if parent is None:
      return None # cannot do anything

    index = parent.getchildren().index(dom)
    parent.insert(index+1, new_dom)
    dom.tail = None
    return new_dom

  def _is_text_tag(self, tag: str) -> bool:
    global _TEXT_TAG
    return tag in _TEXT_TAG

  def _is_ban_to_string_tag(self, tag: str) -> bool:
    global _BAN_TO_STRING_TAG
    return tag in _BAN_TO_STRING_TAG

  def _is_not_empty_str(self, text: str | None) -> bool:
    if text is None:
      return False
    for char in text:
      if char != " " and char != "\n":
          return True
    return False