import os
import shutil


def move_files_with_extensions(source_dir, target_dir, extensions):
    # Ensure the file extensions are formatted correctly
    for i, ext in enumerate(extensions):
        if not ext.startswith('.'):
            extensions[i] = '.' + ext

    # Walking through the source directory
    for foldername, subfolders, filenames in os.walk(source_dir):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                # Create the same structure in the target directory
                structure = os.path.join(target_dir, os.path.relpath(foldername, source_dir))
                if not os.path.isdir(structure):
                    os.makedirs(structure)

                source_file = os.path.join(foldername, filename)
                target_file = os.path.join(structure, filename)

                # Move the file
                shutil.move(source_file, target_file)
                print(f"Moved {source_file} to {target_file}")


# Example Usage
source_directory = input('Enter the source directory path: ')
target_directory = input('Enter the target directory path: ')
extensions_input = input('Enter the file extensions separated by commas and/or spaces (e.g. .txt, .jpg .png): ')

# Split extensions by comma and/or space and then strip any leading/trailing spaces
extensions = [ext.strip() for ext in extensions_input.replace(',', ' ').split()]
move_files_with_extensions(source_directory, target_directory, extensions)
