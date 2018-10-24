import os

def writeLog(file_path, str):
    with open(file_path,'a') as f:
        f.writelines(str)
