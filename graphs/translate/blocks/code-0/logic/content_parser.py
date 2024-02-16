from lxml import etree

class Spine:
  def __init__(self, item):
    self.href = item.get("href")
    self.media_type = item.get("media-type")

class EpubContent:
  def __init__(self, file_path):
    self._tree = etree.parse(file_path)
    self._namespaces = { "ns": self._tree.getroot().nsmap.get(None) }
    self._spine = self._tree.xpath("//ns:spine", namespaces=self._namespaces)[0]
    self._manifest = self._tree.xpath("//ns:manifest", namespaces=self._namespaces)[0]

  @property
  def spines(self):
    idref_dict = {}
    index = 0
  
    for child in self._spine.iterchildren():
      id = child.get("idref")
      idref_dict[id] = index
      index += 1

    items = [None for _ in range(index)]
    spines = []

    for child in self._manifest.iterchildren():
      id = child.get("id")
      if id in idref_dict:
        index = idref_dict[id]
        items[index] = child
    
    for item in items:
      if item is not None:
        spines.append(Spine(item))

    return spines
