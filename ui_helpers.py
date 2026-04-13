import tkinter as tk
from tkinter import ttk

# ── Palette ──────────────────────────────────────────────────────────────────
BG      = "#0F0F1A"
SIDEBAR = "#16162A"
CARD    = "#1E1E35"
CARD2   = "#252540"
ACCENT  = "#FF6B35"
ACCENT2 = "#FF9A5C"
TEXT    = "#F0F0F0"
SUBTEXT = "#9090B0"
SUCCESS = "#2ECC71"
WARNING = "#F39C12"
DANGER  = "#E74C3C"
WHITE   = "#FFFFFF"
BORDER  = "#2A2A45"
INPUT_BG= "#252545"

# ── Fonts ─────────────────────────────────────────────────────────────────────
F_TITLE  = ("Segoe UI", 20, "bold")
F_HEAD   = ("Segoe UI", 13, "bold")
F_BODY   = ("Segoe UI", 10)
F_SMALL  = ("Segoe UI", 9)
F_LABEL  = ("Segoe UI", 10, "bold")
F_BTN    = ("Segoe UI", 9,  "bold")
F_HUGE   = ("Segoe UI", 28, "bold")
F_MED    = ("Segoe UI", 15, "bold")


def setup_treeview_style():
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("H.Treeview",
                    background=CARD, foreground=TEXT,
                    fieldbackground=CARD, rowheight=30,
                    font=F_BODY, borderwidth=0)
    style.configure("H.Treeview.Heading",
                    background=ACCENT, foreground=WHITE,
                    font=F_LABEL, relief="flat", padding=6)
    style.map("H.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", WHITE)])
    style.configure("Vertical.TScrollbar",
                    background=CARD2, troughcolor=CARD,
                    arrowcolor=SUBTEXT)


def make_treeview(parent, columns, headings, col_widths, height=12, stretch_last=True):
    frame = tk.Frame(parent, bg=BG)
    tree = ttk.Treeview(frame, columns=columns, show="headings",
                         style="H.Treeview", height=height)
    for i, (col, head, w) in enumerate(zip(columns, headings, col_widths)):
        anchor = "w" if i in (1, 2, 3) else "center"
        stretch = (i == len(columns) - 1 and stretch_last)
        tree.heading(col, text=head)
        tree.column(col, width=w, anchor=anchor, stretch=stretch)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview, style="Vertical.TScrollbar")
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return frame, tree


def btn(parent, text, command, color=ACCENT, fg=WHITE, padx=16, pady=7, width=None):
    b = tk.Button(parent, text=text, command=command,
                  bg=color, fg=fg, font=F_BTN, relief="flat",
                  activebackground=ACCENT2, activeforeground=WHITE,
                  cursor="hand2", padx=padx, pady=pady, bd=0)
    if width:
        b.config(width=width)

    def on_enter(e):
        if color == ACCENT:
            b.config(bg=ACCENT2)
        else:
            r, g, b_val = parent.winfo_rgb(color)
            r, g, b_val = r // 256, g // 256, b_val // 256
            lighter = f'#{min(r+20,255):02x}{min(g+20,255):02x}{min(b_val+20,255):02x}'
            b.config(bg=lighter)

    def on_leave(e):
        b.config(bg=color)

    b.bind("<Enter>", on_enter)
    b.bind("<Leave>", on_leave)
    return b


def card(parent, **kw):
    return tk.Frame(parent, bg=CARD, **kw)


def lbl(parent, text, fg=TEXT, font=F_BODY, bg=None, **kw):
    return tk.Label(parent, text=text, fg=fg, font=font,
                    bg=bg if bg else (parent.cget('bg') if hasattr(parent, 'cget') else BG), **kw)


def entry(parent, width=28, show=None, var=None):
    kw = dict(bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
              font=F_BODY, relief="flat", bd=0, width=width,
              highlightthickness=1, highlightbackground=BORDER,
              highlightcolor=ACCENT)
    if show:
        kw['show'] = show
    if var:
        kw['textvariable'] = var
    return tk.Entry(parent, **kw)


def combo(parent, values, width=22, state="readonly"):
    style = ttk.Style()
    style.configure("H.TCombobox", fieldbackground=INPUT_BG, background=INPUT_BG,
                    foreground=TEXT, selectbackground=ACCENT, font=F_BODY)
    cb = ttk.Combobox(parent, values=values, width=width,
                      font=F_BODY, state=state, style="H.TCombobox")
    return cb


def separator(parent, color=BORDER, height=1, padx=0, pady=6):
    f = tk.Frame(parent, bg=color, height=height)
    f.pack(fill="x", padx=padx, pady=pady)
    return f


def toolbar_btn(parent, text, command, color=CARD, fg=TEXT):
    return btn(parent, text, command, color=color, fg=fg, padx=12, pady=6)


class ScrollableFrame(tk.Frame):
    """A frame with a vertical scrollbar."""
    def __init__(self, parent, bg=BG, **kw):
        super().__init__(parent, bg=bg, **kw)
        canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=bg)
        self.inner.bind("<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))


class FormDialog(tk.Toplevel):
    """Base class for consistent form dialogs."""
    def __init__(self, parent, title, width=460, height=500):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        # Center relative to parent
        parent.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        x = px + (pw - width) // 2
        y = py + (ph - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Header bar
        hdr = tk.Frame(self, bg=ACCENT, height=6)
        hdr.pack(fill="x")

        self._body = tk.Frame(self, bg=BG, padx=28, pady=18)
        self._body.pack(fill="both", expand=True)

        lbl(self._body, title.split("—")[0].strip(),
            fg=ACCENT, font=F_HEAD).pack(anchor="w", pady=(0, 14))

    @property
    def body(self):
        return self._body

    def field_row(self, label_text, widget=None, required=False):
        row = tk.Frame(self._body, bg=BG)
        row.pack(fill="x", pady=(0, 8))
        tag = " *" if required else ""
        lbl(row, label_text + tag, fg=SUBTEXT, font=F_SMALL).pack(anchor="w")
        if widget:
            widget.pack(fill="x", pady=(2, 0), ipady=7)
        return row

    def save_btn(self, text, command):
        btn(self._body, text, command, pady=10).pack(fill="x", pady=(12, 0))
