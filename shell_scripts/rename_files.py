import os

def rename_files_in_directory(directory, old_text, new_text):
    for foldername, subfolders, filenames in os.walk(directory):
        for filename in filenames:
            if old_text in filename:
                old_filepath = os.path.join(foldername, filename)
                new_filename = filename.replace(old_text, new_text)
                new_filepath = os.path.join(foldername, new_filename)

                os.rename(old_filepath, new_filepath)
                print(f"Renamed {old_filepath} to {new_filepath}")

# Example Usage
directory_to_rename = input('Enter the directory path: ')
text_to_replace = input('Enter the text you want to replace: ')
replacement_text = input('Enter the replacement text: ')

rename_files_in_directory(directory_to_rename, text_to_replace, replacement_text)
