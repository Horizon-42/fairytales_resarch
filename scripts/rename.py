import os

dir_path = "datasets/ChineseTales/texts"
for filename in os.listdir(dir_path):
    if filename.endswith(".txt"):
        new_filename = "CH_"+filename
        os.rename(
            os.path.join(dir_path, filename),
            os.path.join(dir_path, new_filename)
        )