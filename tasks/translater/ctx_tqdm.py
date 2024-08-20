from tqdm.std import tqdm as std_tqdm
from oocana import Context

class tqdm(std_tqdm):
  def __init__(self, context: Context, *args, **kwargs):
    self._context: Context = context
    super().__init__(*args, **kwargs)

  def clear(self, *_, **__):
    pass

  def display(self, *_, **__):
    n = self.n
    total = self.total
    p = round(n * 100.0 / total)
    self._context.report_progress(p)