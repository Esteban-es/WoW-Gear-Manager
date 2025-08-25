import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# Definir tiers
TIERS = ["Desnudo", "Explorador", "Aventurero", "Veterano", "Campeón", "Héroe", "Mítico"]

# Slots encantables
ENCHANTABLE_SLOTS = ["Capa", "Pechera", "Brazales", "Pantalones", "Botas", "Anillo 1", "Anillo 2", "Arma 2M", "Arma 1M"]

# Archivos
STATE_FILE = "gear_state.json"
BIS_FILE = "bis.json"


class GearApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WoW BIS Tracker")
        self.root.geometry("1200x700")

        self.bis_data = self.load_bis()

        # Frames principales
        left_frame = tk.Frame(root)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        right_frame = tk.Frame(root)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Tabla de prioridades
        self.priority_table = ttk.Treeview(
            right_frame,
            columns=("Num", "Slot", "Tier", "Objeto", "Localización", "Nivel"),
            show="headings",
            height=25
        )

        self.priority_table.heading("Num", text="#")
        self.priority_table.heading("Slot", text="Slot")
        self.priority_table.heading("Tier", text="Tier")
        self.priority_table.heading("Objeto", text="Objeto")
        self.priority_table.heading("Localización", text="Localización")
        self.priority_table.heading("Nivel", text="Nivel M+")

        self.priority_table.column("Num", width=40, anchor="center")
        self.priority_table.column("Slot", width=120, anchor="center")
        self.priority_table.column("Tier", width=100, anchor="center")
        self.priority_table.column("Objeto", width=200, anchor="w")
        self.priority_table.column("Localización", width=250, anchor="w")
        self.priority_table.column("Nivel", width=100, anchor="center")

        self.priority_table.pack(fill="both", expand=True)

        # Botón modificar BIS
        tk.Button(right_frame, text="Modificar BIS", command=self.open_bis_editor).pack(pady=5)

        # Slots
        self.entries = {}
        self.create_slots(left_frame)

        # Cargar estado guardado
        self.load_state()

        # Actualizar en tiempo real
        self.update_priority()

        # Guardar al cerrar
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_slots(self, parent):
        slots = [
            "Cabeza", "Cuello", "Hombreras", "Capa",
            "Pechera", "Brazales", "Guantes", "Cinturón",
            "Pantalones", "Botas", "Anillo 1", "Anillo 2",
            "Abalorio 1", "Abalorio 2", "Arma 1M", "Arma 2M"
        ]

        for slot in slots:
            frame = tk.Frame(parent)
            frame.pack(fill="x", pady=2)

            tk.Label(frame, text=slot, width=12, anchor="w").pack(side="left")

            tier_var = tk.StringVar(value="Desnudo")
            tier_menu = ttk.Combobox(frame, textvariable=tier_var, values=TIERS, state="readonly", width=12)
            tier_menu.pack(side="left", padx=5)

            bis_var = tk.BooleanVar()
            tk.Checkbutton(frame, text="Tengo BIS", variable=bis_var).pack(side="left")

            enchant_var = tk.BooleanVar()
            tk.Checkbutton(frame, text="Encantado", variable=enchant_var).pack(side="left")

            exclude_var = tk.BooleanVar()
            tk.Checkbutton(frame, text="Excluir", variable=exclude_var).pack(side="left")

            self.entries[slot] = {
                "tier": tier_var,
                "bis": bis_var,
                "enchant": enchant_var,
                "exclude": exclude_var
            }

            tier_var.trace_add("write", lambda *_: self.update_priority())
            bis_var.trace_add("write", lambda *_: self.update_priority())
            enchant_var.trace_add("write", lambda *_: self.update_priority())
            exclude_var.trace_add("write", lambda *_: self.update_priority())

    def update_priority(self):
        # Limpiar tabla
        for item in self.priority_table.get_children():
            self.priority_table.delete(item)

        upgrades, enchants_pending = [], []

        for slot, vars in self.entries.items():
            if vars["exclude"].get():
                continue

            tier = vars["tier"].get()
            has_bis = vars["bis"].get()
            has_enchant = vars["enchant"].get()

            bis_info = self.bis_data.get(slot, {})
            bis_name = bis_info.get("Item", "—")
            source = bis_info.get("Source", "—")

            # Mejoras pendientes
            if not (tier == "Mítico" and has_bis):
                min_lvl = self.min_keystone_for_upgrade(tier)
                if min_lvl:
                    upgrades.append({
                        "slot": slot,
                        "tier": tier,
                        "bis": bis_name,
                        "source": source,
                        "min_lvl": min_lvl
                    })

            # Encantamientos pendientes (solo si BIS y tier Héroe/Mítico)
            if has_bis and slot in ENCHANTABLE_SLOTS and tier in ("Héroe", "Mítico") and not has_enchant:
                enchants_pending.append({
                    "slot": slot,
                    "enchant": bis_info.get("Enchant", "—")
                })

        # Mostrar en la tabla
        index = 1

        # Encantamientos primero
        for e in enchants_pending:
            self.priority_table.insert(
                "", "end",
                values=(index, e["slot"], "—", "Encantamiento: " + e["enchant"], "—", "—")
            )
            index += 1

        # Mejoras ordenadas por tier
        upgrades.sort(
            key=lambda x: (
                TIERS.index(x["tier"]),       # primero el tier
                0 if not self.entries[x["slot"]]["bis"].get() else 1,  # luego BIS (los que no son BIS primero)
                x["slot"]                     # opcional: desempate por nombre de slot
            )
        )
        for p in upgrades:
            self.priority_table.insert(
                "", "end",
                values=(index, p["slot"], p["tier"], p["bis"], p["source"], p["min_lvl"])
            )
            index += 1

    def min_keystone_for_upgrade(self, tier):
        tier_index = TIERS.index(tier)
        if tier_index < TIERS.index("Campeón"):
            return 2  # cualquier M+ vale
        elif tier_index == TIERS.index("Campeón"):
            return 6  # héroe -> necesitas mínimo +6
        elif tier_index == TIERS.index("Mítico"):
            return None  # ya tope
        return 6

    def load_bis(self):
        if not os.path.exists(BIS_FILE):
            return {}
        with open(BIS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_bis(self):
        with open(BIS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.bis_data, f, indent=4, ensure_ascii=False)

    def load_state(self):
        if not os.path.exists(STATE_FILE):
            return
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
            for slot, info in state.items():
                if slot in self.entries:
                    vars = self.entries[slot]
                    if info.get("Tier") in TIERS:
                        vars["tier"].set(info.get("Tier"))
                    vars["bis"].set(info.get("BIS", False))
                    vars["enchant"].set(info.get("Enchant", False))
                    vars["exclude"].set(info.get("Exclude", False))
        except Exception:
            pass

    def save_state(self):
        state = {}
        for slot, vars in self.entries.items():
            state[slot] = {
                "Tier": vars["tier"].get(),
                "BIS": vars["bis"].get(),
                "Enchant": vars["enchant"].get(),
                "Exclude": vars["exclude"].get()
            }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4, ensure_ascii=False)

    def on_close(self):
        self.save_state()
        self.save_bis()
        self.root.destroy()

    def open_bis_editor(self):
        editor = tk.Toplevel(self.root)
        editor.title("Modificar BIS")
        editor.geometry("1000x600")

        frame = tk.Frame(editor)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Encabezado
        header = tk.Frame(frame)
        header.pack(fill="x")
        tk.Label(header, text="Slot", width=15, anchor="w").pack(side="left", padx=5)
        tk.Label(header, text="Objeto", width=40, anchor="w").pack(side="left", padx=5)
        tk.Label(header, text="Localización", width=40, anchor="w").pack(side="left", padx=5)
        tk.Label(header, text="Encantamiento", width=20, anchor="w").pack(side="left", padx=5)

        self.bis_entries = {}
        for slot, info in self.bis_data.items():
            row = tk.Frame(frame)
            row.pack(fill="x", pady=1)

            tk.Label(row, text=slot, width=15, anchor="w").pack(side="left", padx=5)

            item_var = tk.StringVar(value=info.get("Item", ""))
            tk.Entry(row, textvariable=item_var, width=40).pack(side="left", padx=5)

            source_var = tk.StringVar(value=info.get("Source", ""))
            tk.Entry(row, textvariable=source_var, width=40).pack(side="left", padx=5)

            enchant_var = tk.StringVar(value=info.get("Enchant", ""))
            tk.Entry(row, textvariable=enchant_var, width=20).pack(side="left", padx=5)

            self.bis_entries[slot] = {"Item": item_var, "Source": source_var, "Enchant": enchant_var}

        tk.Button(editor, text="Guardar", command=self.save_bis_editor).pack(pady=10)

    def save_bis_editor(self):
        for slot, vars in self.bis_entries.items():
            self.bis_data[slot] = {
                "Item": vars["Item"].get(),
                "Source": vars["Source"].get(),
                "Enchant": vars["Enchant"].get()
            }
        self.save_bis()
        messagebox.showinfo("Guardado", "Cambios en BIS guardados correctamente")
        self.update_priority()


if __name__ == "__main__":
    root = tk.Tk()
    app = GearApp(root)
    root.mainloop()
