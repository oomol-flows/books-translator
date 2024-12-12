import io
import re

_MinSentenceLen = 12
_BracketDict: dict = {
  "[": "]",
  "(": ")",
  "\"": "\"",
  "'": "'",
  "“": "”",
  "‘": "’",
  "「": "」",
  "【": "】",
  "（": "）",
}

_SplitSentenceSet: set = {
  ",",
  ":",
}
_StopSentenceSet: set = {
  "?",
  "!",
  "。",
  "；",
  "？",
  "！",
  ";",
}

def split_paragraph(text: str) -> list:
  words_in_sentence = 0
  is_read_words = False
  bracket_stack = []
  sentences = []
  buffer = io.StringIO()

  for char in text:
    buffer.write(char)

    if char in _SplitSentenceSet:
      words_in_sentence = 0
    elif is_read_words and re.match(r"^[\s\n]$", char):
      words_in_sentence += 1
      is_read_words = False
    elif not is_read_words and not re.match(r"^[\s\n]$", char):
      is_read_words = True

    if len(bracket_stack) > 0 and char == bracket_stack[-1]:
      bracket_stack.pop()
    elif char in _BracketDict:
      bracket_stack.append(_BracketDict[char])
    elif len(bracket_stack) == 0 and (
      char in _StopSentenceSet
    or (
      words_in_sentence > 1 and char == "."
    )):
      words_in_sentence = 0
      buffer.flush()
      sentences.append(buffer.getvalue())
      buffer.close()
      buffer = io.StringIO()

  last_sentence = buffer.getvalue()
  buffer.close()

  if len(last_sentence):
    sentences.append(last_sentence)

  target_sentences = []
  last_append_index = -1

  for sentence in sentences:
    if last_append_index >= 0 and len(sentence) < _MinSentenceLen:
      target_sentences[last_append_index] += sentence
    else:
      last_append_index = len(target_sentences)
      target_sentences.append(sentence)

  return target_sentences