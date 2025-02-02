import os

def gather_python_files(root="."):
    """
    Walk through 'root' directory and collect all .py file paths
    except this script file itself.
    """
    this_script = os.path.abspath(__file__)
    py_files = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(".py"):
                full_path = os.path.abspath(os.path.join(dirpath, fname))
                # Skip this script itself if you don't want it included
                if full_path != this_script:
                    py_files.append(full_path)
    return py_files

def remove_consecutive_blank_lines(lines):
    """
    Given a list of lines, collapse consecutive blank lines into a single one.
    """
    new_lines = []
    previous_blank = False
    
    for line in lines:
        # Check if the line is empty or only whitespace
        if line.strip() == "":
            if not previous_blank:
                new_lines.append(line)
            previous_blank = True
        else:
            new_lines.append(line)
            previous_blank = False
    
    return new_lines

def combine_py_files(output_file="combined.py"):
    """
    Combine all .py files into a single file (default: combined.py).
    Each file is prefixed with a comment of the form:
         #/docs/<relative-path>.py
    if it's not already at the top.
    """
    py_files = gather_python_files(".")
    combined_lines = []

    for py_file in py_files:
        # Compute a relative path from current dir (.)
        relative_path = os.path.relpath(py_file, ".")
        doc_comment = f"#.\{relative_path}"

        with open(py_file, "r", encoding="utf-8") as f:
            file_lines = f.readlines()

        # Remove consecutive blank lines from the file's contents
        file_lines = remove_consecutive_blank_lines(file_lines)
        
        # Check if the file's first line is already "#/docs/<path>"
        if file_lines:
            first_line = file_lines[0].rstrip("\n")
            if first_line != doc_comment:
                combined_lines.append(doc_comment + "\n")
        else:
            # If the file is empty, we still add the doc_comment
            combined_lines.append(doc_comment + "\n")

        combined_lines.extend(file_lines)
        # Add a blank line between files so they don't mash together
        combined_lines.append("\n")

    # Finally, remove consecutive blank lines from the entire combined output
    combined_lines = remove_consecutive_blank_lines(combined_lines)

    # Write the combined output
    with open(output_file, "w", encoding="utf-8") as out:
        out.writelines(combined_lines)

if __name__ == "__main__":
    combine_py_files("combined.py")
