import tkinter as tk
from tkinter import filedialog, messagebox
import requests

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv *.avi")])
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)

def send_request():
    file_path = entry_file.get()
    selected_codecs = [codec for codec, var in codec_vars.items() if var.get()]
    selected_resolutions = [res for res, var in resolution_vars.items() if var.get()]
    selected_bitrates = [bitrate for bitrate, var in bitrate_vars.items() if var.get()]

    if not file_path or not selected_codecs:
        messagebox.showerror("Error", "Por favor, completa todos los campos.")
        return

    if operation_var.get() == "encoding-ladder":
        if not selected_resolutions or not selected_bitrates:
            messagebox.showerror("Error", "Por favor, selecciona resoluciones y bitrates.")
            return

        if len(selected_resolutions) != len(selected_bitrates):
            messagebox.showerror("Error", "Debe haber un bitrate para cada resolución seleccionada.")
            return

        try:
            files = {'file': open(file_path, 'rb')}
            data = {
                'codecs': selected_codecs,
                'resolutions': selected_resolutions,
                'bitrates': selected_bitrates
            }
            response = requests.post("http://127.0.0.1:8000/encoding-ladder/", files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                messagebox.showinfo("Éxito", f"Videos convertidos:\n{result['ladder_files']}")
            else:
                messagebox.showerror("Error", f"Error en la API: {response.json()['detail']}")

        except Exception as e:
            messagebox.showerror("Error", f"Algo salió mal: {str(e)}")

    elif operation_var.get() == "convert":
        try:
            files = {'file': open(file_path, 'rb')}
            data = {
                'codecs': selected_codecs
            }
            response = requests.post("http://127.0.0.1:8000/convert/", files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                messagebox.showinfo("Éxito", f"Videos convertidos:\n{result['converted_files']}")
            else:
                messagebox.showerror("Error", f"Error en la API: {response.json()['detail']}")

        except Exception as e:
            messagebox.showerror("Error", f"Algo salió mal: {str(e)}")

root = tk.Tk()
root.title("Video Transcoding GUI")
root.geometry("600x600")

# Campo para seleccionar archivo
tk.Label(root, text="Seleccionar archivo:").pack(pady=5)
frame_file = tk.Frame(root)
frame_file.pack(pady=5)
entry_file = tk.Entry(frame_file, width=50)
entry_file.pack(side=tk.LEFT, padx=5)
btn_file = tk.Button(frame_file, text="Examinar", command=select_file)
btn_file.pack(side=tk.LEFT)

# Selección de operación
tk.Label(root, text="Seleccionar operación:").pack(pady=5)
operation_var = tk.StringVar(value="encoding-ladder")
tk.Radiobutton(root, text="Convertir códec", variable=operation_var, value="convert").pack()
tk.Radiobutton(root, text="Encoding Ladder", variable=operation_var, value="encoding-ladder").pack()

# Opciones de códecs
tk.Label(root, text="Seleccionar códecs:").pack(pady=5)
codec_vars = {
    "vp9": tk.BooleanVar(),
    "h265": tk.BooleanVar(),
    "av1": tk.BooleanVar()
}
frame_codecs = tk.Frame(root)
frame_codecs.pack(pady=5)
for codec, var in codec_vars.items():
    tk.Checkbutton(frame_codecs, text=codec.upper(), variable=var).pack(side=tk.LEFT, padx=5)

# Opciones de resoluciones
tk.Label(root, text="Seleccionar resoluciones:").pack(pady=5)
resolution_vars = {
    "1920x1080": tk.BooleanVar(),
    "1280x720": tk.BooleanVar(),
    "854x480": tk.BooleanVar()
}
frame_resolutions = tk.Frame(root)
frame_resolutions.pack(pady=5)
for resolution, var in resolution_vars.items():
    tk.Checkbutton(frame_resolutions, text=resolution, variable=var).pack(side=tk.LEFT, padx=5)

# Opciones de bitrates
tk.Label(root, text="Seleccionar bitrates:").pack(pady=5)
bitrate_vars = {
    "6000000": tk.BooleanVar(),  # 6 Mbps
    "3000000": tk.BooleanVar(),  # 3 Mbps
    "1000000": tk.BooleanVar()   # 1 Mbps
}
frame_bitrates = tk.Frame(root)
frame_bitrates.pack(pady=5)
for bitrate, var in bitrate_vars.items():
    tk.Checkbutton(frame_bitrates, text=f"{int(bitrate) // 1000000} Mbps", variable=var).pack(side=tk.LEFT, padx=5)

# Botón para enviar la solicitud
btn_send = tk.Button(root, text="Convertir", command=send_request, bg="green", fg="white")
btn_send.pack(pady=20)

root.mainloop()