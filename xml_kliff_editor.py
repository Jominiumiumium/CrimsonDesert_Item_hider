import os
import sys
import re
import shutil
from datetime import datetime
import tempfile
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "python"))
from paz_parse import parse_pamt, PazEntry
from paz_unpack import extract_entry
from paz_repack import repack_entry

TARGET_FILE = "phm_description_player_kliff.xml"

# All PartInOutSocket items grouped by category
SOCKET_CATEGORIES = [
    ("Misc", [
        "CD_HyperspacePlug",
    ]),
    ("Sword (1H)", [
        "CD_MainWeapon_Sword_R",
        "CD_MainWeapon_Sword_IN_R",
        "CD_MainWeapon_Sword_L",
        "CD_MainWeapon_Sword_IN_L",
        "CD_MainWeapon_Sword_R_Aux",
        "CD_MainWeapon_Sword_IN_R_Aux",
    ]),
    ("Dagger", [
        "CD_MainWeapon_Dagger_R",
        "CD_MainWeapon_Dagger_IN_R",
        "CD_MainWeapon_Dagger_L",
        "CD_MainWeapon_Dagger_IN_L",
    ]),
    ("Axe (1H)", [
        "CD_MainWeapon_Axe_R",
        "CD_MainWeapon_Axe_L",
    ]),
    ("Mace (1H)", [
        "CD_MainWeapon_Mace_R",
        "CD_MainWeapon_Mace_L",
    ]),
    ("Wand", [
        "CD_MainWeapon_Wand_R",
    ]),
    ("Fist / Hand Cannon / Gauntlet", [
        "CD_MainWeapon_Fist_R",
        "CD_MainWeapon_Fist_L",
        "CD_MainWeapon_HandCannon",
        "CD_MainWeapon_Gauntlet",
    ]),
    ("Two-Hand Sword", [
        "CD_TwoHandWeapon_Sword",
    ]),
    ("Two-Hand Axe", [
        "CD_TwoHandWeapon_Axe",
    ]),
    ("Two-Hand Mace / Hammer", [
        "CD_TwoHandWeapon_Mace",
        "CD_TwoHandWeapon_WarHammer",
        "CD_TwoHandWeapon_Hammer",
    ]),
    ("Cannon / Thrower", [
        "CD_TwoHandWeapon_Cannon",
        "CD_TwoHandWeapon_Thrower",
    ]),
    ("Spear / Pike / Halberd", [
        "CD_TwoHandWeapon_Spear",
        "CD_MainWeapon_Pike",
        "CD_TwoHandWeapon_Alebard",
    ]),
    ("Fan / Rod / Scythe", [
        "CD_MainWeapon_Fan",
        "CD_TwoHandWeapon_Rod",
        "CD_TwoHandWeapon_Scythe",
    ]),
    ("Shield", [
        "CD_MainWeapon_Shield_L",
        "CD_MainWeapon_TowerShield_L",
    ]),
    ("Bow / Arrow", [
        "CD_MainWeapon_Bow",
        "CD_MainWeapon_Quiver",
        "CD_MainWeapon_Arw",
        "CD_MainWeapon_Arw_IN",
    ]),
    ("Bomb", [
        "CD_MainWeapon_Bomb",
    ]),
    ("Tools", [
        "CD_Tool_Torch",
        "CD_Lantern",
        "CD_Tool_Flute",
        "CD_Tool_Pipe",
        "CD_Tool_FishingRod",
        "CD_Tool_Axe",
        "CD_Tool_Pan",
        "CD_Tool_Hammer",
        "CD_Tool_Shovel",
        "CD_Tool_Pickaxe",
        "CD_Tool_Saw",
        "CD_Tool_Broom",
        "CD_Tool_Hayfork",
        "CD_Tool_FarmScythe",
        "CD_Tool_Rake",
        "CD_Tool_Hoe",
        "CD_Tool_Sprayer",
        "CD_Tool_Shooter",
    ]),
    ("Accessories", [
        "CD_Ring_R",
        "CD_Ring_L",
        "CD_Earring_R",
        "CD_Earring_L",
    ]),
    ("Abyss", [
        "CD_Abyss_Gauntlet_02",
    ]),
]


class KliffEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("XML Editor")
        self.geometry("620x780")
        self.resizable(True, True)

        self.pamt_path = r"C:\Program Files (x86)\Steam\steamapps\common\Crimson Desert\0009\0.pamt"
        self.kliff_entry = None
        self._current_content = None

        self.temp_dir = tempfile.mkdtemp(prefix="kliff_edit_")

        # Checkbox variables: {part_name: BooleanVar}
        self.check_vars = {}

        self._build_ui()
        self.after(100, self._auto_load_pamt)

    def _build_ui(self):
        # --- Top info ---
        top_frame = tk.Frame(self, padx=10, pady=5)
        top_frame.pack(fill=tk.X)

        tk.Label(top_frame, text="Target archive:", anchor="w").pack(fill=tk.X)

        info_frame = tk.Frame(top_frame)
        info_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(info_frame, text=self.pamt_path, fg="#555", font=("Arial", 8)).pack(side=tk.LEFT)
        self.lbl_status = tk.Label(info_frame, text="Initializing...", fg="blue")
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=10)

        # --- Button bar ---
        btn_frame = tk.Frame(self, padx=10, pady=5)
        btn_frame.pack(fill=tk.X)

        self.btn_select_all = tk.Button(btn_frame, text="Select All", command=self._select_all, state=tk.DISABLED)
        self.btn_select_all.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_deselect_all = tk.Button(btn_frame, text="Deselect All", command=self._deselect_all, state=tk.DISABLED)
        self.btn_deselect_all.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_apply = tk.Button(btn_frame, text="Apply Changes", command=self._apply,
                                   state=tk.DISABLED, font=("Arial", 10, "bold"))
        self.btn_apply.pack(side=tk.RIGHT)

        # --- Scrollable checkbox area ---
        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas)

        self.scroll_frame.bind("<Configure>",
                               lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>",
                             lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # Build checkboxes per category
        for cat_name, parts in SOCKET_CATEGORIES:
            lbl = tk.Label(self.scroll_frame, text=cat_name, font=("Arial", 10, "bold"), anchor="w")
            lbl.pack(fill=tk.X, padx=5, pady=(8, 2))

            for part in parts:
                var = tk.BooleanVar(value=False)
                self.check_vars[part] = var
                display = part.replace("CD_", "").replace("_", " ")
                cb = tk.Checkbutton(self.scroll_frame, text=display, variable=var, anchor="w")
                cb.pack(fill=tk.X, padx=20)

        # --- Bottom help ---
        help_text = "Check items to enable Visible=\"Out\". Uncheck to remove it.\nClick Apply Changes to write edits into the PAZ archive."
        tk.Label(self, text=help_text, justify=tk.LEFT, fg="#555555", padx=10).pack(side=tk.BOTTOM, anchor="w", pady=(0, 5))

    # ------------------------------------------------------------------
    def _select_all(self):
        for var in self.check_vars.values():
            var.set(True)

    def _deselect_all(self):
        for var in self.check_vars.values():
            var.set(False)

    # ------------------------------------------------------------------
    def _auto_load_pamt(self):
        if not os.path.exists(self.pamt_path):
            messagebox.showerror("Error",
                                 f"Could not find 0.pamt at:\n{self.pamt_path}\n\nMake sure the game is installed there.")
            self.lbl_status.config(text="File not found", fg="red")
            return

        try:
            self.lbl_status.config(text="Parsing...", fg="blue")
            self.update()

            paz_dir = os.path.dirname(self.pamt_path)
            entries = parse_pamt(self.pamt_path, paz_dir=paz_dir)

            self.kliff_entry = next((e for e in entries if TARGET_FILE in e.path.lower()), None)

            if not self.kliff_entry:
                messagebox.showerror("Error", f"Could not find {TARGET_FILE} in the archive.")
                self.lbl_status.config(text="File not found", fg="red")
                return

            self.lbl_status.config(text="Loaded successfully", fg="green")
            self._read_current_states()

            self.btn_select_all.config(state=tk.NORMAL)
            self.btn_deselect_all.config(state=tk.NORMAL)
            self.btn_apply.config(state=tk.NORMAL)

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load PAMT:\n{e}")
            self.lbl_status.config(text="Error loading", fg="red")

    def _read_current_states(self):
        """Extract the file and set checkbox states from current XML content."""
        try:
            res = extract_entry(self.kliff_entry, self.temp_dir)
            with open(res["path"], 'rb') as f:
                self._current_content = f.read()

            for part_name, var in self.check_vars.items():
                marker = b'PartName="' + part_name.encode('utf-8') + b'"'
                has_visible = False
                for line in self._current_content.split(b'\n'):
                    if marker in line:
                        has_visible = b'Visible="Out"' in line
                        break
                var.set(has_visible)

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to read file states:\n{e}")

    # ------------------------------------------------------------------
    def _apply(self):
        if not self.kliff_entry:
            return

        try:
            # Re-extract fresh content
            res = extract_entry(self.kliff_entry, self.temp_dir)
            extracted_path = res["path"]
            with open(extracted_path, 'rb') as f:
                content = f.read()

            # Build desired states from checkboxes
            changes = {name: var.get() for name, var in self.check_vars.items()}
            content = self._apply_visible_changes(content, changes)

            with open(extracted_path, 'wb') as f:
                f.write(content)

            # Backup before repacking
            paz_file = self.kliff_entry.paz_file
            backup_ext = datetime.now().strftime("%Y%m%d_%H%M%S") + ".bak"
            backup_path = paz_file + "." + backup_ext
            shutil.copy2(paz_file, backup_path)

            repack_entry(extracted_path, self.kliff_entry, output_path=None)

            messagebox.showinfo("Success",
                                f"Changes applied and repacked!\n\nBackup saved as:\n{os.path.basename(backup_path)}")

            self._read_current_states()

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to apply changes:\n{e}")

    @staticmethod
    def _apply_visible_changes(content, changes):
        """Add or remove Visible='Out' for each PartName in *changes*."""
        sep = b'\r\n' if b'\r\n' in content else b'\n'
        lines = content.split(sep)

        for part_name, should_be_visible in changes.items():
            marker = b'PartName="' + part_name.encode('utf-8') + b'"'

            for i, line in enumerate(lines):
                if marker not in line:
                    continue

                has_visible = b'Visible="Out"' in line

                if should_be_visible and not has_visible:
                    # Insert Visible="Out" before the closing />
                    idx = line.rfind(b'/>')
                    if idx >= 0:
                        before = line[:idx].rstrip()
                        after = line[idx + 2:]
                        lines[i] = before + b' Visible="Out"/>' + after

                elif not should_be_visible and has_visible:
                    # Remove Visible="Out" and any preceding whitespace
                    lines[i] = re.sub(rb'[\t ]+Visible="Out"', b'', line)

                break

        return sep.join(lines)


if __name__ == "__main__":
    app = KliffEditor()
    app.mainloop()
