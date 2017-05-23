import unittest2 as unittest
import sys

sys.path.append('tests')
sys.path.append('plugin/python')
vdebugLoader = unittest.TestLoader()
suites = vdebugLoader.discover('tests','test_*.py')
result = unittest.TextTestRunner().run(suites)
if result.failures:
    exit(1)
elif result.errors:
    exit(2)
