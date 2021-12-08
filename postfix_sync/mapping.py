import re
import subprocess
from pathlib import Path


class Mapping:
    @classmethod
    def fromfile(cls, mapping_file: Path):
        input = mapping_file.read_text()
        return cls(input)

    @classmethod
    def fromtext(cls, mapping_str: str):
        return cls(mapping_str)

    def __init__(self, input: str):
        self._input = input
        self._entries = self._parse(self._input)

    def get(self, key):
        for entry in self._entries:
            if entry["key"] == key:
                return entry
        raise KeyError()

    def update(self, key, values):
        if not values:
            raise ValueError("values cannot be empty")
        entry = self.get(key)
        new_value = f"{key}\n" + "\n".join([f"\t{v}" for v in values])
        self._input = self._replace_lines(
            self._input, entry["start_line"], entry["end_line"], new_value
        )
        self._entries = self._parse(self._input)

    def tofile(self, target_file: Path):
        target_file.write_text(self._input)
        r = subprocess.check_output(
            ["/usr/sbin/postmap", str(target_file)],
            shell=False,
            stderr=subprocess.STDOUT,
        )
        if r:
            raise RuntimeError(f"Postmap validation failed!\n{r}")

    @staticmethod
    def _parse(data):
        logic_lines = []
        for no, raw_line in enumerate(data.split("\n")):
            line = raw_line.strip()
            if not line:
                continue
            if line[0] == "#":
                continue
            if raw_line[0] in (" ", "\t"):
                is_continuation_line = True
            else:
                is_continuation_line = False
            tokens = re.split(r",| |\t", line)
            is_key = not is_continuation_line
            for token in tokens:
                if not token:
                    continue
                if is_key:
                    logic_lines.append(
                        {
                            "key": token,
                            "value": [],
                            "start_line": no + 1,
                            "end_line": no + 1,
                        }
                    )
                    is_key = False
                else:
                    logic_lines[-1]["value"].append(token)
                    logic_lines[-1]["end_line"] = no + 1
        entries = logic_lines
        return entries

    @staticmethod
    def _replace_lines(input, start, end, repl):
        lines = input.split("\n")
        return "\n".join(lines[0 : start - 1] + [repl] + lines[end:])

    def __len__(self):
        return len(self._entries)

    def __getitem__(self, i):
        return self._entries[i]
