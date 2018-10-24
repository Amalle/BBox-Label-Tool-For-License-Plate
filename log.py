import os
import time

def logIni(file_path):
    with open(file_path,'w') as f:
        f.write('\n')

def writeLog(file_path, str):
    with open(file_path,'a') as f:
        f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()))
        f.write(str)
        f.write('\n')
