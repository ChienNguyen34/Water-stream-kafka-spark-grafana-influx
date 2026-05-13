"""
Root conftest.py cho toàn bộ tst/ — thêm producer và spark_streaming vào sys.path
để các test file không cần tự quản lý sys.path.
"""
import sys
import os

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(_ROOT, "producer"))
sys.path.insert(0, os.path.join(_ROOT, "spark_streaming"))
sys.path.insert(0, _ROOT)
