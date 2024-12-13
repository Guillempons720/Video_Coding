import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import threading
import time

# Función para seleccionar un archivo
def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mkv *.avi")])
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)

# Función para manejar el progreso
def update_progress(progress_bar, duration=5):
    progress_bar["value"] = 0
    step = 100 / (duration * 10)
    for _ in range(duration * 10):
        time.sleep(0.1)
        progress_bar["value"] += step
        root.update_idletasks()
    progress_bar["value"] = 100

# Función para enviar datos en un hilo
def send_request_thread():
    try:
        btn_send.config(state="disabled")  # Desactivar el botón

        file_path = entry_file.get()
        selected_codecs = [codec for codec, var in codec_vars.items() if var.get()]
        selected_resolution = resolution_var.get()
        selected_bitrate = bitrate_var.get()

        if not file_path:
            messagebox.showerror("Error", "Por favor, selecciona un archivo.")
            return

        if mode_var.get() == "codec" and not selected_codecs:
            messagebox.showerror("Error", "Selecciona al menos un códec.")
            return

        if mode_var.get() == "resolution" and not (selected_resolution and selected_bitrate):
            messagebox.showerror("Error", "Completa los campos de resolución y bitrate.")
            return

        progress_bar.pack(pady=10)  # Mostrar la barra de progreso

        # Simular el progreso (actualízalo acorde con la lógica real del backend)
        threading.Thread(target=update_progress, args=(progress_bar,)).start()

        # Enviar solicitud
        files = {'file': open(file_path, 'rb')}
        if mode_var.get() == "codec":
            data = {'codecs': selected_codecs}
            response = requests.post("http://127.0.0.1:8000/convert/", files=files, data=data)
        else:
            data = {'resolutions': [selected_resolution], 'bitrates': [selected_bitrate]}
            response = requests.post("http://127.0.0.1:8000/encoding-ladder/", files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            messagebox.showinfo("Éxito", f"Resultado:\n{result}")
        else:
            messagebox.showerror("Error", f"Error en la API: {response.json()['detail']}")

    except Exception as e:
        messagebox.showerror("Error", f"Algo salió mal: {str(e)}")
    finally:
        btn_send.config(state="normal")  # Reactivar el botón
        progress_bar.pack_forget()  # Ocultar la barra de progreso

# Función para iniciar el hilo
def start_request():
    threading.Thread(target=send_request_thread).start()

# Función para alternar entre los modos
def toggle_mode():
    for widget in frame_options.winfo_children():
        widget.pack_forget()

    if mode_var.get() == "codec":
        frame_codecs.pack(pady=5)
    else:
        frame_resolutions.pack(pady=5)

# Crear la ventana principal
root = tk.Tk()
root.title("Video Transcoding GUI")
root.geometry("600x500")

# Campo para seleccionar archivo
tk.Label(root, text="Seleccionar archivo:").pack(pady=5)
frame_file = tk.Frame(root)
frame_file.pack(pady=5)
entry_file = tk.Entry(frame_file, width=50)
entry_file.pack(side=tk.LEFT, padx=5)
btn_file = tk.Button(frame_file, text="Examinar", command=select_file)
btn_file.pack(side=tk.LEFT)

# Selección entre modos
tk.Label(root, text="Modo de conversión:").pack(pady=5)
mode_var = tk.StringVar(value="codec")
tk.Radiobutton(root, text="Convertir códec", variable=mode_var, value="codec", command=toggle_mode).pack()
tk.Radiobutton(root, text="Convertir resolución", variable=mode_var, value="resolution", command=toggle_mode).pack()

# Marco contenedor de opciones
frame_options = tk.Frame(root)
frame_options.pack(pady=5)

# Opciones de códecs
frame_codecs = tk.Frame(frame_options)
tk.Label(frame_codecs, text="Seleccionar códecs:").pack()
codec_vars = {
    "vp9": tk.BooleanVar(),
    "h265": tk.BooleanVar(),
    "av1": tk.BooleanVar()
}
for codec, var in codec_vars.items():
    tk.Checkbutton(frame_codecs, text=codec.upper(), variable=var).pack(side=tk.LEFT, padx=5)

# Opciones de resolución y bitrate
frame_resolutions = tk.Frame(frame_options)
tk.Label(frame_resolutions, text="Seleccionar resolución:").pack(pady=5)
resolution_var = tk.StringVar(value="1920x1080")
resolutions = ["1920x1080", "1280x720", "854x480"]
ttk.OptionMenu(frame_resolutions, resolution_var, *resolutions).pack(pady=5)

tk.Label(frame_resolutions, text="Seleccionar bitrate:").pack(pady=5)
bitrate_var = tk.StringVar(value="3000000")
bitrates = ["6000000", "3000000", "1000000"]
ttk.OptionMenu(frame_resolutions, bitrate_var, *bitrates).pack(pady=5)

# Botón para enviar la solicitud (siempre al final)
btn_send = tk.Button(root, text="Convertir", command=start_request, bg="green", fg="white")
btn_send.pack(pady=20)

# Barra de progreso
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")

# Inicializar modo
toggle_mode()

# Iniciar la aplicación
root.mainloop()
