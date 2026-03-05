#!/usr/bin/env python3
"""简易测试runner，兼容无pytest环境"""
import unittest
import sys
import os

def run_module_tests(module_path=None):
    if module_path:
        loader = unittest.TestLoader()
        suite = loader.discover(module_path, pattern='test_*.py')
    else:
        loader = unittest.TestLoader()
        suite = loader.discover('.', pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    sys.exit(run_module_tests(path))
