#!/usr/bin/env python3
"""
Tinyhttpd Python - main entry point
Usage: python3 main.py [port]
"""
import sys
import os

# 确保模块路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.server import run

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(port=port, htdocs_root='htdocs')
