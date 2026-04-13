import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3, os, sys, subprocess, webbrowser, urllib.parse, shutil
from datetime import datetime, date, timedelta

from database import (init_db, get_connection, verify_login, get_next_bill_no,
                      backup_database, get_shop_outstanding, rows_to_dicts, row_to_dict,
                      hash_password, APP_DIR)
from pdf_gen import (generate_bill_pdf, generate_company_order_pdf,
                     generate_delivery_route_pdf, generate_monthly_report_pdf)
from ui_helpers import *


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER UTILITIES
# ══════════════════════════════════════════════════════════════════════════════
def open_file(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception:
        pass
    messagebox.showinfo("File Ready", f"Saved at:\n{path}")


def today_str():
    return str(date.today())


def fmt_inr(val):
    try:
        return f"₹{float(val):,.2f}"
    except Exception:
        return "₹0.00"


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hangyo Distribution — Login")
        self.geometry("460x540")
        self.configure(bg=BG)
        self.resizable(False, False)
        setup_treeview_style()
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        w, h = 460, 540
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        tk.Frame(self, bg=ACCENT, height=6).pack(fill="x")
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=55, pady=25)

        lbl(body, "🍦", fg=ACCENT, font=("Segoe UI", 44), bg=BG).pack(pady=(10, 0))
        lbl(body, "HANGYO", fg=ACCENT, font=("Segoe UI", 24, "bold"), bg=BG).pack()
        lbl(body, "Ice Cream Distribution Manager", fg=SUBTEXT, font=F_BODY, bg=BG).pack(pady=(2, 28))

        c = card(body)
        c.pack(fill="x")
        inner = tk.Frame(c, bg=CARD, padx=28, pady=28)
        inner.pack(fill="x")

        lbl(inner, "Username", fg=SUBTEXT, font=F_SMALL, bg=CARD).pack(anchor="w")
        self.user_e = entry(inner, width=32)
        self.user_e.pack(fill="x", pady=(4, 14), ipady=8)

        lbl(inner, "Password", fg=SUBTEXT, font=F_SMALL, bg=CARD).pack(anchor="w")
        self.pass_e = entry(inner, width=32, show="●")
        self.pass_e.pack(fill="x", pady=(4, 22), ipady=8)

        btn(inner, "  LOGIN  →  ", self._login, pady=11).pack(fill="x")
        self.bind("<Return>", lambda e: self._login())

        lbl(body, "Default login:  admin  /  admin123",
            fg=SUBTEXT, font=F_SMALL, bg=BG).pack(pady=12)

    def _login(self):
        u = self.user_e.get().strip()
        p = self.pass_e.get().strip()
        if not u or not p:
            messagebox.showerror("Error", "Enter username and password")
            return
        user = verify_login(u, p)
        if user:
            self.destroy()
            MainApp(user).mainloop()
        else:
            messagebox.showerror("Login Failed", "Wrong username or password")
            self.pass_e.delete(0, tk.END)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
class MainApp(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.title(f"Hangyo Distribution Manager  —  {user['full_name'] or user['username']}")
        self.geometry("1280x760")
        self.configure(bg=BG)
        self.minsize(1100, 660)
        setup_treeview_style()
        self._center()
        self._build_shell()
        self._show_dashboard()

    def _center(self):
        self.update_idletasks()
        w, h = 1280, 760
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── Shell Layout ──────────────────────────────────────────────────────────
    def _build_shell(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR, width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo = tk.Frame(self.sidebar, bg=ACCENT, height=68)
        logo.pack(fill="x")
        logo.pack_propagate(False)
        lbl(logo, "🍦  HANGYO", fg=WHITE, font=("Segoe UI", 14, "bold"), bg=ACCENT).pack(expand=True)

        lbl(self.sidebar, f"  👤  {self.user['full_name'] or self.user['username']}",
            fg=SUBTEXT, font=F_SMALL, bg=SIDEBAR).pack(fill="x", pady=(8, 2))
        lbl(self.sidebar, f"  🔑  {self.user['role'].capitalize()}",
            fg=SUBTEXT, font=F_SMALL, bg=SIDEBAR).pack(fill="x", pady=(0, 6))
        separator(self.sidebar, padx=14)

        is_admin = self.user['role'] == 'admin'
        self._nav_items = [
            ("📊", "Dashboard",        self._show_dashboard,      True),
            ("📦", "Stock",            self._show_stock,           True),
            ("🧾", "Orders & Billing", self._show_orders,          True),
            ("💰", "Payments",         self._show_payments,        is_admin),
            ("🚚", "Deliveries",       self._show_deliveries,      True),
            ("📋", "Company Order",    self._show_company_order,   is_admin),
            ("📖", "Shop Khata",       self._show_khata,           is_admin),
            ("📊", "Monthly Report",   self._show_report,          is_admin),
            ("↩️",  "Returns",          self._show_returns,         is_admin),
            ("🏪", "Manage Shops",     self._show_shops,           is_admin),
            ("👥", "Manage Users",     self._show_users,           is_admin),
        ]
        self._nav_btns = []
        for icon, label, cmd, visible in self._nav_items:
            if not visible:
                continue
            b = tk.Button(self.sidebar,
                          text=f"  {icon}   {label}",
                          command=cmd, bg=SIDEBAR, fg=TEXT,
                          font=F_BODY, relief="flat", anchor="w",
                          activebackground=CARD, activeforeground=ACCENT,
                          cursor="hand2", padx=12, pady=9, bd=0)
            b.pack(fill="x", padx=8, pady=1)
            self._nav_btns.append((b, label))

        separator(self.sidebar, padx=14, pady=8)
        btn(self.sidebar, "💾  Backup Data", self._backup,
            color=CARD2, fg=SUBTEXT, padx=10, pady=7).pack(fill="x", padx=8, pady=2)
        btn(self.sidebar, "⏻   Logout", self._logout,
            color=CARD2, fg=DANGER, padx=10, pady=7).pack(fill="x", padx=8, pady=2, side="bottom")
        separator(self.sidebar, padx=14, pady=4)

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

    def _highlight(self, label):
        for b, lname in self._nav_btns:
            if lname == label:
                b.config(bg=CARD, fg=ACCENT)
            else:
                b.config(bg=SIDEBAR, fg=TEXT)

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _page_hdr(self, title, subtitle=""):
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="x", padx=24, pady=(18, 8))
        lbl(f, title, fg=TEXT, font=F_TITLE, bg=BG).pack(side="left")
        if subtitle:
            lbl(f, subtitle, fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left", padx=10, pady=8)
        return f

    def _toolbar(self):
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="x", padx=24, pady=(0, 8))
        return f

    def _logout(self):
        if messagebox.askyesno("Logout", "Logout and return to login?"):
            self.destroy()
            LoginWindow().mainloop()

    def _backup(self):
        try:
            dest = backup_database()
            messagebox.showinfo("Backup Done", f"Backup saved:\n{dest}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ══════════════════════════════════════════════════════════════════════════
    #  DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    def _show_dashboard(self):
        self._clear(); self._highlight("Dashboard")
        self._page_hdr("📊  Dashboard", f"  Welcome, {self.user['full_name'] or self.user['username']}!")

        # Date filter
        tf = tk.Frame(self.content, bg=BG)
        tf.pack(fill="x", padx=24, pady=(0, 6))
        lbl(tf, "View:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        self._dash_filter = combo(tf, ["Today", "This Week", "This Month", "All Time"], width=14)
        self._dash_filter.set("This Month")
        self._dash_filter.pack(side="left", padx=6, ipady=4)
        self._dash_filter.bind("<<ComboboxSelected>>", lambda e: self._refresh_dashboard())
        btn(tf, "🔔  View Overdue Payments", self._show_overdue,
            color=DANGER, padx=10, pady=5).pack(side="right")

        self._dash_stat_frame = tk.Frame(self.content, bg=BG)
        self._dash_stat_frame.pack(fill="x", padx=24)

        self._dash_bottom = tk.Frame(self.content, bg=BG)
        self._dash_bottom.pack(fill="both", expand=True, padx=24, pady=8)

        self._refresh_dashboard()

    def _refresh_dashboard(self):
        for w in self._dash_stat_frame.winfo_children():
            w.destroy()
        for w in self._dash_bottom.winfo_children():
            w.destroy()

        flt = self._dash_filter.get() if hasattr(self, '_dash_filter') else "This Month"
        today = date.today()
        if flt == "Today":
            d_from = str(today)
        elif flt == "This Week":
            d_from = str(today - timedelta(days=today.weekday()))
        elif flt == "This Month":
            d_from = str(today.replace(day=1))
        else:
            d_from = "2000-01-01"

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM products")
        total_products = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM products WHERE stock_qty <= low_stock_alert")
        low_stock = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM orders WHERE order_date>=?", (d_from,))
        orders_count = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(total_amount-paid_amount),0) FROM orders WHERE status!='Paid'")
        pending_amt = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM orders WHERE delivery_status='Pending' AND order_date>=?", (d_from,))
        pending_del = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM shops")
        total_shops = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE order_date>=?", (d_from,))
        total_billed = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(paid_amount),0) FROM orders WHERE order_date>=?", (d_from,))
        total_collected = c.fetchone()[0]
        # Expiry alerts
        alert_date = str(today + timedelta(days=30))
        c.execute("SELECT COUNT(*) FROM stock_receipt_items WHERE expiry_date!='' AND expiry_date<=?", (alert_date,))
        expiry_alert = c.fetchone()[0]
        conn.close()

        stats = [
            ("📦", "Total Products",    str(total_products),         ACCENT),
            ("⚠️",  "Low Stock Items",  str(low_stock),              DANGER if low_stock else SUCCESS),
            ("🧾", "Orders",           str(orders_count),            ACCENT),
            ("💰", "Amount Pending",   fmt_inr(pending_amt),         DANGER if pending_amt else SUCCESS),
            ("🚚", "Pending Delivery", str(pending_del),             WARNING if pending_del else SUCCESS),
            ("🏪", "Total Shops",      str(total_shops),             ACCENT),
            ("💵", "Billed",           fmt_inr(total_billed),        ACCENT),
            ("✅", "Collected",        fmt_inr(total_collected),      SUCCESS),
        ]
        if expiry_alert:
            stats.append(("🧊", "Expiry Alert",  str(expiry_alert), DANGER))

        for icon, label, value, color in stats:
            c2 = card(self._dash_stat_frame, padx=12, pady=12)
            c2.pack(side="left", fill="both", expand=True, padx=5, pady=4)
            lbl(c2, icon,   fg=color,   font=("Segoe UI", 20), bg=CARD).pack()
            lbl(c2, value,  fg=color,   font=("Segoe UI", 18, "bold"), bg=CARD).pack()
            lbl(c2, label,  fg=SUBTEXT, font=F_SMALL, bg=CARD).pack()

        # Recent orders table
        lbl(self._dash_bottom, "Recent Orders", fg=TEXT, font=F_HEAD,
            bg=BG).pack(anchor="w", pady=(4, 6))
        cols   = ("bill_no","shop","date","total","paid","pending","status","delivery")
        heads  = ("Bill No","Shop","Date","Total","Paid","Pending","Pay Status","Delivery")
        widths = [95, 170, 90, 95, 95, 95, 90, 90]
        tv_f, tree = make_treeview(self._dash_bottom, cols, heads, widths, height=9)
        tv_f.pack(fill="both", expand=True)

        conn = get_connection()
        rows = conn.execute("""
            SELECT o.bill_no, s.name, o.order_date,
                   o.total_amount, o.paid_amount,
                   (o.total_amount-o.paid_amount), o.status, o.delivery_status
            FROM orders o JOIN shops s ON o.shop_id=s.id
            WHERE o.order_date>=?
            ORDER BY o.id DESC LIMIT 30""", (d_from,)).fetchall()
        conn.close()
        for r in rows:
            row = tuple(r)
            tag = "paid" if row[6]=="Paid" else ("partial" if float(row[4])>0 else "unpaid")
            tree.insert("", "end", values=row, tags=(tag,))
        tree.tag_configure("paid",    foreground=SUCCESS)
        tree.tag_configure("partial", foreground=WARNING)
        tree.tag_configure("unpaid",  foreground=DANGER)

    def _show_overdue(self):
        dlg = FormDialog(self, "🔔 Overdue Payments", width=700, height=500)
        cols   = ("shop","bill_no","total","pending","due","days")
        heads  = ("Shop","Bill No","Total","Pending","Due Date","Days Overdue")
        widths = [160, 90, 90, 90, 100, 100]
        tv_f, tree = make_treeview(dlg.body, cols, heads, widths, height=10)
        tv_f.pack(fill="both", expand=True)
        conn = get_connection()
        rows = conn.execute("""
            SELECT s.name, o.bill_no, o.total_amount,
                   (o.total_amount-o.paid_amount), o.due_date, o.id
            FROM orders o JOIN shops s ON o.shop_id=s.id
            WHERE o.status!='Paid' AND o.due_date!='' AND o.due_date < date('now')
            ORDER BY o.due_date""").fetchall()
        conn.close()
        today = str(date.today())
        for r in rows:
            r = tuple(r)
            try:
                days = (date.today() - datetime.strptime(r[4], "%Y-%m-%d").date()).days
            except Exception:
                days = 0
            tree.insert("", "end",
                        values=(r[0], r[1], fmt_inr(r[2]), fmt_inr(r[3]), r[4], f"{days} days"),
                        tags=("over",))
        tree.tag_configure("over", foreground=DANGER)

    # ══════════════════════════════════════════════════════════════════════════
    #  STOCK MANAGEMENT
    # ══════════════════════════════════════════════════════════════════════════
    def _show_stock(self):
        self._clear(); self._highlight("Stock")
        self._page_hdr("📦  Stock Management")

        tb = self._toolbar()
        btn(tb, "+ Add Product",     self._add_product,  padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "✏️ Edit Selected",  self._edit_product, color=CARD2, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🗑 Delete",         self._del_product,  color=DANGER, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "📥 Receive Stock",  self._receive_stock, color=SUCCESS, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🧊 Batch / Expiry", self._show_batches, color=CARD2, padx=12, pady=6).pack(side="left", padx=3)

        # Search
        sf = tk.Frame(tb, bg=BG); sf.pack(side="right")
        lbl(sf, "Search:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        self._stock_search_var = tk.StringVar()
        se = entry(sf, width=22, var=self._stock_search_var)
        se.pack(side="left", padx=6, ipady=5)
        self._stock_search_var.trace_add("write", lambda *_: self._refresh_stock())

        cols   = ("id","name","category","price","stock","alert","status")
        heads  = ("ID","Product Name","Category","Price (₹)","Stock Qty","Alert At","Status")
        widths = [40, 210, 110, 90, 90, 80, 110]
        tv_f, self._stock_tree = make_treeview(self.content, cols, heads, widths, height=18)
        tv_f.pack(fill="both", expand=True, padx=24, pady=4)
        self._refresh_stock()

    def _refresh_stock(self):
        for r in self._stock_tree.get_children():
            self._stock_tree.delete(r)
        q = f"%{self._stock_search_var.get()}%"
        conn = get_connection()
        rows = conn.execute(
            "SELECT id,name,category,price,stock_qty,low_stock_alert FROM products "
            "WHERE name LIKE ? OR category LIKE ? ORDER BY name", (q, q)).fetchall()
        conn.close()
        for r in rows:
            r = tuple(r)
            status = "⚠️  Low Stock" if r[4] <= r[5] else "✅  OK"
            tag    = "low" if r[4] <= r[5] else "ok"
            self._stock_tree.insert("", "end",
                values=(r[0], r[1], r[2], fmt_inr(r[3]), r[4], r[5], status),
                tags=(tag,))
        self._stock_tree.tag_configure("low", foreground=DANGER)
        self._stock_tree.tag_configure("ok",  foreground=SUCCESS)

    def _add_product(self):
        self._product_form()

    def _edit_product(self):
        sel = self._stock_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a product to edit"); return
        pid = self._stock_tree.item(sel[0])['values'][0]
        self._product_form(product_id=pid)

    def _product_form(self, product_id=None):
        title = "Add New Product" if not product_id else "Edit Product"
        dlg = FormDialog(self, title, width=460, height=470)

        data = {}
        if product_id:
            conn = get_connection()
            r = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
            conn.close()
            data = row_to_dict(r)

        fields = {}
        for label_text, key, default in [
            ("Product Name *", "name", ""),
            ("Category",       "category", "General"),
            ("Selling Price (₹) *", "price", "0"),
            ("Current Stock Qty",   "stock_qty", "0"),
            ("Low Stock Alert At",  "low_stock_alert", "10"),
        ]:
            e = entry(dlg.body, width=36)
            e.insert(0, str(data.get(key, default)))
            dlg.field_row(label_text, e)
            fields[key] = e

        def save():
            name = fields['name'].get().strip()
            if not name:
                messagebox.showerror("Required", "Product name is required", parent=dlg); return
            try:
                price = float(fields['price'].get())
                qty   = float(fields['stock_qty'].get())
                alert = int(fields['low_stock_alert'].get())
            except ValueError:
                messagebox.showerror("Invalid", "Enter valid numbers for price/qty/alert", parent=dlg); return
            conn = get_connection()
            if product_id:
                conn.execute(
                    "UPDATE products SET name=?,category=?,price=?,stock_qty=?,low_stock_alert=? WHERE id=?",
                    (name, fields['category'].get().strip(), price, qty, alert, product_id))
            else:
                conn.execute(
                    "INSERT INTO products (name,category,price,stock_qty,low_stock_alert) VALUES (?,?,?,?,?)",
                    (name, fields['category'].get().strip(), price, qty, alert))
            conn.commit(); conn.close()
            messagebox.showinfo("Saved", "Product saved successfully!", parent=dlg)
            dlg.destroy(); self._refresh_stock()

        dlg.save_btn("💾  Save Product", save)

    def _del_product(self):
        sel = self._stock_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a product to delete"); return
        vals = self._stock_tree.item(sel[0])['values']
        if messagebox.askyesno("Confirm Delete", f"Delete '{vals[1]}'?\nThis cannot be undone."):
            conn = get_connection()
            conn.execute("DELETE FROM products WHERE id=?", (vals[0],))
            conn.commit(); conn.close()
            self._refresh_stock()

    def _receive_stock(self):
        dlg = FormDialog(self, "📥 Receive Stock from Hangyo", width=760, height=620)

        top = tk.Frame(dlg.body, bg=BG); top.pack(fill="x", pady=(0, 10))
        lbl(top, "Invoice No:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        inv_e = entry(top, width=20); inv_e.pack(side="left", padx=8, ipady=5)
        lbl(top, "Expiry Date:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        exp_e = entry(top, width=14); exp_e.insert(0, "YYYY-MM-DD"); exp_e.pack(side="left", padx=8, ipady=5)
        lbl(top, "Batch No:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        batch_e = entry(top, width=14); batch_e.pack(side="left", padx=8, ipady=5)

        cols   = ("id","name","category","stock","receive","cost")
        heads  = ("ID","Product","Category","Current Stock","Receive Qty","Cost Price")
        widths = [40, 190, 100, 110, 110, 100]
        tv_f, tree = make_treeview(dlg.body, cols, heads, widths, height=13)
        tv_f.pack(fill="both", expand=True)

        conn = get_connection()
        prods = conn.execute("SELECT id,name,category,stock_qty FROM products ORDER BY name").fetchall()
        conn.close()
        for p in prods:
            tree.insert("", "end", values=(p[0], p[1], p[2], p[3], 0, 0))

        lbl(dlg.body, "Double-click a row to set Receive Qty and Cost Price",
            fg=SUBTEXT, font=F_SMALL, bg=BG).pack(pady=4)

        def on_dbl(event):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0])['values']
            qty = simpledialog.askfloat("Quantity", f"Receive qty for '{vals[1]}':",
                                        initialvalue=vals[4], minvalue=0, parent=dlg)
            if qty is None: return
            cost = simpledialog.askfloat("Cost Price", f"Cost price per unit for '{vals[1]}':",
                                         initialvalue=vals[5], minvalue=0, parent=dlg)
            if cost is None: cost = 0
            tree.item(sel[0], values=(*vals[:4], qty, cost))
        tree.bind("<Double-1>", on_dbl)

        def save():
            items = [tree.item(c)['values'] for c in tree.get_children()
                     if float(tree.item(c)['values'][4]) > 0]
            if not items:
                messagebox.showerror("Error", "Set quantity for at least one product", parent=dlg); return
            conn = get_connection()
            rid = conn.execute(
                "INSERT INTO stock_receipts (invoice_no,notes) VALUES (?,?)",
                (inv_e.get(), "")).lastrowid
            for item in items:
                conn.execute(
                    "INSERT INTO stock_receipt_items (receipt_id,product_id,quantity,unit_price,batch_no,expiry_date) VALUES (?,?,?,?,?,?)",
                    (rid, item[0], item[4], item[5], batch_e.get(), exp_e.get()))
                conn.execute("UPDATE products SET stock_qty=stock_qty+? WHERE id=?", (item[4], item[0]))
            conn.commit(); conn.close()
            messagebox.showinfo("Done", "Stock received and updated!", parent=dlg)
            dlg.destroy(); self._refresh_stock()

        btn(dlg.body, "✅  Confirm Receipt", save, pady=9).pack(fill="x", pady=8)

    def _show_batches(self):
        dlg = FormDialog(self, "🧊 Batch & Expiry Tracking", width=800, height=520)
        cols   = ("product","batch","received","expiry","qty","status")
        heads  = ("Product","Batch No","Received Date","Expiry Date","Qty","Status")
        widths = [190, 100, 110, 110, 70, 120]
        tv_f, tree = make_treeview(dlg.body, cols, heads, widths, height=14)
        tv_f.pack(fill="both", expand=True)

        conn = get_connection()
        rows = conn.execute("""
            SELECT p.name, sri.batch_no, sr.receipt_date, sri.expiry_date, sri.quantity
            FROM stock_receipt_items sri
            JOIN products p ON sri.product_id=p.id
            JOIN stock_receipts sr ON sri.receipt_id=sr.id
            ORDER BY sri.expiry_date""").fetchall()
        conn.close()
        today = date.today()
        for r in rows:
            r = tuple(r)
            exp_str = r[3] or ""
            if exp_str and exp_str != "YYYY-MM-DD":
                try:
                    exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
                    days_left = (exp_date - today).days
                    if days_left < 0:
                        status = "❌ Expired"; tag = "expired"
                    elif days_left <= 7:
                        status = f"⚠️ {days_left}d left"; tag = "soon"
                    elif days_left <= 30:
                        status = f"🔶 {days_left}d left"; tag = "warn"
                    else:
                        status = f"✅ {days_left}d left"; tag = "ok"
                except Exception:
                    status = "—"; tag = "ok"
            else:
                status = "—"; tag = "ok"
            tree.insert("", "end", values=(*r, status), tags=(tag,))
        tree.tag_configure("expired", foreground=DANGER)
        tree.tag_configure("soon",    foreground=DANGER)
        tree.tag_configure("warn",    foreground=WARNING)
        tree.tag_configure("ok",      foreground=SUCCESS)

    # ══════════════════════════════════════════════════════════════════════════
    #  ORDERS & BILLING
    # ══════════════════════════════════════════════════════════════════════════
    def _show_orders(self):
        self._clear(); self._highlight("Orders & Billing")
        self._page_hdr("🧾  Orders & Billing")

        tb = self._toolbar()
        btn(tb, "+ New Order",          self._new_order,                   padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "✏️ Edit Order",        self._edit_order,       color=CARD2, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "👁 View / Print Bill", self._view_bill,        color=CARD2, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "💳 Record Payment",    self._record_payment,   color=SUCCESS, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "📱 WhatsApp Reminder", self._wa_reminder,      color="#25D366", padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🗑 Delete",            self._del_order,        color=DANGER, padx=12, pady=6).pack(side="left", padx=3)

        # Search
        sf = tk.Frame(tb, bg=BG); sf.pack(side="right")
        lbl(sf, "Search:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        self._order_search_var = tk.StringVar()
        entry(sf, width=20, var=self._order_search_var).pack(side="left", padx=6, ipady=5)
        self._order_search_var.trace_add("write", lambda *_: self._refresh_orders())

        cols   = ("bill_no","shop","date","due","total","paid","pending","status","delivery")
        heads  = ("Bill No","Shop","Date","Due Date","Total","Paid","Pending","Pay Status","Delivery")
        widths = [90, 155, 85, 85, 90, 90, 90, 90, 90]
        tv_f, self._orders_tree = make_treeview(self.content, cols, heads, widths, height=17)
        tv_f.pack(fill="both", expand=True, padx=24, pady=4)
        self._refresh_orders()

    def _refresh_orders(self):
        for r in self._orders_tree.get_children():
            self._orders_tree.delete(r)
        q = f"%{self._order_search_var.get()}%"
        conn = get_connection()
        rows = conn.execute("""
            SELECT o.bill_no, s.name, o.order_date, o.due_date,
                   o.total_amount, o.paid_amount,
                   (o.total_amount-o.paid_amount), o.status, o.delivery_status
            FROM orders o JOIN shops s ON o.shop_id=s.id
            WHERE s.name LIKE ? OR o.bill_no LIKE ?
            ORDER BY o.id DESC""", (q, q)).fetchall()
        conn.close()
        for r in rows:
            r = tuple(r)
            row = (r[0], r[1], r[2], r[3] or "—",
                   fmt_inr(r[4]), fmt_inr(r[5]), fmt_inr(r[6]),
                   r[7], r[8])
            tag = "paid" if r[7]=="Paid" else ("partial" if float(r[5])>0 else "unpaid")
            self._orders_tree.insert("", "end", values=row, tags=(tag,))
        self._orders_tree.tag_configure("paid",    foreground=SUCCESS)
        self._orders_tree.tag_configure("partial", foreground=WARNING)
        self._orders_tree.tag_configure("unpaid",  foreground=DANGER)

    def _get_selected_order_id(self, tree=None):
        t = tree or self._orders_tree
        sel = t.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select an order first"); return None
        bill_no = t.item(sel[0])['values'][0]
        conn = get_connection()
        order = row_to_dict(conn.execute("SELECT * FROM orders WHERE bill_no=?", (bill_no,)).fetchone())
        conn.close()
        return order

    def _new_order(self):
        self._order_form()

    def _edit_order(self):
        order = self._get_selected_order_id()
        if not order: return
        self._order_form(order_id=order['id'])

    def _order_form(self, order_id=None):
        title = "New Order / Bill" if not order_id else f"Edit Order"
        dlg = FormDialog(self, title, width=860, height=680)

        conn = get_connection()
        shops = conn.execute("SELECT id,name,phone FROM shops ORDER BY name").fetchall()
        existing = {}
        existing_items = {}
        if order_id:
            existing = row_to_dict(conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone())
            items = conn.execute(
                "SELECT product_id, quantity, unit_price FROM order_items WHERE order_id=?",
                (order_id,)).fetchall()
            existing_items = {str(r[0]): (r[1], r[2]) for r in items}
        conn.close()

        shop_names = [s[1] for s in shops]
        shop_map   = {s[1]: s[0] for s in shops}
        shop_id_map= {s[0]: s[1] for s in shops}

        top = tk.Frame(dlg.body, bg=BG); top.pack(fill="x", pady=(0,8))
        lbl(top, "Shop:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        shop_cb = combo(top, shop_names, width=22)
        if existing:
            shop_cb.set(shop_id_map.get(existing['shop_id'], ''))
        shop_cb.pack(side="left", padx=6, ipady=4)

        lbl(top, "Date:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        date_e = entry(top, width=12); date_e.insert(0, existing.get('order_date', today_str()))
        date_e.pack(side="left", padx=6, ipady=4)

        lbl(top, "Due Date:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        due_e = entry(top, width=12); due_e.insert(0, existing.get('due_date', ''))
        due_e.pack(side="left", padx=6, ipady=4)

        lbl(top, "Initial Payment ₹:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        pay_e = entry(top, width=10); pay_e.insert(0, str(existing.get('paid_amount', '0')))
        pay_e.pack(side="left", padx=6, ipady=4)

        cols   = ("id","name","cat","price","stock","qty","line_total")
        heads  = ("ID","Product","Category","Price ₹","In Stock","Order Qty","Line Total ₹")
        widths = [40, 190, 100, 80, 80, 80, 100]
        tv_f, tree = make_treeview(dlg.body, cols, heads, widths, height=13)
        tv_f.pack(fill="both", expand=True)

        conn = get_connection()
        prods = conn.execute("SELECT id,name,category,price,stock_qty FROM products ORDER BY name").fetchall()
        conn.close()
        for p in prods:
            prev = existing_items.get(str(p[0]))
            qty = prev[0] if prev else 0
            lt  = round(float(qty) * float(p[3]), 2)
            tree.insert("", "end", values=(p[0], p[1], p[2], p[3], p[4], qty, lt))

        total_var = tk.StringVar(value="Total: ₹0.00")
        lbl(dlg.body, "", fg=BG, font=F_SMALL, bg=BG).pack()
        total_lbl = lbl(dlg.body, "Total: ₹0.00", fg=ACCENT, font=F_MED, bg=BG)
        total_lbl.pack(anchor="e", padx=4)

        def recalc():
            total = sum(float(tree.item(c)['values'][6]) for c in tree.get_children())
            total_lbl.config(text=f"Total: {fmt_inr(total)}")

        def on_dbl(event):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0])['values']
            qty = simpledialog.askfloat("Order Qty",
                                        f"Enter qty for '{vals[1]}':\n(Current stock: {vals[4]})",
                                        initialvalue=vals[5], minvalue=0, parent=dlg)
            if qty is None: return
            lt = round(float(qty) * float(vals[3]), 2)
            tree.item(sel[0], values=(*vals[:5], qty, lt))
            recalc()
        tree.bind("<Double-1>", on_dbl)
        recalc()

        lbl(dlg.body, "Double-click a row to set order quantity",
            fg=SUBTEXT, font=F_SMALL, bg=BG).pack()

        def save():
            shop_name = shop_cb.get()
            if not shop_name:
                messagebox.showerror("Error", "Select a shop", parent=dlg); return
            shop_id = shop_map[shop_name]
            items = [tree.item(c)['values'] for c in tree.get_children()
                     if float(tree.item(c)['values'][5]) > 0]
            if not items:
                messagebox.showerror("Error", "Add at least one item", parent=dlg); return

            total = sum(float(i[6]) for i in items)
            try:
                paid = float(pay_e.get())
            except ValueError:
                paid = 0
            paid = min(paid, total)

            # Credit limit check
            conn = get_connection()
            shop_r = row_to_dict(conn.execute("SELECT * FROM shops WHERE id=?", (shop_id,)).fetchone())
            conn.close()
            outstanding = get_shop_outstanding(shop_id)
            if order_id:
                outstanding -= existing.get('total_amount', 0) - existing.get('paid_amount', 0)
            credit_limit = float(shop_r.get('credit_limit', 0))
            new_pending = (total - paid)
            if credit_limit > 0 and (outstanding + new_pending) > credit_limit:
                if not messagebox.askyesno(
                    "Credit Limit Warning",
                    f"⚠️ {shop_name} credit limit is {fmt_inr(credit_limit)}\n"
                    f"Current outstanding: {fmt_inr(outstanding)}\n"
                    f"This order pending: {fmt_inr(new_pending)}\n\n"
                    f"Total will be {fmt_inr(outstanding+new_pending)} — OVER LIMIT!\n\n"
                    f"Proceed anyway?", parent=dlg):
                    return

            status = "Paid" if paid >= total else ("Partial" if paid > 0 else "Pending")
            conn = get_connection()
            if order_id:
                # Restore old stock
                old_items = conn.execute(
                    "SELECT product_id, quantity FROM order_items WHERE order_id=?",
                    (order_id,)).fetchall()
                for oi in old_items:
                    conn.execute("UPDATE products SET stock_qty=stock_qty+? WHERE id=?",
                                 (oi[0], oi[1]))  # NOTE: stock only adjusted on delivery
                conn.execute("DELETE FROM order_items WHERE order_id=?", (order_id,))
                conn.execute("""UPDATE orders SET shop_id=?,order_date=?,due_date=?,
                                total_amount=?,paid_amount=?,status=?
                                WHERE id=?""",
                             (shop_id, date_e.get(), due_e.get(), total, paid, status, order_id))
                oid = order_id
            else:
                bill_no = get_next_bill_no()
                oid = conn.execute(
                    "INSERT INTO orders (bill_no,shop_id,order_date,due_date,total_amount,paid_amount,status) VALUES (?,?,?,?,?,?,?)",
                    (bill_no, shop_id, date_e.get(), due_e.get(), total, paid, status)).lastrowid
                if paid > 0:
                    conn.execute("INSERT INTO payments (order_id,amount) VALUES (?,?)", (oid, paid))
            for item in items:
                conn.execute(
                    "INSERT INTO order_items (order_id,product_id,quantity,unit_price,total_price) VALUES (?,?,?,?,?)",
                    (oid, item[0], item[5], item[3], item[6]))
                # Stock NOT deducted here — deducted on delivery
            conn.commit(); conn.close()
            messagebox.showinfo("✅ Saved", "Order saved successfully!", parent=dlg)
            dlg.destroy(); self._refresh_orders()

        btn(dlg.body, "✅  Save Order", save, pady=9).pack(fill="x", pady=6)

    def _view_bill(self):
        order = self._get_selected_order_id()
        if not order: return
        conn = get_connection()
        shop  = row_to_dict(conn.execute("SELECT * FROM shops WHERE id=?", (order['shop_id'],)).fetchone())
        items = rows_to_dicts(conn.execute("""
            SELECT oi.quantity, oi.unit_price, oi.total_price, p.name, p.category
            FROM order_items oi JOIN products p ON oi.product_id=p.id
            WHERE oi.order_id=?""", (order['id'],)).fetchall())
        conn.close()
        path = os.path.join(APP_DIR, f"bill_{order['bill_no']}.pdf")
        generate_bill_pdf(order, items, shop, path)
        open_file(path)

    def _record_payment(self):
        order = self._get_selected_order_id()
        if not order: return
        pending = float(order['total_amount']) - float(order['paid_amount'])
        if pending <= 0:
            messagebox.showinfo("Fully Paid", "This order is already fully paid!"); return

        dlg = FormDialog(self, "💳 Record Payment", width=420, height=340)
        lbl(dlg.body, f"Bill No:  {order['bill_no']}", fg=TEXT, font=F_LABEL, bg=BG).pack(anchor="w")
        lbl(dlg.body, f"Total:    {fmt_inr(order['total_amount'])}", fg=TEXT, font=F_BODY, bg=BG).pack(anchor="w", pady=2)
        lbl(dlg.body, f"Paid:     {fmt_inr(order['paid_amount'])}", fg=SUCCESS, font=F_BODY, bg=BG).pack(anchor="w", pady=2)
        lbl(dlg.body, f"Pending:  {fmt_inr(pending)}", fg=DANGER, font=F_LABEL, bg=BG).pack(anchor="w", pady=(2,12))

        amt_e = entry(dlg.body, width=30); amt_e.insert(0, str(round(pending, 2)))
        dlg.field_row("Payment Amount ₹ *", amt_e)
        note_e = entry(dlg.body, width=30)
        dlg.field_row("Notes (optional)", note_e)

        btn(dlg.body, "Full Amount", lambda: (amt_e.delete(0, tk.END), amt_e.insert(0, str(round(pending, 2)))),
            color=CARD2, padx=10, pady=5).pack(anchor="w", pady=2)

        def save():
            try:
                amt = float(amt_e.get())
                if amt <= 0: raise ValueError
                if amt > pending: amt = pending
            except ValueError:
                messagebox.showerror("Invalid", "Enter a valid amount", parent=dlg); return
            conn = get_connection()
            conn.execute("INSERT INTO payments (order_id,amount,notes) VALUES (?,?,?)",
                         (order['id'], amt, note_e.get()))
            new_paid = float(order['paid_amount']) + amt
            status = "Paid" if new_paid >= float(order['total_amount']) else "Partial"
            conn.execute("UPDATE orders SET paid_amount=?,status=? WHERE id=?",
                         (new_paid, status, order['id']))
            conn.commit(); conn.close()
            messagebox.showinfo("✅ Done", f"{fmt_inr(amt)} recorded!", parent=dlg)
            dlg.destroy(); self._refresh_orders()

        dlg.save_btn("💳  Record Payment", save)

    def _wa_reminder(self):
        order = self._get_selected_order_id()
        if not order: return
        pending = float(order['total_amount']) - float(order['paid_amount'])
        if pending <= 0:
            messagebox.showinfo("Fully Paid", "This order is already paid!"); return
        conn = get_connection()
        shop = row_to_dict(conn.execute("SELECT * FROM shops WHERE id=?", (order['shop_id'],)).fetchone())
        conn.close()
        msg = (f"🍦 *Hangyo Ice Cream — Payment Reminder*\n\n"
               f"Dear {shop.get('owner_name') or shop['name']},\n\n"
               f"This is a friendly reminder for the following outstanding payment:\n\n"
               f"📋 Bill No: *{order['bill_no']}*\n"
               f"📅 Date: {order['order_date']}\n"
               f"💰 Total: {fmt_inr(order['total_amount'])}\n"
               f"✅ Paid: {fmt_inr(order['paid_amount'])}\n"
               f"🔴 Pending: *{fmt_inr(pending)}*\n")
        if order.get('due_date'):
            msg += f"📆 Due Date: {order['due_date']}\n"
        msg += "\nKindly arrange the payment at your earliest convenience.\n\nThank you!"
        phone = shop.get('phone', '').strip().replace(' ','').replace('-','')
        url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}" if phone else \
              f"https://wa.me/?text={urllib.parse.quote(msg)}"
        webbrowser.open(url)

    def _del_order(self):
        order = self._get_selected_order_id()
        if not order: return
        if messagebox.askyesno("Confirm", f"Delete order {order['bill_no']}?\nThis cannot be undone."):
            conn = get_connection()
            conn.execute("DELETE FROM order_items WHERE order_id=?", (order['id'],))
            conn.execute("DELETE FROM payments WHERE order_id=?", (order['id'],))
            conn.execute("DELETE FROM orders WHERE id=?", (order['id'],))
            conn.commit(); conn.close()
            self._refresh_orders()

    # ══════════════════════════════════════════════════════════════════════════
    #  PAYMENTS
    # ══════════════════════════════════════════════════════════════════════════
    def _show_payments(self):
        self._clear(); self._highlight("Payments")
        self._page_hdr("💰  Payment Tracker")

        tb = self._toolbar()
        btn(tb, "💳 Record Payment",    self._quick_pay,         padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "📱 WhatsApp Reminder", self._wa_reminder_pay,   color="#25D366", padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🔄 Refresh",          self._refresh_payments,  color=CARD2, padx=12, pady=6).pack(side="left", padx=3)

        # Summary cards
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT COALESCE(SUM(total_amount),0), COALESCE(SUM(paid_amount),0) FROM orders")
        row = c.fetchone()
        conn.close()
        total_b = row[0]; total_c = row[1]; total_p = total_b - total_c

        sf = tk.Frame(self.content, bg=BG)
        sf.pack(fill="x", padx=24, pady=4)
        for label, val, color in [
            ("Total Billed", fmt_inr(total_b), ACCENT),
            ("Collected",    fmt_inr(total_c), SUCCESS),
            ("Pending",      fmt_inr(total_p), DANGER),
        ]:
            c2 = card(sf, padx=20, pady=14)
            c2.pack(side="left", fill="both", expand=True, padx=6, pady=4)
            lbl(c2, val,   fg=color,   font=("Segoe UI", 18, "bold"), bg=CARD).pack()
            lbl(c2, label, fg=SUBTEXT, font=F_SMALL, bg=CARD).pack()

        # Filter
        ff = tk.Frame(self.content, bg=BG); ff.pack(fill="x", padx=24, pady=(0,4))
        lbl(ff, "Filter:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        self._pay_filter = combo(ff, ["All", "Pending", "Partial", "Paid"], width=14)
        self._pay_filter.set("All")
        self._pay_filter.pack(side="left", padx=6, ipady=4)
        self._pay_filter.bind("<<ComboboxSelected>>", lambda e: self._refresh_payments())

        cols   = ("bill_no","shop","date","due","total","paid","pending","status")
        heads  = ("Bill No","Shop","Date","Due Date","Total","Paid","Pending","Status")
        widths = [90, 160, 85, 85, 90, 90, 90, 90]
        tv_f, self._pay_tree = make_treeview(self.content, cols, heads, widths, height=12)
        tv_f.pack(fill="both", expand=True, padx=24, pady=4)
        self._refresh_payments()

    def _refresh_payments(self):
        for r in self._pay_tree.get_children():
            self._pay_tree.delete(r)
        flt = self._pay_filter.get() if hasattr(self, '_pay_filter') else "All"
        where = "" if flt == "All" else f" AND o.status='{flt}'"
        conn = get_connection()
        rows = conn.execute(f"""
            SELECT o.bill_no, s.name, o.order_date, o.due_date,
                   o.total_amount, o.paid_amount,
                   (o.total_amount-o.paid_amount), o.status
            FROM orders o JOIN shops s ON o.shop_id=s.id
            WHERE 1=1 {where}
            ORDER BY o.id DESC""").fetchall()
        conn.close()
        for r in rows:
            r = tuple(r)
            row = (r[0], r[1], r[2], r[3] or "—",
                   fmt_inr(r[4]), fmt_inr(r[5]), fmt_inr(r[6]), r[7])
            tag = "paid" if r[7]=="Paid" else ("partial" if float(r[5])>0 else "unpaid")
            self._pay_tree.insert("", "end", values=row, tags=(tag,))
        self._pay_tree.tag_configure("paid",    foreground=SUCCESS)
        self._pay_tree.tag_configure("partial", foreground=WARNING)
        self._pay_tree.tag_configure("unpaid",  foreground=DANGER)

    def _quick_pay(self):
        order = self._get_selected_order_id(self._pay_tree)
        if not order: return
        pending = float(order['total_amount']) - float(order['paid_amount'])
        if pending <= 0:
            messagebox.showinfo("Paid", "Already fully paid!"); return
        amt = simpledialog.askfloat("Payment",
                                    f"Bill: {order['bill_no']}\nPending: {fmt_inr(pending)}\nEnter amount:",
                                    minvalue=0.01, maxvalue=pending)
        if not amt: return
        conn = get_connection()
        conn.execute("INSERT INTO payments (order_id,amount) VALUES (?,?)", (order['id'], amt))
        new_paid = float(order['paid_amount']) + amt
        status = "Paid" if new_paid >= float(order['total_amount']) else "Partial"
        conn.execute("UPDATE orders SET paid_amount=?,status=? WHERE id=?",
                     (new_paid, status, order['id']))
        conn.commit(); conn.close()
        messagebox.showinfo("Done", f"{fmt_inr(amt)} recorded!")
        self._refresh_payments()

    def _wa_reminder_pay(self):
        sel = self._pay_tree.selection()
        if not sel: messagebox.showwarning("Select", "Select an order"); return
        bill_no = self._pay_tree.item(sel[0])['values'][0]
        conn = get_connection()
        order = row_to_dict(conn.execute("SELECT * FROM orders WHERE bill_no=?", (bill_no,)).fetchone())
        conn.close()
        pending = float(order['total_amount']) - float(order['paid_amount'])
        if pending <= 0:
            messagebox.showinfo("Paid", "Already paid!"); return
        conn = get_connection()
        shop = row_to_dict(conn.execute("SELECT * FROM shops WHERE id=?", (order['shop_id'],)).fetchone())
        conn.close()
        msg = (f"🍦 *Hangyo Ice Cream — Payment Reminder*\n\n"
               f"Dear {shop.get('owner_name') or shop['name']},\n\n"
               f"📋 Bill No: *{order['bill_no']}*\n"
               f"🔴 Pending: *{fmt_inr(pending)}*\n\n"
               f"Please arrange payment. Thank you!")
        phone = shop.get('phone', '').strip().replace(' ','').replace('-','')
        url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}" if phone else \
              f"https://wa.me/?text={urllib.parse.quote(msg)}"
        webbrowser.open(url)

    # ══════════════════════════════════════════════════════════════════════════
    #  DELIVERIES
    # ══════════════════════════════════════════════════════════════════════════
    def _show_deliveries(self):
        self._clear(); self._highlight("Deliveries")
        self._page_hdr("🚚  Delivery Management")

        tb = self._toolbar()
        btn(tb, "✅ Mark Delivered",    self._mark_delivered,    color=SUCCESS, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "📄 Print Route Sheet", self._print_route,       color=CARD2, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🔄 Refresh",          self._refresh_deliveries, color=CARD2, padx=12, pady=6).pack(side="left", padx=3)

        ff = tk.Frame(tb, bg=BG); ff.pack(side="right")
        lbl(ff, "Filter:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        self._del_filter = combo(ff, ["Pending", "Delivered", "All"], width=14)
        self._del_filter.set("Pending")
        self._del_filter.pack(side="left", padx=6, ipady=4)
        self._del_filter.bind("<<ComboboxSelected>>", lambda e: self._refresh_deliveries())

        cols   = ("bill_no","shop","phone","address","date","items","total","status")
        heads  = ("Bill No","Shop","Phone","Address","Date","Items","Total ₹","Delivery")
        widths = [90, 150, 100, 180, 85, 55, 85, 90]
        tv_f, self._del_tree = make_treeview(self.content, cols, heads, widths, height=18)
        tv_f.pack(fill="both", expand=True, padx=24, pady=4)
        self._refresh_deliveries()

    def _refresh_deliveries(self):
        for r in self._del_tree.get_children():
            self._del_tree.delete(r)
        flt = self._del_filter.get() if hasattr(self, '_del_filter') else "Pending"
        where = "" if flt=="All" else f" AND o.delivery_status='{flt}'"
        conn = get_connection()
        rows = conn.execute(f"""
            SELECT o.bill_no, s.name, s.phone, s.address, o.order_date,
                   COUNT(oi.id), o.total_amount, o.delivery_status
            FROM orders o
            JOIN shops s ON o.shop_id=s.id
            LEFT JOIN order_items oi ON oi.order_id=o.id
            WHERE 1=1 {where}
            GROUP BY o.id ORDER BY o.order_date DESC""").fetchall()
        conn.close()
        for r in rows:
            r = tuple(r)
            tag = "delivered" if r[7]=="Delivered" else "pend"
            self._del_tree.insert("", "end",
                values=(r[0], r[1], r[2] or "—", r[3] or "—", r[4], r[5], fmt_inr(r[6]), r[7]),
                tags=(tag,))
        self._del_tree.tag_configure("delivered", foreground=SUCCESS)
        self._del_tree.tag_configure("pend",      foreground=WARNING)

    def _mark_delivered(self):
        sel = self._del_tree.selection()
        if not sel: messagebox.showwarning("Select", "Select an order"); return
        bill_no = self._del_tree.item(sel[0])['values'][0]
        conn = get_connection()
        order = row_to_dict(conn.execute("SELECT * FROM orders WHERE bill_no=?", (bill_no,)).fetchone())
        if order.get('delivery_status') == 'Delivered':
            conn.close()
            messagebox.showinfo("Already", "This order is already marked as Delivered!"); return
        # Deduct stock on delivery
        items = conn.execute(
            "SELECT product_id, quantity FROM order_items WHERE order_id=?",
            (order['id'],)).fetchall()
        for item in items:
            conn.execute("UPDATE products SET stock_qty=MAX(0, stock_qty-?) WHERE id=?",
                         (item[0], item[1]))
        conn.execute("UPDATE orders SET delivery_status='Delivered' WHERE bill_no=?", (bill_no,))
        conn.commit(); conn.close()
        messagebox.showinfo("✅ Done", f"Order {bill_no} marked as Delivered!\nStock has been updated.")
        self._refresh_deliveries()

    def _print_route(self):
        conn = get_connection()
        rows = conn.execute("""
            SELECT o.bill_no, s.name, s.phone, s.address,
                   o.order_date, COUNT(oi.id), o.total_amount
            FROM orders o
            JOIN shops s ON o.shop_id=s.id
            LEFT JOIN order_items oi ON oi.order_id=o.id
            WHERE o.delivery_status='Pending'
            GROUP BY o.id ORDER BY s.name""").fetchall()
        conn.close()
        if not rows:
            messagebox.showinfo("No Orders", "No pending deliveries to print!"); return
        order_dicts = [{'bill_no': r[0], 'shop_name': r[1], 'phone': r[2],
                        'address': r[3], 'order_date': r[4],
                        'items_count': r[5], 'total_amount': r[6]} for r in rows]
        path = os.path.join(APP_DIR, f"delivery_route_{today_str()}.pdf")
        generate_delivery_route_pdf(today_str(), order_dicts, path)
        open_file(path)

    # ══════════════════════════════════════════════════════════════════════════
    #  COMPANY ORDER
    # ══════════════════════════════════════════════════════════════════════════
    def _show_company_order(self):
        self._clear(); self._highlight("Company Order")
        self._page_hdr("📋  Company Order (Order from Hangyo)")

        tb = self._toolbar()
        btn(tb, "+ New Order",       self._new_co,         padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "📄 Export PDF",     self._export_co_pdf,  color=CARD2, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "📱 Share WhatsApp", self._share_co_wa,    color="#25D366", padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🗑 Delete",         self._del_co,         color=DANGER, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🔄 Refresh",        self._refresh_co,     color=CARD2, padx=12, pady=6).pack(side="left", padx=3)

        # Low stock banner
        conn = get_connection()
        low = conn.execute("SELECT name FROM products WHERE stock_qty<=low_stock_alert").fetchall()
        conn.close()
        if low:
            banner = tk.Frame(self.content, bg="#2A1000", pady=6, padx=24)
            banner.pack(fill="x", padx=24)
            names = ", ".join([r[0] for r in low[:6]])
            lbl(banner, f"⚠️  Low stock: {names}{'...' if len(low)>6 else ''}  — Consider placing a company order!",
                fg=WARNING, font=F_SMALL, bg="#2A1000").pack(anchor="w")

        # Split layout
        pane = tk.Frame(self.content, bg=BG)
        pane.pack(fill="both", expand=True, padx=24, pady=4)

        left = tk.Frame(pane, bg=BG); left.pack(side="left", fill="both", expand=True)
        right = card(pane, padx=10, pady=10); right.pack(side="right", fill="both", expand=True, padx=(10,0))

        lbl(left, "Company Orders", fg=TEXT, font=F_HEAD, bg=BG).pack(anchor="w", pady=(0,6))
        cols  = ("id","date","items","status","notes")
        heads = ("ID","Date","Items","Status","Notes")
        widths= [50, 100, 70, 80, 240]
        tv_f, self._co_tree = make_treeview(left, cols, heads, widths, height=8)
        tv_f.pack(fill="both", expand=True)

        lbl(right, "Order Items", fg=ACCENT, font=F_LABEL, bg=CARD).pack(anchor="w", pady=(0,6))
        cols2  = ("name","cat","qty")
        heads2 = ("Product","Category","Qty")
        widths2= [190, 110, 80]
        tv_f2, self._co_detail = make_treeview(right, cols2, heads2, widths2, height=8)
        tv_f2.pack(fill="both", expand=True)

        self._co_tree.bind("<<TreeviewSelect>>", self._on_co_sel)
        self._refresh_co()

    def _refresh_co(self):
        for r in self._co_tree.get_children():
            self._co_tree.delete(r)
        conn = get_connection()
        rows = conn.execute("""
            SELECT co.id, co.order_date, COUNT(ci.id), co.status, co.notes
            FROM company_orders co
            LEFT JOIN company_order_items ci ON ci.company_order_id=co.id
            GROUP BY co.id ORDER BY co.id DESC""").fetchall()
        conn.close()
        for r in rows:
            self._co_tree.insert("", "end", values=tuple(r))

    def _on_co_sel(self, event):
        sel = self._co_tree.selection()
        if not sel: return
        co_id = self._co_tree.item(sel[0])['values'][0]
        for r in self._co_detail.get_children():
            self._co_detail.delete(r)
        conn = get_connection()
        items = conn.execute("""
            SELECT p.name, p.category, ci.quantity
            FROM company_order_items ci
            JOIN products p ON ci.product_id=p.id
            WHERE ci.company_order_id=?""", (co_id,)).fetchall()
        conn.close()
        for item in items:
            self._co_detail.insert("", "end", values=tuple(item))

    def _get_selected_co(self):
        sel = self._co_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a company order"); return None
        co_id = self._co_tree.item(sel[0])['values'][0]
        conn = get_connection()
        order = row_to_dict(conn.execute("SELECT * FROM company_orders WHERE id=?", (co_id,)).fetchone())
        items = rows_to_dicts(conn.execute("""
            SELECT p.name, p.category, ci.quantity, ci.product_id
            FROM company_order_items ci JOIN products p ON ci.product_id=p.id
            WHERE ci.company_order_id=?""", (co_id,)).fetchall())
        conn.close()
        return order, items

    def _new_co(self):
        dlg = FormDialog(self, "New Company Order", width=800, height=600)
        top = tk.Frame(dlg.body, bg=BG); top.pack(fill="x", pady=(0,10))
        lbl(top, "Notes:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        note_e = entry(top, width=45); note_e.pack(side="left", padx=8, ipady=5)

        cols   = ("id","name","cat","price","stock","alert","status","qty")
        heads  = ("ID","Product","Category","Price","Stock","Alert","Status","Order Qty")
        widths = [40, 180, 95, 75, 75, 60, 80, 85]
        tv_f, tree = make_treeview(dlg.body, cols, heads, widths, height=13)
        tv_f.pack(fill="both", expand=True)

        conn = get_connection()
        prods = conn.execute(
            "SELECT id,name,category,price,stock_qty,low_stock_alert FROM products ORDER BY stock_qty").fetchall()
        conn.close()
        for p in prods:
            status = "⚠️ Low" if float(p[4]) <= float(p[5]) else "✅ OK"
            tree.insert("", "end", values=(*tuple(p), status, 0),
                        tags=("low" if float(p[4])<=float(p[5]) else "ok",))
        tree.tag_configure("low", foreground=DANGER)
        tree.tag_configure("ok",  foreground=SUCCESS)

        def on_dbl(e):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0])['values']
            qty = simpledialog.askfloat("Order Qty", f"Qty to order for '{vals[1]}':",
                                        initialvalue=vals[7], minvalue=0, parent=dlg)
            if qty is not None:
                tree.item(sel[0], values=(*vals[:7], qty))
        tree.bind("<Double-1>", on_dbl)
        lbl(dlg.body, "Double-click row to set quantity  |  Low stock items shown first",
            fg=SUBTEXT, font=F_SMALL, bg=BG).pack(pady=4)

        def save():
            items = [tree.item(c)['values'] for c in tree.get_children()
                     if float(tree.item(c)['values'][7]) > 0]
            if not items:
                messagebox.showerror("Error", "Add at least one item", parent=dlg); return
            conn = get_connection()
            co_id = conn.execute(
                "INSERT INTO company_orders (order_date,notes) VALUES (?,?)",
                (today_str(), note_e.get())).lastrowid
            for item in items:
                conn.execute(
                    "INSERT INTO company_order_items (company_order_id,product_id,quantity) VALUES (?,?,?)",
                    (co_id, item[0], item[7]))
            conn.commit(); conn.close()
            messagebox.showinfo("✅ Saved", "Company order saved!")
            dlg.destroy(); self._refresh_co()
        btn(dlg.body, "💾  Save Company Order", save, pady=9).pack(fill="x", pady=6)

    def _export_co_pdf(self):
        result = self._get_selected_co()
        if not result: return
        order, items = result
        path = os.path.join(APP_DIR, f"company_order_{order['id']}.pdf")
        generate_company_order_pdf(order, items, path)
        open_file(path)

    def _share_co_wa(self):
        result = self._get_selected_co()
        if not result: return
        order, items = result
        msg = f"🍦 *Hangyo Stock Order Request*\nDate: {order['order_date']}  |  ID: CO-{order['id']}\n\n*Items Required:*\n"
        for i, item in enumerate(items, 1):
            msg += f"{i}. {item['name']} — Qty: {item['quantity']}\n"
        if order.get('notes'):
            msg += f"\nNotes: {order['notes']}"
        webbrowser.open(f"https://wa.me/?text={urllib.parse.quote(msg)}")

    def _del_co(self):
        result = self._get_selected_co()
        if not result: return
        order, _ = result
        if messagebox.askyesno("Confirm", f"Delete Company Order CO-{order['id']}?"):
            conn = get_connection()
            conn.execute("DELETE FROM company_order_items WHERE company_order_id=?", (order['id'],))
            conn.execute("DELETE FROM company_orders WHERE id=?", (order['id'],))
            conn.commit(); conn.close()
            self._refresh_co()
            for r in self._co_detail.get_children():
                self._co_detail.delete(r)

    # ══════════════════════════════════════════════════════════════════════════
    #  SHOP KHATA (LEDGER)
    # ══════════════════════════════════════════════════════════════════════════
    def _show_khata(self):
        self._clear(); self._highlight("Shop Khata")
        self._page_hdr("📖  Shop Khata (Account Ledger)")

        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", padx=24, pady=(0,8))
        lbl(top, "Select Shop:", fg=SUBTEXT, font=F_LABEL, bg=BG).pack(side="left")
        conn = get_connection()
        shops = conn.execute("SELECT id,name FROM shops ORDER BY name").fetchall()
        conn.close()
        shop_names = [s[1] for s in shops]
        self._khata_shop_map = {s[1]: s[0] for s in shops}
        self._khata_cb = combo(top, shop_names, width=30)
        self._khata_cb.pack(side="left", padx=8, ipady=4)
        btn(top, "📖 View Khata", self._load_khata, padx=12, pady=6).pack(side="left", padx=6)
        btn(top, "📄 Export PDF", self._export_khata_pdf, color=CARD2, padx=12, pady=6).pack(side="left", padx=3)

        # Summary cards
        self._khata_summary = tk.Frame(self.content, bg=BG)
        self._khata_summary.pack(fill="x", padx=24, pady=4)

        self._khata_body = tk.Frame(self.content, bg=BG)
        self._khata_body.pack(fill="both", expand=True, padx=24, pady=4)

    def _load_khata(self):
        shop_name = self._khata_cb.get()
        if not shop_name: messagebox.showwarning("Select", "Select a shop"); return
        shop_id = self._khata_shop_map[shop_name]

        for w in self._khata_summary.winfo_children(): w.destroy()
        for w in self._khata_body.winfo_children(): w.destroy()

        conn = get_connection()
        shop = row_to_dict(conn.execute("SELECT * FROM shops WHERE id=?", (shop_id,)).fetchone())
        orders = rows_to_dicts(conn.execute("""
            SELECT o.bill_no, o.order_date, o.due_date,
                   o.total_amount, o.paid_amount,
                   (o.total_amount-o.paid_amount), o.status, o.delivery_status
            FROM orders o WHERE o.shop_id=? ORDER BY o.id DESC""", (shop_id,)).fetchall())
        total_billed = sum(float(o['total_amount']) for o in orders)
        total_paid   = sum(float(o['paid_amount'])  for o in orders)
        total_pend   = total_billed - total_paid
        conn.close()

        # Shop info
        info_card = card(self._khata_summary, padx=16, pady=12)
        info_card.pack(side="left", fill="x", expand=True, padx=5, pady=4)
        lbl(info_card, f"🏪  {shop['name']}", fg=ACCENT, font=F_HEAD, bg=CARD).pack(anchor="w")
        lbl(info_card, f"👤  {shop.get('owner_name','—')}   📞  {shop.get('phone','—')}", fg=TEXT, font=F_BODY, bg=CARD).pack(anchor="w", pady=2)
        lbl(info_card, f"📍  {shop.get('address','—')}", fg=SUBTEXT, font=F_SMALL, bg=CARD).pack(anchor="w")
        if shop.get('notes'):
            lbl(info_card, f"📝  {shop['notes']}", fg=WARNING, font=F_SMALL, bg=CARD).pack(anchor="w", pady=2)
        lbl(info_card, f"💳  Credit Limit: {fmt_inr(shop.get('credit_limit',0))}", fg=SUBTEXT, font=F_SMALL, bg=CARD).pack(anchor="w")

        for label, val, color in [("Total Billed", fmt_inr(total_billed), ACCENT),
                                   ("Total Paid",   fmt_inr(total_paid),   SUCCESS),
                                   ("Outstanding",  fmt_inr(total_pend),   DANGER if total_pend>0 else SUCCESS)]:
            c2 = card(self._khata_summary, padx=16, pady=12)
            c2.pack(side="left", fill="both", expand=True, padx=5, pady=4)
            lbl(c2, val,   fg=color,   font=("Segoe UI", 16, "bold"), bg=CARD).pack()
            lbl(c2, label, fg=SUBTEXT, font=F_SMALL, bg=CARD).pack()

        cols   = ("bill_no","date","due","total","paid","pending","status","delivery")
        heads  = ("Bill No","Date","Due Date","Total","Paid","Pending","Pay Status","Delivery")
        widths = [90, 85, 85, 90, 90, 90, 90, 90]
        tv_f, tree = make_treeview(self._khata_body, cols, heads, widths, height=12)
        tv_f.pack(fill="both", expand=True)
        for o in orders:
            row = (o['bill_no'], o['order_date'], o.get('due_date','—') or '—',
                   fmt_inr(o['total_amount']), fmt_inr(o['paid_amount']),
                   fmt_inr(o['total_amount']-o['paid_amount']),
                   o['status'], o['delivery_status'])
            tag = "paid" if o['status']=="Paid" else ("partial" if float(o['paid_amount'])>0 else "unpaid")
            tree.insert("", "end", values=row, tags=(tag,))
        tree.tag_configure("paid",    foreground=SUCCESS)
        tree.tag_configure("partial", foreground=WARNING)
        tree.tag_configure("unpaid",  foreground=DANGER)
        self._khata_shop_id = shop_id

    def _export_khata_pdf(self):
        if not hasattr(self, '_khata_shop_id'):
            messagebox.showwarning("Select", "Load a shop khata first"); return
        shop_id = self._khata_shop_id
        conn = get_connection()
        shop   = row_to_dict(conn.execute("SELECT * FROM shops WHERE id=?", (shop_id,)).fetchone())
        orders = rows_to_dicts(conn.execute("""
            SELECT o.bill_no, o.order_date, o.due_date, o.total_amount, o.paid_amount,
                   (o.total_amount-o.paid_amount) as pending, o.status, o.delivery_status
            FROM orders o WHERE shop_id=? ORDER BY o.id DESC""", (shop_id,)).fetchall())
        conn.close()
        # Simple PDF via generate_monthly_report_pdf reuse
        total_b = sum(float(o['total_amount']) for o in orders)
        total_p = sum(float(o['paid_amount'])  for o in orders)
        path = os.path.join(APP_DIR, f"khata_{shop['name'].replace(' ','_')}.pdf")
        data = {
            'summary': {
                'total_orders': len(orders), 'total_billed': total_b,
                'total_collected': total_p, 'total_pending': total_b-total_p,
                'delivered': sum(1 for o in orders if o['delivery_status']=='Delivered'),
            },
            'top_shops': [], 'top_products': []
        }
        generate_monthly_report_pdf(f"Khata — {shop['name']}", data, path)
        open_file(path)

    # ══════════════════════════════════════════════════════════════════════════
    #  MONTHLY REPORT
    # ══════════════════════════════════════════════════════════════════════════
    def _show_report(self):
        self._clear(); self._highlight("Monthly Report")
        self._page_hdr("📊  Monthly Sales Report")

        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", padx=24, pady=(0,10))

        months = []
        today = date.today()
        for i in range(12):
            d = today.replace(day=1) - timedelta(days=i*28)
            months.append(d.strftime("%Y-%m"))
        months = sorted(list(set(months)), reverse=True)

        lbl(top, "Month:", fg=SUBTEXT, font=F_LABEL, bg=BG).pack(side="left")
        self._report_month = combo(top, months, width=14)
        self._report_month.set(today.strftime("%Y-%m"))
        self._report_month.pack(side="left", padx=8, ipady=4)
        btn(top, "📊 Generate Report", self._generate_report, padx=12, pady=6).pack(side="left", padx=6)
        btn(top, "📄 Export PDF", self._export_report_pdf, color=CARD2, padx=12, pady=6).pack(side="left", padx=3)

        self._report_area = tk.Frame(self.content, bg=BG)
        self._report_area.pack(fill="both", expand=True, padx=24, pady=4)
        self._report_data = None

    def _generate_report(self):
        for w in self._report_area.winfo_children(): w.destroy()
        month = self._report_month.get()
        d_from = f"{month}-01"
        try:
            y, m = int(month[:4]), int(month[5:7])
            import calendar
            last_day = calendar.monthrange(y, m)[1]
            d_to = f"{month}-{last_day:02d}"
        except Exception:
            d_to = f"{month}-31"

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM orders WHERE order_date BETWEEN ? AND ?", (d_from, d_to))
        total_orders = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(total_amount),0), COALESCE(SUM(paid_amount),0) FROM orders WHERE order_date BETWEEN ? AND ?", (d_from, d_to))
        r = c.fetchone(); total_billed = r[0]; total_collected = r[1]
        c.execute("SELECT COUNT(*) FROM orders WHERE order_date BETWEEN ? AND ? AND delivery_status='Delivered'", (d_from, d_to))
        delivered = c.fetchone()[0]

        top_prods = rows_to_dicts(conn.execute("""
            SELECT p.name, p.category,
                   SUM(oi.quantity) as total_qty,
                   SUM(oi.total_price) as revenue
            FROM order_items oi JOIN products p ON oi.product_id=p.id
            JOIN orders o ON oi.order_id=o.id
            WHERE o.order_date BETWEEN ? AND ?
            GROUP BY p.id ORDER BY revenue DESC LIMIT 10""", (d_from, d_to)).fetchall())

        top_shops = rows_to_dicts(conn.execute("""
            SELECT s.name,
                   COUNT(o.id) as orders,
                   SUM(o.total_amount) as billed,
                   SUM(o.paid_amount) as paid,
                   SUM(o.total_amount-o.paid_amount) as pending
            FROM orders o JOIN shops s ON o.shop_id=s.id
            WHERE o.order_date BETWEEN ? AND ?
            GROUP BY s.id ORDER BY billed DESC LIMIT 10""", (d_from, d_to)).fetchall())
        conn.close()

        self._report_data = {
            'summary': {
                'total_orders': total_orders,
                'total_billed': total_billed,
                'total_collected': total_collected,
                'total_pending': total_billed - total_collected,
                'delivered': delivered,
            },
            'top_products': top_prods,
            'top_shops': top_shops,
        }

        # Summary cards
        sf = tk.Frame(self._report_area, bg=BG)
        sf.pack(fill="x", pady=4)
        for label, val, color in [
            ("Total Orders",   str(total_orders),                  ACCENT),
            ("Total Billed",   fmt_inr(total_billed),              ACCENT),
            ("Collected",      fmt_inr(total_collected),           SUCCESS),
            ("Pending",        fmt_inr(total_billed-total_collected), DANGER if (total_billed-total_collected)>0 else SUCCESS),
            ("Delivered",      str(delivered),                     SUCCESS),
        ]:
            c2 = card(sf, padx=14, pady=12)
            c2.pack(side="left", fill="both", expand=True, padx=5, pady=4)
            lbl(c2, val,   fg=color,   font=("Segoe UI", 16, "bold"), bg=CARD).pack()
            lbl(c2, label, fg=SUBTEXT, font=F_SMALL, bg=CARD).pack()

        bot = tk.Frame(self._report_area, bg=BG)
        bot.pack(fill="both", expand=True, pady=4)

        left = tk.Frame(bot, bg=BG); left.pack(side="left", fill="both", expand=True, padx=(0,8))
        lbl(left, "🏆  Top Products", fg=TEXT, font=F_HEAD, bg=BG).pack(anchor="w", pady=(0,4))
        cols   = ("name","cat","qty","rev")
        heads  = ("Product","Category","Qty Sold","Revenue ₹")
        widths = [160, 100, 80, 100]
        tv_f, tree1 = make_treeview(left, cols, heads, widths, height=9)
        tv_f.pack(fill="both", expand=True)
        for p in top_prods:
            tree1.insert("", "end", values=(p['name'], p['category'],
                                             p['total_qty'], fmt_inr(p['revenue'])))

        right = tk.Frame(bot, bg=BG); right.pack(side="left", fill="both", expand=True)
        lbl(right, "🏪  Top Shops", fg=TEXT, font=F_HEAD, bg=BG).pack(anchor="w", pady=(0,4))
        cols2  = ("name","orders","billed","paid","pending")
        heads2 = ("Shop","Orders","Billed","Paid","Pending")
        widths2= [160, 60, 90, 90, 90]
        tv_f2, tree2 = make_treeview(right, cols2, heads2, widths2, height=9)
        tv_f2.pack(fill="both", expand=True)
        for s in top_shops:
            tree2.insert("", "end", values=(s['name'], s['orders'],
                                             fmt_inr(s['billed']), fmt_inr(s['paid']), fmt_inr(s['pending'])))

    def _export_report_pdf(self):
        if not self._report_data:
            messagebox.showwarning("Generate First", "Click 'Generate Report' first"); return
        month = self._report_month.get()
        path = os.path.join(APP_DIR, f"report_{month}.pdf")
        generate_monthly_report_pdf(month, self._report_data, path)
        open_file(path)

    # ══════════════════════════════════════════════════════════════════════════
    #  RETURNS / DAMAGED GOODS
    # ══════════════════════════════════════════════════════════════════════════
    def _show_returns(self):
        self._clear(); self._highlight("Returns")
        self._page_hdr("↩️  Returns & Damaged Goods")

        tb = self._toolbar()
        btn(tb, "+ New Return",   self._new_return,     padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🗑 Delete",      self._del_return,     color=DANGER, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🔄 Refresh",    self._refresh_returns, color=CARD2, padx=12, pady=6).pack(side="left", padx=3)

        cols   = ("id","shop","date","items","credit","reason")
        heads  = ("ID","Shop","Date","Items","Credit ₹","Reason")
        widths = [50, 170, 90, 60, 90, 280]
        tv_f, self._ret_tree = make_treeview(self.content, cols, heads, widths, height=18)
        tv_f.pack(fill="both", expand=True, padx=24, pady=4)
        self._refresh_returns()

    def _refresh_returns(self):
        for r in self._ret_tree.get_children():
            self._ret_tree.delete(r)
        conn = get_connection()
        rows = conn.execute("""
            SELECT r.id, s.name, r.return_date,
                   COUNT(ri.id), r.total_credit, r.reason
            FROM returns r
            JOIN shops s ON r.shop_id=s.id
            LEFT JOIN return_items ri ON ri.return_id=r.id
            GROUP BY r.id ORDER BY r.id DESC""").fetchall()
        conn.close()
        for r in rows:
            r = tuple(r)
            self._ret_tree.insert("", "end", values=(r[0], r[1], r[2], r[3], fmt_inr(r[4]), r[5] or "—"))

    def _new_return(self):
        dlg = FormDialog(self, "New Return / Damaged Goods", width=800, height=600)
        conn = get_connection()
        shops = conn.execute("SELECT id,name FROM shops ORDER BY name").fetchall()
        conn.close()
        shop_names = [s[1] for s in shops]
        shop_map   = {s[1]: s[0] for s in shops}

        top = tk.Frame(dlg.body, bg=BG); top.pack(fill="x", pady=(0,8))
        lbl(top, "Shop:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        shop_cb = combo(top, shop_names, width=22); shop_cb.pack(side="left", padx=6, ipady=4)
        lbl(top, "Reason:", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(side="left")
        reason_e = entry(top, width=28); reason_e.pack(side="left", padx=6, ipady=4)

        cols   = ("id","name","cat","price","qty","credit","condition")
        heads  = ("ID","Product","Category","Price","Return Qty","Credit ₹","Condition")
        widths = [40, 180, 90, 75, 80, 85, 100]
        tv_f, tree = make_treeview(dlg.body, cols, heads, widths, height=12)
        tv_f.pack(fill="both", expand=True)

        conn = get_connection()
        prods = conn.execute("SELECT id,name,category,price FROM products ORDER BY name").fetchall()
        conn.close()
        for p in prods:
            tree.insert("", "end", values=(p[0], p[1], p[2], p[3], 0, 0, "Damaged"))

        total_lbl = lbl(dlg.body, "Total Credit: ₹0.00", fg=ACCENT, font=F_MED, bg=BG)
        total_lbl.pack(anchor="e", padx=4, pady=4)

        def recalc():
            total = sum(float(tree.item(c)['values'][5]) for c in tree.get_children())
            total_lbl.config(text=f"Total Credit: {fmt_inr(total)}")

        def on_dbl(e):
            sel = tree.selection()
            if not sel: return
            vals = tree.item(sel[0])['values']
            qty = simpledialog.askfloat("Return Qty", f"Return qty for '{vals[1]}':",
                                        initialvalue=vals[4], minvalue=0, parent=dlg)
            if qty is None: return
            cond = simpledialog.askstring("Condition", "Condition (Damaged/Expired/Wrong Item):",
                                          initialvalue=vals[6], parent=dlg) or "Damaged"
            credit = round(float(qty) * float(vals[3]), 2)
            tree.item(sel[0], values=(*vals[:4], qty, credit, cond))
            recalc()
        tree.bind("<Double-1>", on_dbl)
        lbl(dlg.body, "Double-click to enter return quantity", fg=SUBTEXT, font=F_SMALL, bg=BG).pack()

        def save():
            shop_name = shop_cb.get()
            if not shop_name: messagebox.showerror("Error", "Select a shop", parent=dlg); return
            shop_id = shop_map[shop_name]
            items = [tree.item(c)['values'] for c in tree.get_children()
                     if float(tree.item(c)['values'][4]) > 0]
            if not items: messagebox.showerror("Error", "Add at least one item", parent=dlg); return
            total_credit = sum(float(i[5]) for i in items)
            conn = get_connection()
            rid = conn.execute(
                "INSERT INTO returns (shop_id,return_date,total_credit,reason) VALUES (?,?,?,?)",
                (shop_id, today_str(), total_credit, reason_e.get())).lastrowid
            for item in items:
                conn.execute(
                    "INSERT INTO return_items (return_id,product_id,quantity,unit_price,condition) VALUES (?,?,?,?,?)",
                    (rid, item[0], item[4], item[3], item[6]))
                conn.execute("UPDATE products SET stock_qty=stock_qty+? WHERE id=?", (item[4], item[0]))
            conn.commit(); conn.close()
            messagebox.showinfo("✅ Done", f"Return recorded!\nTotal Credit: {fmt_inr(total_credit)}", parent=dlg)
            dlg.destroy(); self._refresh_returns()
        btn(dlg.body, "✅  Save Return", save, pady=9).pack(fill="x", pady=6)

    def _del_return(self):
        sel = self._ret_tree.selection()
        if not sel: messagebox.showwarning("Select", "Select a return"); return
        rid = self._ret_tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", "Delete this return record?"):
            conn = get_connection()
            # Reverse stock
            items = conn.execute("SELECT product_id,quantity FROM return_items WHERE return_id=?", (rid,)).fetchall()
            for i in items:
                conn.execute("UPDATE products SET stock_qty=MAX(0,stock_qty-?) WHERE id=?", (i[0], i[1]))
            conn.execute("DELETE FROM return_items WHERE return_id=?", (rid,))
            conn.execute("DELETE FROM returns WHERE id=?", (rid,))
            conn.commit(); conn.close()
            self._refresh_returns()

    # ══════════════════════════════════════════════════════════════════════════
    #  MANAGE SHOPS
    # ══════════════════════════════════════════════════════════════════════════
    def _show_shops(self):
        self._clear(); self._highlight("Manage Shops")
        self._page_hdr("🏪  Manage Local Shops")

        tb = self._toolbar()
        btn(tb, "+ Add Shop",    self._add_shop,   padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "✏️ Edit",       self._edit_shop,  color=CARD2, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🗑 Delete",     self._del_shop,   color=DANGER, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "📖 View Khata", self._khata_from_shops, color=CARD2, padx=12, pady=6).pack(side="left", padx=3)

        cols   = ("id","name","owner","phone","address","credit","notes","outstanding")
        heads  = ("ID","Shop Name","Owner","Phone","Address","Credit Limit","Notes","Outstanding")
        widths = [40, 160, 130, 110, 160, 95, 130, 100]
        tv_f, self._shops_tree = make_treeview(self.content, cols, heads, widths, height=18)
        tv_f.pack(fill="both", expand=True, padx=24, pady=4)
        self._refresh_shops()

    def _refresh_shops(self):
        for r in self._shops_tree.get_children():
            self._shops_tree.delete(r)
        conn = get_connection()
        rows = conn.execute("SELECT id,name,owner_name,phone,address,credit_limit,notes FROM shops ORDER BY name").fetchall()
        conn.close()
        for r in rows:
            r = tuple(r)
            outstanding = get_shop_outstanding(r[0])
            tag = "over" if outstanding > 0 else "ok"
            self._shops_tree.insert("", "end",
                values=(r[0], r[1], r[2] or "—", r[3] or "—", r[4] or "—",
                        fmt_inr(r[5]), r[6] or "—", fmt_inr(outstanding)),
                tags=(tag,))
        self._shops_tree.tag_configure("over", foreground=WARNING)
        self._shops_tree.tag_configure("ok",   foreground=SUCCESS)

    def _add_shop(self): self._shop_form()
    def _edit_shop(self):
        sel = self._shops_tree.selection()
        if not sel: messagebox.showwarning("Select", "Select a shop"); return
        self._shop_form(shop_id=self._shops_tree.item(sel[0])['values'][0])

    def _shop_form(self, shop_id=None):
        title = "Add New Shop" if not shop_id else "Edit Shop"
        dlg = FormDialog(self, title, width=480, height=540)
        data = {}
        if shop_id:
            conn = get_connection()
            data = row_to_dict(conn.execute("SELECT * FROM shops WHERE id=?", (shop_id,)).fetchone())
            conn.close()
        fields = {}
        for label_text, key, default in [
            ("Shop Name *",      "name",        ""),
            ("Owner Name",       "owner_name",  ""),
            ("Phone Number",     "phone",       ""),
            ("Address",          "address",     ""),
            ("Credit Limit (₹)", "credit_limit","0"),
            ("Notes (e.g. Cash only, Trusted)", "notes", ""),
        ]:
            e = entry(dlg.body, width=38)
            e.insert(0, str(data.get(key, default) or ""))
            dlg.field_row(label_text, e)
            fields[key] = e

        def save():
            name = fields['name'].get().strip()
            if not name: messagebox.showerror("Required", "Shop name is required", parent=dlg); return
            try:
                credit = float(fields['credit_limit'].get() or 0)
            except ValueError:
                credit = 0
            conn = get_connection()
            if shop_id:
                conn.execute(
                    "UPDATE shops SET name=?,owner_name=?,phone=?,address=?,credit_limit=?,notes=? WHERE id=?",
                    (name, fields['owner_name'].get(), fields['phone'].get(),
                     fields['address'].get(), credit, fields['notes'].get(), shop_id))
            else:
                conn.execute(
                    "INSERT INTO shops (name,owner_name,phone,address,credit_limit,notes) VALUES (?,?,?,?,?,?)",
                    (name, fields['owner_name'].get(), fields['phone'].get(),
                     fields['address'].get(), credit, fields['notes'].get()))
            conn.commit(); conn.close()
            messagebox.showinfo("✅ Saved", "Shop saved!", parent=dlg)
            dlg.destroy(); self._refresh_shops()
        dlg.save_btn("💾  Save Shop", save)

    def _del_shop(self):
        sel = self._shops_tree.selection()
        if not sel: messagebox.showwarning("Select", "Select a shop"); return
        vals = self._shops_tree.item(sel[0])['values']
        if messagebox.askyesno("Confirm", f"Delete shop '{vals[1]}'? All orders will be affected!"):
            conn = get_connection()
            conn.execute("DELETE FROM shops WHERE id=?", (vals[0],))
            conn.commit(); conn.close()
            self._refresh_shops()

    def _khata_from_shops(self):
        sel = self._shops_tree.selection()
        if not sel: messagebox.showwarning("Select", "Select a shop"); return
        name = self._shops_tree.item(sel[0])['values'][1]
        self._show_khata()
        self._khata_cb.set(name)
        self._load_khata()

    # ══════════════════════════════════════════════════════════════════════════
    #  MANAGE USERS
    # ══════════════════════════════════════════════════════════════════════════
    def _show_users(self):
        self._clear(); self._highlight("Manage Users")
        self._page_hdr("👥  Manage Users & Staff")

        tb = self._toolbar()
        btn(tb, "+ Add User",  self._add_user,  padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "✏️ Edit",     self._edit_user, color=CARD2, padx=12, pady=6).pack(side="left", padx=3)
        btn(tb, "🗑 Delete",   self._del_user,  color=DANGER, padx=12, pady=6).pack(side="left", padx=3)

        cols   = ("id","username","full_name","role")
        heads  = ("ID","Username","Full Name","Role")
        widths = [50, 180, 220, 120]
        tv_f, self._users_tree = make_treeview(self.content, cols, heads, widths, height=14)
        tv_f.pack(fill="both", expand=True, padx=24, pady=4)

        note_card = card(self.content, padx=16, pady=12)
        note_card.pack(fill="x", padx=24, pady=4)
        lbl(note_card, "ℹ️  Roles:  admin — full access  |  staff — can view orders & deliveries only (no payments, no reports)",
            fg=SUBTEXT, font=F_SMALL, bg=CARD).pack(anchor="w")

        self._refresh_users()

    def _refresh_users(self):
        for r in self._users_tree.get_children():
            self._users_tree.delete(r)
        conn = get_connection()
        rows = conn.execute("SELECT id,username,full_name,role FROM users ORDER BY id").fetchall()
        conn.close()
        for r in rows:
            self._users_tree.insert("", "end", values=tuple(r))

    def _add_user(self): self._user_form()
    def _edit_user(self):
        sel = self._users_tree.selection()
        if not sel: messagebox.showwarning("Select", "Select a user"); return
        self._user_form(user_id=self._users_tree.item(sel[0])['values'][0])

    def _user_form(self, user_id=None):
        title = "Add New User" if not user_id else "Edit User"
        dlg = FormDialog(self, title, width=460, height=440)
        data = {}
        if user_id:
            conn = get_connection()
            data = row_to_dict(conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone())
            conn.close()
        fields = {}
        for label_text, key, default in [
            ("Full Name",  "full_name", ""),
            ("Username *", "username",  ""),
        ]:
            e = entry(dlg.body, width=36)
            e.insert(0, str(data.get(key, default) or ""))
            dlg.field_row(label_text, e)
            fields[key] = e

        lbl(dlg.body, "Role", fg=SUBTEXT, font=F_SMALL, bg=BG).pack(anchor="w")
        role_cb = combo(dlg.body, ["admin", "staff"], width=36)
        role_cb.set(data.get('role', 'staff'))
        role_cb.pack(fill="x", pady=(2,8), ipady=4)

        lbl(dlg.body, "Password *" + (" (leave blank to keep)" if user_id else ""),
            fg=SUBTEXT, font=F_SMALL, bg=BG).pack(anchor="w")
        pass_e = entry(dlg.body, width=36, show="●"); pass_e.pack(fill="x", pady=(2,8), ipady=7)

        def save():
            uname = fields['username'].get().strip()
            if not uname: messagebox.showerror("Required", "Username required", parent=dlg); return
            pwd = pass_e.get()
            if not user_id and not pwd:
                messagebox.showerror("Required", "Password required for new user", parent=dlg); return
            conn = get_connection()
            if user_id:
                if pwd:
                    conn.execute("UPDATE users SET full_name=?,username=?,role=?,password=? WHERE id=?",
                                 (fields['full_name'].get(), uname, role_cb.get(), hash_password(pwd), user_id))
                else:
                    conn.execute("UPDATE users SET full_name=?,username=?,role=? WHERE id=?",
                                 (fields['full_name'].get(), uname, role_cb.get(), user_id))
            else:
                conn.execute("INSERT INTO users (full_name,username,role,password) VALUES (?,?,?,?)",
                             (fields['full_name'].get(), uname, role_cb.get(), hash_password(pwd)))
            conn.commit(); conn.close()
            messagebox.showinfo("✅ Saved", "User saved!", parent=dlg)
            dlg.destroy(); self._refresh_users()
        dlg.save_btn("💾  Save User", save)

    def _del_user(self):
        sel = self._users_tree.selection()
        if not sel: messagebox.showwarning("Select", "Select a user"); return
        vals = self._users_tree.item(sel[0])['values']
        if vals[1] == 'admin':
            messagebox.showerror("Cannot Delete", "Cannot delete the admin user!"); return
        if messagebox.askyesno("Confirm", f"Delete user '{vals[1]}'?"):
            conn = get_connection()
            conn.execute("DELETE FROM users WHERE id=?", (vals[0],))
            conn.commit(); conn.close()
            self._refresh_users()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    init_db()
    LoginWindow().mainloop()
