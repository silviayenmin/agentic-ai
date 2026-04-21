import os
from langchain_core.tools import tool

# project root → workspace
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "workspace")
)


@tool
def write_to_file():
    try:
        file_name = input(" Enter file name (e.g., demo.txt): ").strip()

        full_path = os.path.join(BASE_DIR, file_name)

        print(f" Checking path: {full_path}")

        if not os.path.isfile(full_path):
            print(" File not found in workspace.")
            return

        print("Enter content (type 'END' in new line to finish):")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)

        content = "\n".join(lines)

        with open(full_path, "w", encoding="utf-8") as file:
            file.write(content + "\n")

        print(f" Successfully written to '{full_path}'")
        return f" Successfully written to '{full_path}'"

    except Exception as e:
        print(f" Error: {e}")
        return f" Error: {e}"
