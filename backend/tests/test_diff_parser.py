"""Unit tests for diff parser."""

import pytest
from src.utils.diff_parser import parse_unified_diff


def test_parse_single_file_addition():
    """Test parsing a diff with a single file and additions."""
    diff = """diff --git a/test.py b/test.py
index abc123..def456 100644
--- a/test.py
+++ b/test.py
@@ -1,3 +1,5 @@
 def hello():
+    print("Hello")
+    return True
     pass
"""
    result = parse_unified_diff(diff)
    
    assert len(result) == 1
    assert result[0].file == "test.py"
    
    additions = [c for c in result[0].changes if c.type == "addition"]
    assert len(additions) == 2
    assert additions[0].content == '    print("Hello")'
    assert additions[1].content == "    return True"


def test_parse_multiple_files():
    """Test parsing a diff with multiple files."""
    diff = """diff --git a/file1.py b/file1.py
index abc..def 100644
--- a/file1.py
+++ b/file1.py
@@ -1,2 +1,3 @@
 line1
+line2
 line3
diff --git a/file2.py b/file2.py
index ghi..jkl 100644
--- a/file2.py
+++ b/file2.py
@@ -1,1 +1,2 @@
 original
+new line
"""
    result = parse_unified_diff(diff)
    
    assert len(result) == 2
    assert result[0].file == "file1.py"
    assert result[1].file == "file2.py"
    
    # Check first file has one addition
    file1_additions = [c for c in result[0].changes if c.type == "addition"]
    assert len(file1_additions) == 1
    
    # Check second file has one addition
    file2_additions = [c for c in result[1].changes if c.type == "addition"]
    assert len(file2_additions) == 1


def test_parse_additions_and_deletions():
    """Test parsing a diff with both additions and deletions."""
    diff = """diff --git a/app.py b/app.py
index old..new 100644
--- a/app.py
+++ b/app.py
@@ -5,7 +5,7 @@ def process():
     old_var = 1
-    removed_line = "delete this"
+    new_line = "add this"
     keep_this = True
"""
    result = parse_unified_diff(diff)
    
    assert len(result) == 1
    
    additions = [c for c in result[0].changes if c.type == "addition"]
    deletions = [c for c in result[0].changes if c.type == "deletion"]
    
    assert len(additions) == 1
    assert len(deletions) == 1
    assert additions[0].content == '    new_line = "add this"'
    assert deletions[0].content == '    removed_line = "delete this"'


def test_parse_empty_diff():
    """Test parsing an empty diff."""
    result = parse_unified_diff("")
    assert len(result) == 0


def test_parse_line_numbers():
    """Test that line numbers are correctly tracked."""
    diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -10,3 +10,5 @@ def func():
     existing_line
+    line_at_11 = True
+    line_at_12 = False
     another_line
"""
    result = parse_unified_diff(diff)
    
    additions = [c for c in result[0].changes if c.type == "addition"]
    assert additions[0].line == 11
    assert additions[1].line == 12
