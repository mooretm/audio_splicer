""" Automated audio splicing tool. Offset background 
    noise files to present uncorrelated background noise.

    Version 2.0.0
    Written by: Travis M. Moore
    Created: Jun 10, 2022
    Last edited: Jun 21, 2022
"""

# Import science packages
import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt

# Import GUI packages
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

# Import system packages
import os
import time


# Dictionary of data types and ranges
wav_dict = {
    'float32': (-1.0, 1.0),
    'int32': (-2147483648, 2147483647),
    'int16': (-32768, 32767),
    'uint8': (0, 255)
}

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

frm_submit = ttk.Frame(root)
frm_submit.grid(column=1,row=0,rowspan=3, **options)

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
    # Apply gating
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


def mnu_import_file():
    # Import and convert audio to float64
    global audio_file
    global fs
    global filename
    global audio_dtype
    global t_audio
    global original_audio

    filename = filedialog.askopenfilename()
    fs, audio_file = wavfile.read(filename)
    t_audio = np.arange(0,len(audio_file)/fs,1/fs)[:-1]
    audio_dtype = np.dtype(audio_file[0])
    #print(f"Incoming data type: {audio_dtype}")

    # Keep original data type file for comparison at end
    original_audio = audio_file

    # Immediately convert to float64 for manipulating
    if audio_dtype == 'float64':
        pass
    else:
        # 1. Convert to float64
        audio_file = audio_file.astype(np.float64)
        #print(f"Forced audio data type: {type(audio_file[0])}")
        # 2. Divide by original dtype max val
        audio_file = audio_file / wav_dict[str(audio_dtype)][1]

    # Display file name on GUI
    just_name = filename.split('/')[-1]
    if len(just_name) > 35:
        loaded.set(just_name[:35] + "...")
    else:
        loaded.set(just_name)


def do_splice():
    """ Splice audio, convert back to original 
        audio data type, and write spliced files.
    """
    # Get number of copies to make and the offset from GUI
    num_files =  int(ent_files.get())
    splice_time = int(ent_splice.get())

    # Crashes if only a single file is selected. 
    # An error for another day, so just test for it. 
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

    # Splice
    # First cut offsets from beginning of signal
    spliced_list = [] # holds spliced audio
    spliced_time_list = [] # holds spliced time vector
    len_list = [] # holds length of spliced audio segments
    for idx in range(1, num_files+1):
        cut_time = splice_time * idx
        cut_in_samples = cut_time * fs
        sig = audio_file[cut_in_samples:]
        t_sig = t_audio[cut_in_samples:]
        spliced_list.append(sig)
        len_list.append(len(sig))
        spliced_time_list.append(t_sig)
        #spliced_array = np.array(spliced_list,dtype=object)
        spliced_array = np.array(spliced_list)
    min_len = min(len_list)

    # Remove existing file name from path
    just_name = filename.split('/')[-1]
    just_path = filename.split(just_name)[0]

    # Take as many samples as the smallest array 
    # length to make every array the same length
    for idx in range(len(spliced_array)):
        sig = spliced_array[idx][:min_len]
        t_sig = spliced_time_list[idx][:min_len]

        # Normalize by clip? Actually messes up output. 
        #float_clip_max = np.max(np.abs(sig))
        #print(f"Float clip max: {float_clip_max}")

        # Check if ramps were indicated
        if chk_Status.get() == 1:
            sig = doGate(sig,0.02,fs)

        #sig = sig / float_clip_max
        # Multiply by original data type max
        sig = sig * wav_dict[str(audio_dtype)][1]
        # Round to return to integer values
        sig = np.round(sig)
        # Convert back to original data type
        sig = sig.astype(audio_dtype)
        #plt.plot(t_audio,original_audio)
        #plt.plot(t_sig,sig)
        #plt.show()

        # Update GUI with progress
        file_num.set(f"Writing file {str(idx+1)}")
        lbl_file_num.update() # Must update label to show text change
        
        # Write the .wav file
        #file_name = just_path + str(idx+1) + ".wav"
        file_name = save_path + os.sep + str(idx+1) + ".wav"
        wavfile.write(file_name, fs, sig)
        time.sleep(1) # give it a second to write file

    # Update the GUI when finished
    file_num.set("No files being written")

    # Give user feedback when finished
    messagebox.showinfo(
        title="Splicing Completed",
        message=(f"Successfully created {len(spliced_array)} files!")
    )


def get_save_path():
    global save_path
    # Ask user to specify save location
    save_path = filedialog.askdirectory()

    # Do nothing if cancelled
    if save_path is None:
        return

    # Call the splice function
    do_splice()


# Splice button
btn_submit = ttk.Button(frm_submit, text="Chop!", command=get_save_path)
btn_submit.grid(column=0, row=0, padx=(0,10))

# create a menubar
menubar = tk.Menu(root)
root.config(menu=menubar)
# create the File menu
file_menu = tk.Menu(menubar, tearoff=False)
# add menu items to the File menu
file_menu.add_command(
    label="Import Files",
    command=mnu_import_file
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
        message="Version: 2.0.0\nWritten by: Travis M. Moore\nCreated: 06/10/2022\nLast Updated: 06/21/2022"
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
