from oocana import Context

# "in", "out" is the default node key.
# Redefine the name and type of the node, change it manually below.
# Click on the gear(⚙) to configure the input output UI

def main(inputs: dict, context: Context):
  # inputs.get("in") -> help you get node input value

  # preview pandas dataframe
  # context.preview(df)

  # context.preview({
  #   # type can be "image", "video", "audio", "markdown", "table", "iframe"
  #   "type": "image",
  #   # data can be file path, base64, pandas dataframe
  #   "data": "",
  # })

  return { "out": inputs }