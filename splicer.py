""" Automated audio splicing tool. Create offset background 
    noise file to present uncorrelated background noise.

    Written by: Travis M. Moore
    Created: 6/10/2022
"""
# Import science packages
import numpy as np
from scipy.io import wavfile

# Import GUI packages
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

# Import system packages
import os
import time

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

# Begin root window
root = tk.Tk()
root.title("Audio Splicing Tool")
root.withdraw()

# Widget options
options = {'padx':5, 'pady':5}
# Frame options
frm_options = {'padx':10, 'pady':10}

# Frames
frm_file_name = ttk.Frame(root)
frm_file_name.grid(column=0, columnspan=3, row=3, **options, sticky='w')

frm_data = ttk.LabelFrame(root, text="File Settings")
frm_data.grid(column=0, row=1, **frm_options)

lfrm_ramps = ttk.LabelFrame(root, text="Signal Settings")
lfrm_ramps.grid(column=0, row=2, **frm_options, sticky='nsew')

#frm_sep_speakers = tk.Frame(root, width=1)
#frm_sep_speakers.grid(column=1, row=0, rowspan=3, sticky="ns")
#frm_sep_speakers["background"] = "gray"

frm_submit = ttk.Frame(root)
frm_submit.grid(column=1,row=0,rowspan=3, **options)
#frm_submit.grid(column=0,row=3)

# Widgets
loaded = tk.StringVar(value='No file selected')
lbl_file_name = ttk.Label(frm_file_name, textvariable=loaded)
lbl_file_name.grid(column=0,row=1,sticky='w', padx=5)

file_num = tk.StringVar(value="No files being written")
lbl_file_num = ttk.Label(frm_file_name, textvariable=file_num)
lbl_file_num.grid(column=0, row=0,stick='w',padx=5)

lbl_files = ttk.Label(frm_data, text="Number of files to return:")
lbl_files.grid(column=0, row=1, **options, sticky='w')
ent_files = ttk.Entry(frm_data, width=5)
ent_files.grid(column=1, row=1, **options)
ent_files.focus()

lbl_splice = ttk.Label(lfrm_ramps, text="Offset time (in seconds):")
lbl_splice.grid(column=0, row=1, **options, sticky='w')
ent_splice = ttk.Entry(lfrm_ramps, width=5)
ent_splice.grid(column=1,row=1,**options)

chk_Status = tk.IntVar(value=1)
chk_ramps = ttk.Checkbutton(lfrm_ramps,text="Ramps (20 ms)",takefocus=0,onvalue=1,offvalue=0,variable=chk_Status)
chk_ramps.grid(column=0, row=2, **options, sticky='w')


def doGate(sig,rampdur=0.02,fs=48000):
    """
        Apply rising and falling ramps to signal SIG, of 
        duration RAMPDUR. Takes a 1-channel or 2-channel 
        signal. 

            SIG: a 1-channel or 2-channel signal
            RAMPDUR: duration of one side of the gate in 
                seconds
            FS: sampling rate in samples/second

            Example: 
            [t, tone] = mkTone(100,0.4,0,48000)
            gated = doGate(tone,0.01,48000)

        Original code: Anonymous
        Adapted by: Travis M. Moore
        Last edited: Jan. 13, 2022          
    """
    gate =  np.cos(np.linspace(np.pi, 2*np.pi, int(fs*rampdur)))
    # Adjust envelope modulator to be within +/-1
    gate = gate + 1 # translate modulator values to the 0/+2 range
    gate = gate/2 # compress values within 0/+1 range
    # Create offset gate by flipping the array
    offsetgate = np.flip(gate)
    # Check number of channels in signal
    if len(sig.shape) == 1:
        # Create "sustain" portion of envelope
        sustain = np.ones(len(sig)-(2*len(gate)))
        envelope = np.concatenate([gate, sustain, offsetgate])
        gated = envelope * sig
    elif len(sig.shape) == 2:
        # Create "sustain" portion of envelope
        sustain = np.ones(len(sig[0])-(2*len(gate)))
        envelope = np.concatenate([gate, sustain, offsetgate])
        gatedLeft = envelope * sig[0]
        gatedRight = envelope * sig[1]
        gated = np.array([gatedLeft, gatedRight])
    return gated


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
    filename = filedialog.askopenfilename()
    fs, audio_file = wavfile.read(filename)

    just_name = filename.split('/')[-1]
    if len(just_name) > 35:
        loaded.set(just_name[:35] + "...")
    else:
        loaded.set(just_name)


def do_splice():
    global audio_file
    num_files =  int(ent_files.get())
    splice_time = int(ent_splice.get())

    if num_files == 1:
        messagebox.showwarning(
            title="Not Enough Files",
            message="Please select at least 2 files!"
        )
        return

    # Test whether the signal is long enough 
    # for splicing
    sigdur = len(audio_file) / fs
    if sigdur <= splice_time * num_files:
        messagebox.showerror(
            title="Cannot Splice!",
            message="The file you imported is too short!"
        )
        return

    # First cut offsets from beginning of signal
    spliced_list = []
    len_list = []
    for idx in range(1, num_files+1):
        cut_time = splice_time * idx
        cut_in_samples = cut_time * fs
        sig = audio_file[cut_in_samples:]
        spliced_list.append(sig)
        len_list.append(len(sig))
        spliced_array = np.array(spliced_list,dtype=object)
    min_len = min(len_list)

    # Remove existing file name from path
    just_name = filename.split('/')[-1]
    just_path = filename.split(just_name)[0]

    file_num.set("Writing files...")

    # Just take as many samples as the smallest array 
    # length to make every array the same length
    for idx in range(len(spliced_array)):
        sig = spliced_array[idx][:min_len]
        # Check if ramps were indicated
        if chk_Status.get() == 1:
            sig = doGate(sig,0.02,fs)
        file_name = just_path + str(idx+1) + ".wav"
        file_num.set(f"Writing file {str(idx+1)}")
        lbl_file_num.update() # Must update label to show text change
        # Write the .wav file
        wavfile.write(file_name, fs, sig.astype(np.int16))
        time.sleep(1) # give it a second to write file

    file_num.set("No files being written")

    messagebox.showinfo(
        title="Splicing Completed",
        message=(f"Successfully created {len(spliced_array)} files!")
    )


# Splice button
btn_submit = ttk.Button(frm_submit, text="Chop!", command=do_splice)
btn_submit.grid(column=0, row=0, padx=(0,10))

# create a menubar
menubar = tk.Menu(root)
root.config(menu=menubar)
# create the File menu
file_menu = tk.Menu(menubar, tearoff=False)
# add menu items to the File menu
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
        message="Version: 1.1.0\nWritten by: Travis M. Moore\nCreated: 06/10/2022\nLast Updated: 06/17/2022"
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
