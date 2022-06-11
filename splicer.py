from tkinter import filedialog
import numpy as np
from scipy.io import wavfile

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import os

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

root = tk.Tk()
root.title("Audio Splicing Tool")
root.withdraw()

options = {'padx':5, 'pady':5}
# Frames
frm_data = ttk.Frame(root)
frm_data.grid(column=0, row=0, **options)

frm_submit = ttk.Frame(root)
frm_submit.grid(column=1,row=0)

# Widgets
lbl_files = ttk.Label(frm_data, text="Number of files to return:")
lbl_files.grid(column=0, row=0, **options, sticky="nw")
ent_files = ttk.Entry(frm_data, width=5)
ent_files.grid(column=1, row=0, **options, sticky="nw")
ent_files.insert(0, 8)

lbl_splice = ttk.Label(frm_data, text="Offset time (in seconds):")
lbl_splice.grid(column=0, row=1)
ent_splice = ttk.Entry(frm_data, width=5)
ent_splice.grid(column=1,row=1)
ent_splice.focus()

# class AudioFile:
#     def __init__(self,audio_data)


def mnu_import_files():
    global audio_file
    global fs
    global filename
    """ For multiple files 
    # Returns a tuple of names
    filenames = filedialog.askopenfilenames(initialdir=_thisDir)
    file_list = []
    for file in filenames:
        fs, audio_file = wavfile.read(file)
        file_list.append(audio_file)
    all_files = np.array(file_list,dtype=object)
    sd.play(all_files[0].T,fs)
    """
    #filename = filedialog.askopenfilename(initialdir=_thisDir)
    filename = filedialog.askopenfilename()
    fs, audio_file = wavfile.read(filename)

def do_splice():
    global audio_file
    num_files =  int(ent_files.get())
    splice_time = int(ent_splice.get())
    #print(f"Number of files: {num_files}")  
    #print(f"Splice time: {splice_time}")
    sigdur = len(audio_file) / fs

    spliced_list = []
    len_list = []
    for idx in range(1, num_files+1):
        cut_time = splice_time * idx
        cut_in_samples = cut_time * fs
        sig = audio_file[cut_in_samples:]
        #print(f"Length of trimmed file: {len(sig)}")
        spliced_list.append(sig)
        len_list.append(len(sig))
    spliced_array = np.array(spliced_list,dtype=object)
    #print(f"Shape of spliced_array: {spliced_array.shape}")
    min_len = min(len_list)
    #print(f"Minimum length: {min_len}")
    #return spliced_array, min_len
    do_truncate(spliced_array, min_len)

def do_truncate(spliced_array, min_len):
    just_name = filename.split('/')[-1]
    just_path = filename.split(just_name)[0]
    for idx in range(len(spliced_array)):
        sig = spliced_array[idx][:min_len]
        #print(len(sig))
        file_name = just_path + str(idx+1) + ".wav"
        wavfile.write(file_name, fs, sig)
    messagebox.showinfo(
        title="Success!",
        message=(f"Successfully created {len(spliced_array)} files!")
    )

btn_submit = ttk.Button(frm_submit, text="Chop!", command=do_splice)
btn_submit.grid(column=0, row=0, **options)


# create a menubar
menubar = tk.Menu(root)
root.config(menu=menubar)
# create the File menu
file_menu = tk.Menu(menubar, tearoff=False)
# add menu items to the File menu
# file_menu.add_command(
#     label='New Session'
#     #command=startup_win
# )
file_menu.add_command(
    label="Import Files",
    command=mnu_import_files
)
file_menu.add_separator()
file_menu.add_command(
    label='Exit',
    command=root.destroy
)
# add the File menu to the menubar
menubar.add_cascade(
    label="File",
    menu=file_menu
)
# # Create Tools menu
# tools_menu = tk.Menu(
#     menubar,
#     tearoff=0
# )
# # Add items to the Tools menu
# tools_menu.add_command(
#     label='Audio Devices',
#     command=list_audio_devs)
# tools_menu.add_command(
#     label='Calibrate',
#     command=mnuCalibrate)
# # Add Tools menu to the menubar
# menubar.add_cascade(
#     label="Tools",
#     menu=tools_menu
# )
# create the help menu
help_menu = tk.Menu(
    menubar,
    tearoff=0
)
# add items to the Help menu
# help_menu.add_command(
#     label='Help',
#     command=lambda: messagebox.showerror(
#         title="Sorry...",
#         message="Not available yet!"
#     ))
help_menu.add_command(
    label='About',
    command=lambda: messagebox.showinfo(
        title="About Audio Splicer",
        message="Version: 1.0.0\nWritten by: Travis M. Moore\nCreated: 06/10/2022\nLast Updated: 06/10/2022"
    )
)
# add the Help menu to the menubar
menubar.add_cascade(
    label="Help",
    menu=help_menu
)


# Center root based on new size
root.update_idletasks()
#root.attributes('-topmost',1)
window_width = root.winfo_width()
window_height = root.winfo_height()
#window_width = 600
#window_height=200
# get the screen dimension
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
# find the center point
center_x = int(screen_width/2 - window_width / 2)
center_y = int(screen_height/2 - window_height / 2)
# set the position of the window to the center of the screen
root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
root.resizable(False, False)
root.deiconify()


root.mainloop()
