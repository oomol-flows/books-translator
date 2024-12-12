import unittest

try:
  loader = unittest.TestLoader()
  suite = loader.discover("./tests")
  runner = unittest.TextTestRunner()
  result = runner.run(suite)
  if not result.wasSuccessful():
    exit(1)
except Exception as e:
  print(e)
  exit(1)