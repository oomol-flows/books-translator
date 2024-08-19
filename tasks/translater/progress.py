from typing import Callable
from oocana import Context

SubProgress = Callable[[float], None]

class Progress:
  def __init__(self, context: Context):
    self._context: Context = context
    self._progress: list[tuple[float, float]] = []

  def sub(self, rate: float) -> SubProgress:
    index: int = len(self._progress)
    self._progress.append((rate, 0.0))
    return lambda progress: self._submit(index, progress)

  def _submit(self, index: int, progress: float):
    rate = self._progress[index][0]
    self._progress[index] = (rate, progress)
    sum_progress: float = 0.0
    for rate, progress_rate in self._progress:
      sum_progress += rate * progress_rate
    self._context.report_progress(
      round(sum_progress * 100.0)
    )