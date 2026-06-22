"""Fundraiser data-entry and viewer app (Tkinter).

Page 1 (Entry): enter first name, last name, amount, and payment type, then
append the record to a chosen CSV. If no CSV is chosen, a new file named
default_csv.csv (or default_csv_1.csv, default_csv_2.csv, ... if that already
exists) is created in the working folder.

Page 2 (View): pick a CSV and see its rows in a scrollable table, with the
total amount pledged shown on the right.
"""

import csv
import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

CSV_HEADER = ["First Name", "Last Name", "Amount", "Payment Type"]
PAYMENT_TYPES = ["cash", "card", "cheque", "e-transfer"]
DEFAULT_CSV_BASE = "default_csv"


def app_dir():
    """Return the folder the app lives in (where default CSVs are written).

    - Bundled in a macOS .app: the folder *containing* the .app bundle
      (the executable itself is at Name.app/Contents/MacOS/Name).
    - Other frozen builds (e.g. --onefile): the folder holding the executable.
    - Run as a plain script: the folder containing this source file.
    """
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        for parent in exe.parents:
            if parent.suffix == ".app":
                return parent.parent
        return exe.parent
    return Path(__file__).resolve().parent


APP_DIR = app_dir()


def next_default_csv_path():
    """Return a non-existing default CSV path in the app folder.

    Tries default_csv.csv first, then default_csv_1.csv, default_csv_2.csv, ...
    """
    candidate = APP_DIR / f"{DEFAULT_CSV_BASE}.csv"
    if not candidate.exists():
        return str(candidate)
    i = 1
    while True:
        candidate = APP_DIR / f"{DEFAULT_CSV_BASE}_{i}.csv"
        if not candidate.exists():
            return str(candidate)
        i += 1


def append_record(path, record):
    """Append a record (list matching CSV_HEADER) to path.

    Writes the header first if the file is new or empty.
    """
    needs_header = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if needs_header:
            writer.writerow(CSV_HEADER)
        writer.writerow(record)


class EntryPage(ttk.Frame):
    """Page 1: data entry form."""

    def __init__(self, master, active_csv):
        super().__init__(master, padding=20)

        # Shared StringVar holding the app-wide active CSV path. Updated on a
        # successful submit so the View page can default to the same file.
        self.active_csv = active_csv

        # --- CSV selection -------------------------------------------------
        csv_frame = ttk.LabelFrame(self, text="Target CSV", padding=10)
        csv_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        csv_frame.columnconfigure(0, weight=1)

        self.csv_path_var = tk.StringVar()
        ttk.Entry(csv_frame, textvariable=self.csv_path_var).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(csv_frame, text="Browse...", command=self.browse_csv).grid(
            row=0, column=1
        )
        ttk.Label(
            csv_frame,
            text="Leave empty to create a new default_csv.csv in the working folder.",
            foreground="gray",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # --- Form fields ---------------------------------------------------
        self.first_var = tk.StringVar()
        self.last_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.payment_var = tk.StringVar(value=PAYMENT_TYPES[0])

        ttk.Label(self, text="First name:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(self, textvariable=self.first_var).grid(
            row=1, column=1, sticky="ew", pady=5
        )

        ttk.Label(self, text="Last name:").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(self, textvariable=self.last_var).grid(
            row=2, column=1, sticky="ew", pady=5
        )

        ttk.Label(self, text="Amount ($):").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(self, textvariable=self.amount_var).grid(
            row=3, column=1, sticky="ew", pady=5
        )

        ttk.Label(self, text="Payment type:").grid(
            row=4, column=0, sticky="nw", pady=5
        )
        radio_frame = ttk.Frame(self)
        radio_frame.grid(row=4, column=1, sticky="w", pady=5)
        for pt in PAYMENT_TYPES:
            ttk.Radiobutton(
                radio_frame, text=pt, value=pt, variable=self.payment_var
            ).pack(side="left", padx=(0, 10))

        ttk.Button(self, text="Submit", command=self.submit).grid(
            row=5, column=0, columnspan=2, pady=(20, 0)
        )

        self.columnconfigure(1, weight=1)

    def browse_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.csv_path_var.set(path)

    def validate_amount(self):
        """Return the amount as a 2-decimal string, or None if invalid."""
        raw = self.amount_var.get().strip()
        try:
            value = float(raw)
        except ValueError:
            return None
        if value <= 0:
            return None
        return f"{value:.2f}"

    def submit(self):
        first = self.first_var.get().strip()
        last = self.last_var.get().strip()
        if not first or not last:
            messagebox.showerror("Invalid input", "First and last name are required.")
            return

        amount = self.validate_amount()
        if amount is None:
            messagebox.showerror(
                "Invalid input", "Amount must be a positive number (e.g. 25.00)."
            )
            return

        path = self.csv_path_var.get().strip()
        if not path:
            path = next_default_csv_path()
            self.csv_path_var.set(path)

        record = [first, last, amount, self.payment_var.get()]
        try:
            append_record(path, record)
        except OSError as exc:
            messagebox.showerror("Write error", f"Could not write to {path}:\n{exc}")
            return

        # Make this CSV the app-wide default (also drives the View page).
        self.active_csv.set(path)

        messagebox.showinfo(
            "Saved", f"Record saved to {os.path.basename(path)}."
        )
        # Clear the form for the next entry (keep the CSV target).
        self.first_var.set("")
        self.last_var.set("")
        self.amount_var.set("")
        self.payment_var.set(PAYMENT_TYPES[0])


class ViewPage(ttk.Frame):
    """Page 2: editable CSV table with a pledged total.

    Single-click a cell to highlight its row (and, more strongly, the cell
    itself). Double-click a cell to edit it in place. Use Delete Row to drop
    the selected record and Save to write the edits back to the CSV.
    """

    # Whole-row highlight (light) vs. the clicked cell (stronger). The cell is
    # rendered with an overlay label since ttk.Treeview cannot colour a single
    # cell on its own.
    ROW_HIGHLIGHT = "#cfe2ff"
    CELL_HIGHLIGHT = "#5b9bff"

    def __init__(self, master, active_csv):
        super().__init__(master, padding=20)

        # The currently selected CSV. Persists until the user opens another
        # one or the app closes.
        self.current_path = None

        # Index of the "Amount" column within the table, if present. Used to
        # keep the pledged total in sync as cells are edited or rows deleted.
        self._amount_idx = None

        # The cell the user last clicked: (item id, column id like "#2").
        self._sel_item = None
        self._sel_col = None

        # Stack of table snapshots (each a list of row tuples) captured before
        # every edit or deletion, so changes can be undone one step at a time.
        self._undo_stack = []

        # Shared app-wide active CSV. When the Entry page submits to a file
        # (including a newly created default CSV), this page loads it.
        self.active_csv = active_csv
        self.active_csv.trace_add("write", self._on_active_change)

        # Row selection shows as a soft highlight; the clicked cell sits on top
        # in a stronger colour (see _highlight / the overlay below).
        style = ttk.Style(self)
        style.map(
            "Treeview",
            background=[("selected", self.ROW_HIGHLIGHT)],
            foreground=[("selected", "black")],
        )
        # Coloured-text variants of the native button so Delete/Undo match the
        # look of the other toolbar buttons.
        style.configure("Delete.TButton", foreground="#e53935")
        style.map("Delete.TButton", foreground=[("active", "#c62828")])
        style.configure("Undo.TButton", foreground="#fb8c00")
        style.map(
            "Undo.TButton",
            foreground=[("active", "#ef6c00"), ("disabled", "#ffcc80")],
        )

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))
        ttk.Button(top, text="Open CSV...", command=self.open_csv).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh).pack(
            side="left", padx=(8, 0)
        )
        # Action buttons with coloured text, matching the native button look.
        ttk.Button(
            top, text="Delete Row", command=self.delete_row,
            style="Delete.TButton",
        ).pack(side="left", padx=(8, 0))
        self.undo_btn = ttk.Button(
            top, text="Undo", command=self.undo, state="disabled",
            style="Undo.TButton",
        )
        self.undo_btn.pack(side="left", padx=(8, 0))
        self.file_label = ttk.Label(top, text="No file loaded", foreground="gray")
        self.file_label.pack(side="left", padx=10)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        # --- Total (right) -------------------------------------------------
        # Packed first so this fixed-width panel always keeps its space; the
        # table then fills whatever remains.
        side = ttk.Frame(body, padding=(20, 0))
        side.pack(side="right", fill="y")
        ttk.Label(side, text="Amount pledged ($)").pack(anchor="w")
        self.total_var = tk.StringVar(value="0.00")
        ttk.Label(
            side, textvariable=self.total_var, font=("TkDefaultFont", 20, "bold")
        ).pack(anchor="w", pady=(5, 0))
        ttk.Label(
            side,
            text="Double-click a cell to edit. Changes auto-save; press "
            "Cmd/Ctrl+Z to undo (last 5).",
            foreground="gray",
            wraplength=140,
            justify="left",
        ).pack(anchor="w", pady=(15, 0))

        # --- Table (left) --------------------------------------------------
        table_frame = ttk.Frame(body)
        table_frame.pack(side="left", fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, show="headings")
        vsb = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.tree.yview
        )
        hsb = ttk.Scrollbar(
            table_frame, orient="horizontal", command=self.tree.xview
        )
        # Hide the cell overlay/editor when the view scrolls (their fixed
        # positions would otherwise drift out of place).
        self.tree.configure(
            yscrollcommand=lambda *a: (self._cancel_edit(), self._hide_highlight(), vsb.set(*a)),
            xscrollcommand=lambda *a: (self._cancel_edit(), self._hide_highlight(), hsb.set(*a)),
        )
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Overlay label used to paint the single selected cell, and the entry
        # used for in-place editing. Created once, repositioned as needed.
        self._cell_overlay = tk.Label(
            self.tree, background=self.CELL_HIGHLIGHT, foreground="white",
            anchor="w", padx=4,
        )
        self._editor = None

        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-1>", self._on_double_click)
        # Undo with Cmd+Z (mac) or Ctrl+Z while the table has focus.
        self.tree.bind("<Command-z>", self._on_undo_key)
        self.tree.bind("<Control-z>", self._on_undo_key)
        # The overlay covers the selected cell, so route its double-click into
        # the editor too (single click is a no-op: the cell is already chosen).
        self._cell_overlay.bind("<Double-1>", lambda e: self._start_edit())

    # ------------------------------------------------------------------ I/O
    def open_csv(self):
        path = filedialog.askopenfilename(
            title="Select CSV to view",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        # Setting the shared var triggers _on_active_change, which loads it.
        self.active_csv.set(path)

    def _on_active_change(self, *_):
        path = self.active_csv.get()
        if not path:
            return
        try:
            self.load_csv(path)
        except OSError as exc:
            messagebox.showerror("Read error", f"Could not read {path}:\n{exc}")

    def refresh(self):
        """Reload the currently selected CSV, if any."""
        if not self.current_path:
            messagebox.showinfo("No file", "Open a CSV first.")
            return
        try:
            self.load_csv(self.current_path)
        except OSError as exc:
            messagebox.showerror(
                "Read error", f"Could not read {self.current_path}:\n{exc}"
            )

    def load_csv(self, path):
        self._cancel_edit()
        self._hide_highlight()
        # Reloading the same file (e.g. Refresh) keeps the undo history; only
        # switching to a different file resets it.
        if path != self.current_path:
            self._undo_stack.clear()
            self._update_undo_state()
        self.current_path = path
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        # Reset the table.
        self.tree.delete(*self.tree.get_children())
        if not rows:
            self.tree["columns"] = ()
            self._amount_idx = None
            self.total_var.set("0.00")
            self.file_label.config(text=os.path.basename(path))
            return

        header = rows[0]
        self.tree["columns"] = header
        for col in header:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="w")

        # Find the amount column for the total (case-insensitive match).
        self._amount_idx = None
        for i, col in enumerate(header):
            if col.strip().lower() == "amount":
                self._amount_idx = i
                break

        for row in rows[1:]:
            self.tree.insert("", "end", values=row)

        self._recompute_total()
        self.file_label.config(text=os.path.basename(path))

    def _autosave(self):
        """Write the current table back to the CSV after any change.

        Silent on success; only surfaces a dialog if the write fails.
        """
        if not self.current_path:
            return
        header = list(self.tree["columns"])
        try:
            with open(self.current_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for item in self.tree.get_children():
                    writer.writerow(self.tree.item(item, "values"))
        except OSError as exc:
            messagebox.showerror(
                "Write error", f"Could not write {self.current_path}:\n{exc}"
            )

    def delete_row(self):
        """Delete the highlighted row."""
        if not self._sel_item or self._sel_item not in self.tree.get_children():
            messagebox.showinfo("No row", "Click a row to select it first.")
            return
        self._cancel_edit()
        self._push_undo()
        self._hide_highlight()
        self.tree.delete(self._sel_item)
        self._sel_item = None
        self._sel_col = None
        self._recompute_total()
        self._autosave()

    def _recompute_total(self):
        total = 0.0
        if self._amount_idx is not None:
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                if self._amount_idx < len(values):
                    try:
                        total += float(values[self._amount_idx])
                    except ValueError:
                        pass
        self.total_var.set(f"{total:,.2f}")

    # ------------------------------------------------------------- undo
    MAX_UNDO = 5

    def _push_undo(self):
        """Snapshot the current table so the next change can be undone.

        Keeps only the most recent MAX_UNDO snapshots.
        """
        snapshot = [self.tree.item(i, "values") for i in self.tree.get_children()]
        self._undo_stack.append(snapshot)
        del self._undo_stack[: -self.MAX_UNDO]
        self._update_undo_state()

    def _on_undo_key(self, _event):
        self.undo()
        return "break"

    def _update_undo_state(self):
        self.undo_btn.configure(
            state="normal" if self._undo_stack else "disabled"
        )

    def undo(self):
        """Restore the table to the state before the last change."""
        if not self._undo_stack:
            return
        self._cancel_edit()
        self._hide_highlight()
        self._sel_item = None
        self._sel_col = None
        snapshot = self._undo_stack.pop()
        self.tree.delete(*self.tree.get_children())
        for values in snapshot:
            self.tree.insert("", "end", values=values)
        self._recompute_total()
        self._update_undo_state()
        self._autosave()

    # ----------------------------------------------------- selection / edit
    def _on_click(self, event):
        """Select the clicked cell: highlight its row and the cell itself."""
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        self._commit_edit()
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item or not col:
            return
        self._sel_item = item
        self._sel_col = col
        self._highlight()

    def _highlight(self):
        """Paint the row selection and the stronger single-cell overlay."""
        if not self._sel_item:
            return
        self.tree.selection_set(self._sel_item)
        bbox = self.tree.bbox(self._sel_item, self._sel_col)
        if not bbox:
            self._cell_overlay.place_forget()
            return
        x, y, w, h = bbox
        value = self.tree.set(self._sel_item, self._sel_col)
        self._cell_overlay.configure(text=value)
        self._cell_overlay.place(x=x, y=y, width=w, height=h)

    def _hide_highlight(self):
        self._cell_overlay.place_forget()

    def _on_double_click(self, event):
        """Open an in-place editor over the double-clicked cell."""
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item or not col:
            return
        self._sel_item = item
        self._sel_col = col
        self._highlight()
        self._start_edit()

    def _start_edit(self):
        """Open an in-place editor over the currently selected cell."""
        if not self._sel_item or self._sel_item not in self.tree.get_children():
            return
        item, col = self._sel_item, self._sel_col
        bbox = self.tree.bbox(item, col)
        if not bbox:
            return
        x, y, w, h = bbox
        self._cancel_edit()
        self._editor = tk.Entry(self.tree)
        self._editor.insert(0, self.tree.set(item, col))
        self._editor.select_range(0, "end")
        self._editor.place(x=x, y=y, width=w, height=h)
        self._editor.focus_set()
        self._editor.bind("<Return>", lambda e: self._commit_edit())
        self._editor.bind("<Escape>", lambda e: self._cancel_edit())
        self._editor.bind("<FocusOut>", lambda e: self._commit_edit())

    def _commit_edit(self):
        """Write the editor's value into the cell and tear the editor down."""
        if self._editor is None:
            return
        editor, self._editor = self._editor, None
        if self._sel_item and self._sel_item in self.tree.get_children():
            new_value = editor.get()
            if new_value != self.tree.set(self._sel_item, self._sel_col):
                self._push_undo()
                self.tree.set(self._sel_item, self._sel_col, new_value)
                self._recompute_total()
                self._autosave()
        editor.destroy()
        # Refresh the overlay so it shows the new value.
        self._highlight()

    def _cancel_edit(self):
        """Discard any in-progress edit without writing it back."""
        if self._editor is None:
            return
        editor, self._editor = self._editor, None
        editor.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fundraiser")
        self.geometry("860x480")

        # Shared across both pages: the active CSV file path.
        self.active_csv = tk.StringVar()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)
        notebook.add(EntryPage(notebook, self.active_csv), text="Enter Data")
        notebook.add(ViewPage(notebook, self.active_csv), text="View CSV")


if __name__ == "__main__":
    App().mainloop()
