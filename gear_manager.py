import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json

# Lista de slots de WoW
SLOTS = [
    "Cabeza", "Cuello", "Hombreras", "Capa", "Pechera", "Brazales", "Guantes",
    "Cinturón", "Pantalones", "Botas", "Anillo 1", "Anillo 2",
    "Abalorio 1", "Abalorio 2", "Arma 1M", "Arma 2M"
]

# Tiers de menor a mayor calidad
TIERS = ["Desnudo", "Explorador", "Aventurero", "Veterano", "Campeón", "Héroe", "Mítico"]

class GearApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Equipo - WoW")
        self.items = {}

        # Contenedor con scrollbar
        container = tk.Frame(root)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Crear slots
        self.entries = {}
        for slot in SLOTS:
            frame = tk.LabelFrame(self.scroll_frame, text=slot, padx=5, pady=5)
            frame.pack(fill="x", padx=10, pady=5)

            tk.Label(frame, text="Item:").grid(row=0, column=0, sticky="w")
            item_entry = tk.Entry(frame, width=40)
            item_entry.grid(row=0, column=1, padx=5)

            tk.Label(frame, text="Fuente:").grid(row=1, column=0, sticky="w")
            source_entry = tk.Entry(frame, width=40)
            source_entry.grid(row=1, column=1, padx=5)

            tk.Label(frame, text="Tier:").grid(row=2, column=0, sticky="w")
            tier_combo = ttk.Combobox(frame, values=TIERS, state="readonly", width=15)
            tier_combo.current(0)  # Por defecto: Desnudo
            tier_combo.grid(row=2, column=1, padx=5, sticky="w")

            bis_var = tk.BooleanVar()
            bis_check = tk.Checkbutton(frame, text="BIS", variable=bis_var)
            bis_check.grid(row=3, column=1, sticky="w")

            self.entries[slot] = {
                "item": item_entry,
                "source": source_entry,
                "tier": tier_combo,
                "bis": bis_var
            }

        # Botones
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Guardar", command=self.save_data).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Cargar", command=self.load_data).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Calcular prioridad", command=self.calculate_priority).grid(row=0, column=2, padx=5)

    def save_data(self):
        data = {}
        for slot, widgets in self.entries.items():
            data[slot] = {
                "Item": widgets["item"].get(),
                "Source": widgets["source"].get(),
                "Tier": widgets["tier"].get(),
                "BIS": widgets["bis"].get()
            }
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", "Datos guardados correctamente.")

    def load_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for slot, info in data.items():
                if slot in self.entries:
                    self.entries[slot]["item"].delete(0, tk.END)
                    self.entries[slot]["item"].insert(0, info.get("Item", ""))
                    self.entries[slot]["source"].delete(0, tk.END)
                    self.entries[slot]["source"].insert(0, info.get("Source", ""))
                    if info.get("Tier") in TIERS:
                        self.entries[slot]["tier"].set(info["Tier"])
                    self.entries[slot]["bis"].set(info.get("BIS", False))
            messagebox.showinfo("Éxito", "Datos cargados correctamente.")

    def calculate_priority(self):
        weakest_tier_index = len(TIERS)
        weakest_slots = []

        for slot, widgets in self.entries.items():
            tier = widgets["tier"].get()
            if tier not in TIERS:
                continue
            tier_index = TIERS.index(tier)

            if tier_index < weakest_tier_index:
                weakest_tier_index = tier_index
                weakest_slots = [(slot, widgets)]
            elif tier_index == weakest_tier_index:
                weakest_slots.append((slot, widgets))

        if not weakest_slots:
            messagebox.showinfo("Resultado", "No hay objetos definidos.")
            return

        result = "Objetos más débiles:\n\n"
        for slot, widgets in weakest_slots:
            result += f"{slot}: {widgets['item'].get()} (Tier: {widgets['tier'].get()}, Fuente: {widgets['source'].get()}, BIS: {'Sí' if widgets['bis'].get() else 'No'})\n"

        messagebox.showinfo("Prioridad", result)


if __name__ == "__main__":
    root = tk.Tk()
    app = GearApp(root)
    root.mainloop()
