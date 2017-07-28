#!/usr/bin/python3
'''
Created on 9 mar. 2017

@author: martintc
'''


'''
Detectar si fue ejecutado desde ventana o terminal
import os
import sys

isGUI = sys.stdin.isatty()
isNotGUI = os.isatty(sys.stdout.fileno())

if os.isatty(sys.stdout.fileno()):
    # print error message text
else:
    # display GUI message

You should check that the DISPLAY environment variable is set
before going with GUI code too, since it won't work without that.
'''
import sys
import os

WINDOWED = 'DISPLAY' in os.environ and not sys.stdin.isatty()

user = 'you'

if not WINDOWED:
    user = sys.argv[1]

msg = "Hello, "+user+"!"

if WINDOWED:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("stdin", "stdin is " + str(sys.stdin.isatty()))
    messagebox.showinfo("Say Hello", msg)
else:
    print("stdin is " + str(sys.stdin.isatty()))
    print(msg)
    input()
