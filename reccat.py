import os
import sys

#Just recursive cat

def print_file_contents(directory, extensions, exclude_folders):
    for root, dirs, files in os.walk(directory):
        # Remove excluded directories from search
        dirs[:] = [d for d in dirs if d not in exclude_folders]

        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                print("\nPrinting content of file:", os.path.join(root, file))
                with open(os.path.join(root, file), 'r', errors='replace') as f:
                    print(f.read())
                print("\n--- End of", file, "---\n")

if __name__ == "__main__":
    folder_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print("The specified path does not exist or is not a directory.")
        sys.exit()

    # print("Tree structure of the current folder:")
    # os.system(f"tree {folder_path}")

    extensions = ['.py', '.js', '.html', '.css']
    exclude_folders = ['venv', '.git', '.idea', 'tests']
    print_file_contents(folder_path, extensions, exclude_folders)
