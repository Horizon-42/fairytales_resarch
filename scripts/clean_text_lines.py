import os

def clean_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gb18030') as f:
                content = f.read()
        except:
            print(f"Failed to read {filepath}")
            return

    lines = [line.strip() for line in content.splitlines()]
    non_empty_lines = [line for line in lines if line]

    if not non_empty_lines:
        print(f"Skipping empty file: {filepath}")
        return

    # Remove the first line (Title) as requested
    if len(non_empty_lines) > 0:
        body = non_empty_lines[1:]
    else:
        body = []

    new_content = "\n".join(body) + "\n"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Processed (title removed): {filepath}")

def main():
    base_dir = "datasets"
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".txt"):
                filepath = os.path.join(root, file)
                clean_file(filepath)

if __name__ == "__main__":
    main()
