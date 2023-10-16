from glob import glob
import shutil
import os


def rename_files(source_mask, text, replace_text):
    files = glob(source_mask)
    for file in files:
        if text in file:
            target_name = file.replace(text,replace_text)
            shutil.move(file,target_name)
            print(f"File {file} moved to {target_name}")



# Example Usage
source_directory = input('Enter the source directory files mask: ')
text = input('Enter the search text in filename: ')
replace_text = input('Enter the replace text in filename: ')
if not replace_text:
    replace_text = ""

rename_files(source_directory,text,replace_text)
