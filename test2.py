
from tkinter import *
 
class Test():
    def __init__(self, master):
        self.parent = master
        e = StringVar()
        self.entry = Entry(self.parent, textvariable=e)
        self.entry.pack()
        self.entry['state'] = 'disabled'
        self.btn = Button(self.parent, text="Edit", command=self.changeState)
        self.btn.pack()
    def changeState():
        if self.entry['state'] == 'disabled':
            self.entry['state'] = 'normal'
            self.entry.
        else:
            self.entry['state'] = 'disabled'

if __name__ == '__main__':
    root = Tk()
    tool = Test(root)
    root.resizable(width=True, height=True)
    root.mainloop()