from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional
from src.utils.logger import setup_logger, log_with_context

logger = setup_logger(__name__)

ChangeType = Literal["addition", "deletion", "context"]


@dataclass
class LineChange:
    type: ChangeType
    line: Optional[int]
    content: str


@dataclass
class FileDiff:
    file: str
    changes: List[LineChange]


def parse_unified_diff(diff_text: str) -> List[FileDiff]:
    """Parse a unified diff string into a list of FileDiff objects.
    """
    logger.info("Starting diff parsing")
    
    lines = diff_text.splitlines()
    file_diffs: List[FileDiff] = []

    current_file: Optional[FileDiff] = None
    new_line_no: Optional[int] = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Start of a new file diff (Git style)
        if line.startswith("diff --git "):
            if current_file is not None:
                file_diffs.append(current_file)
            current_file = None
            new_line_no = None
            i += 1
            continue

        # File path from +++ line (use new file path)
        if line.startswith("+++ "):
            # format: +++ b/path/to/file or +++ /dev/null
            path_part = line[4:].strip()
            if path_part == "/dev/null":
                file_path = "<deleted-file>"
            else:
                # Strip leading a/ or b/ if present
                if path_part.startswith("a/") or path_part.startswith("b/"):
                    file_path = path_part[2:]
                else:
                    file_path = path_part

            current_file = FileDiff(file=file_path, changes=[])
            i += 1
            continue

        # Hunk header: @@ -old_start,old_count +new_start,new_count @@
        if line.startswith("@@ ") and current_file is not None:
            try:
                header = line.split("@@")[1].strip()
                # header like: -1,3 +1,4 or -10 +12
                parts = header.split()
                new_part = [p for p in parts if p.startswith("+")][0]
                # remove leading '+' and possible ',count'
                new_start_str = new_part[1:].split(",")[0]
                new_line_no = int(new_start_str)
            except Exception:
                new_line_no = None
            i += 1
            continue

        # Inside a hunk: track additions, deletions, context
        if current_file is not None and new_line_no is not None and line:
            prefix = line[0]
            content = line[1:]

            if prefix == "+":
                current_file.changes.append(
                    LineChange(type="addition", line=new_line_no, content=content)
                )
                new_line_no += 1
            elif prefix == "-":
                current_file.changes.append(
                    LineChange(type="deletion", line=None, content=content)
                )
                # deletions do not advance new_line_no
            elif prefix == " " or prefix == "\t":
                current_file.changes.append(
                    LineChange(type="context", line=new_line_no, content=content)
                )
                new_line_no += 1

        i += 1

    if current_file is not None:
        file_diffs.append(current_file)

    # Calculate statistics
    total_files = len(file_diffs)
    total_additions = sum(
        len([c for c in fd.changes if c.type == "addition"]) for fd in file_diffs
    )
    total_deletions = sum(
        len([c for c in fd.changes if c.type == "deletion"]) for fd in file_diffs
    )
    total_changes = sum(len(fd.changes) for fd in file_diffs)
    
    log_with_context(
        logger, "info", "Diff parsing completed",
        files_parsed=total_files,
        total_changes=total_changes,
        additions=total_additions,
        deletions=total_deletions
    )

    return file_diffs
