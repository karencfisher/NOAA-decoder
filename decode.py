import os
import time
from apt import APT
from cv2 import createCLAHE, imwrite
import numpy as np
from threading import Thread
from queue import Queue, Empty


import tkinter as tk
from tkinter.messagebox import showerror, askyesno
from tkinter import filedialog
from PIL import Image, ImageTk

class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NOAA Satellite Image Viewer")
        self.root.geometry("550x630")  # Set the window size to 500x500 pixels
        
        self.image_path = None
        self.img_label = tk.Label(root, highlightthickness=2, highlightbackground="black")
        self.img_label.pack(padx=10, pady=10)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(side=tk.BOTTOM, padx=10, pady=5, anchor='e')

        self.text_box = tk.Text(root, height=1, wrap=tk.WORD)
        self.text_box.pack(padx=10, pady=0, side=tk.BOTTOM) 
        self.text_box.insert(tk.END, "Ready")

        self.open_button = tk.Button(self.button_frame, text="Open", command=self.open_image)
        self.open_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(self.button_frame, text="Save", command=self.save_image, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.have_image = False
        self.image_path = 'default_image.jpg'
        self.display_image()


    def on_close(self):
        if self.have_image:
            result = askyesno("Confirm", "Are you sure you want to exit without saving your image?")
            if not result:
                return
        if os.path.exists('temp.jpg'):
            os.remove('temp.jpg')
        self.root.destroy()

    def open_image(self):
        if self.have_image:
            result = askyesno("Confirm", "Are you sure you want to proceed without saving the current image?")
            if not result:
                return
            self.image_path = 'default_image.jpg'
        self.display_image()
        self.have_image = False

        file_path = filedialog.askopenfilename(filetypes=[("WAV File", "*.wav")])
        if file_path:
            self.file_path = file_path
            self.open_button.config(state=tk.DISABLED)
            que = Queue()
            decode_thread = Thread(target=self._decode, args=(que,))
            decode_thread.start()
            done = False
            start = time.time()
            self.text_box.delete("1.0", tk.END)
            self.text_box.insert(tk.END, 'Decoding')
            self.text_box.update()
            while not done:
                try:
                    success = que.get(block=True, timeout=1)
                except Empty:
                    elapsed = time.time() - start
                    minutes = int(elapsed // 60)
                    seconds = int(elapsed % 60)
                    self.text_box.delete("1.0", tk.END)
                    self.text_box.insert(tk.END, f'Decoding - elapsed time {minutes:02d}:{seconds:02d}')
                    self.text_box.update()
                else:
                    done = True
            decode_thread.join()
            self.text_box.delete("1.0", tk.END)
            self.text_box.insert(tk.END, f'Done -- elapsed time {minutes:02d}:{seconds:02d}')
            self.text_box.update()
            self.have_image = True

            if not success:
                self.open_button.config(state=tk.NORMAL)
                return
            self.image_path = 'temp.jpg'
            self.display_image()
            self.open_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
            

    def display_image(self):
        if self.image_path:
            image = Image.open(self.image_path)
            image = image.resize((520, 548), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.img_label.config(image=photo)
            self.img_label.image = photo

    def save_image(self):
        if not self.have_image:
            return
        if self.image_path:
            file_path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPG Files", "*.jpg")])
            if file_path:
                image = Image.open(self.image_path)
                image.save(file_path)
                self.save_button.config(state=tk.DISABLED)
                
                self.text_box.delete("1.0", tk.END)
                self.text_box.insert(tk.END, f'Ready')
                self.text_box.update()
                self.have_image = False

    def _clahe(self, image, clip_limit=40, tileGridSize=(8,8)):
        image = image.astype(np.uint8)
        clahe = createCLAHE(clipLimit=clip_limit, tileGridSize=tileGridSize)
        new_image = clahe.apply(image)
        return new_image

    def _decode(self, que):
        try:
            apt = APT(self.file_path)
        except:
            showerror("Error", "Invalid input file")
            que.put(False)
            
        image = apt.decode()
        image_enh = self._clahe(image, clip_limit=10)
        imwrite('temp.jpg', image_enh[:, :1040])
        que.put(True)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    root.mainloop()

