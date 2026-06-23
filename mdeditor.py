#!/usr/bin/env python3
"""CommonMark Editor - A GUI markdown editor with live preview."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import re
import os
import webbrowser


class MarkdownEditor:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1200x700")
        self.filepath = None
        self.modified = False

        self._build_ui()
        self._build_menubar()
        self._setup_preview_tags()
        self._setup_bindings()
        self.font_size = 14
        self._update_title()

    # ── Menu bar ────────────────────────────────────────────────

    def _build_menubar(self):
        mb = tk.Menu(self.root)
        self.root.config(menu=mb)

        fm = tk.Menu(mb, tearoff=0)
        fm.add_command(label="New File", command=self.new_file, accelerator="Ctrl+N")
        fm.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        fm.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        fm.add_command(label="Save as", command=self.save_as, accelerator="Ctrl+Shift+S")
        fm.add_command(label="Reopen", command=self.reopen_file, accelerator="Ctrl+R")
        fm.add_separator()
        fm.add_command(label="Quit", command=self._on_close, accelerator="Ctrl+Q")
        mb.add_cascade(label="File", menu=fm)

        em = tk.Menu(mb, tearoff=0)
        em.add_command(label="Undo", command=self.text.edit_undo, accelerator="Ctrl+Z")
        em.add_command(label="Redo", command=self.text.edit_redo, accelerator="Ctrl+Y")
        em.add_separator()
        em.add_command(label="Cut", command=lambda: self.text.event_generate("<<Cut>>"), accelerator="Ctrl+X")
        em.add_command(label="Copy", command=lambda: self.text.event_generate("<<Copy>>"), accelerator="Ctrl+C")
        em.add_command(label="Paste", command=lambda: self.text.event_generate("<<Paste>>"), accelerator="Ctrl+V")
        em.add_separator()
        em.add_command(label="Find", command=self.find_dialog, accelerator="Ctrl+F")
        em.add_command(label="Replace", command=self.replace_dialog, accelerator="Ctrl+H")
        em.add_separator()
        em.add_command(label="Delete Line", command=self.delete_line, accelerator="Ctrl+L")
        mb.add_cascade(label="Edit", menu=em)

        vm = tk.Menu(mb, tearoff=0)
        vm.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        vm.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        mb.add_cascade(label="View", menu=vm)

        fmtm = tk.Menu(mb, tearoff=0)
        fmtm.add_command(label="Bold", command=lambda: self.wrap_selection("**", "**"), accelerator="Ctrl+B")
        fmtm.add_command(label="Italic", command=lambda: self.wrap_selection("*", "*"), accelerator="Ctrl+T")
        fmtm.add_command(label="Underline", command=lambda: self.wrap_selection("<u>", "</u>"), accelerator="Ctrl+U")
        fmtm.add_command(label="Strikethrough", command=lambda: self.wrap_selection("~~", "~~"), accelerator="Ctrl+G")
        fmtm.add_command(label="Inline Code", command=lambda: self.wrap_selection("`", "`"), accelerator="Ctrl+K")
        fmtm.add_separator()
        fmtm.add_command(label="Heading ID", command=self.insert_heading_id_tag)
        fmtm.add_command(label="Heading Link", command=self.insert_heading_id)
        fmtm.add_separator()
        fmtm.add_command(label="Footnote", command=self.insert_footnote)
        fmtm.add_command(label="Hyperlink", command=self.insert_hyperlink)
        fmtm.add_separator()
        fmtm.add_command(label="Furigana", command=self.insert_furigana)
        mb.add_cascade(label="Format", menu=fmtm)

        pm = tk.Menu(mb, tearoff=0)
        pm.add_command(label="Heading 1", command=lambda: self.insert_heading(1))
        pm.add_command(label="Heading 2", command=lambda: self.insert_heading(2))
        pm.add_command(label="Heading 3", command=lambda: self.insert_heading(3))
        pm.add_separator()
        pm.add_command(label="Paragraph", command=lambda: self.text.insert(tk.INSERT, "\n\n"), accelerator="Ctrl+P")
        pm.add_command(label="Ordered List", command=lambda: self.text.insert(tk.INSERT, "1. "))
        pm.add_command(label="Unordered List", command=lambda: self.text.insert(tk.INSERT, "* "))
        pm.add_separator()
        pm.add_command(label="Code Block", command=self.insert_code_block)
        pm.add_command(label="Citation", command=lambda: self.text.insert(tk.INSERT, "> "))
        pm.add_command(label="Table", command=self.insert_table)
        pm.add_command(label="Image", command=self.insert_image)
        pm.add_separator()
        pm.add_command(label="Horizontal Rule", command=lambda: self.text.insert(tk.INSERT, "\n---\n"))
        pm.add_separator()
        pm.add_command(label="Comment", command=self.insert_comment, accelerator="Ctrl+M")
        pm.add_command(label="Comment Block", command=self.insert_comment_block, accelerator="Ctrl+Shift+M")
        mb.add_cascade(label="Paragraph", menu=pm)

        hm = tk.Menu(mb, tearoff=0)
        hm.add_command(label="CommonMarkdown Help",
                       command=lambda: webbrowser.open("https://commonmark.org/help/"))
        hm.add_separator()
        hm.add_command(label="About Editor", command=self.about_dialog)
        mb.add_cascade(label="Help", menu=hm)

    # ── UI layout ───────────────────────────────────────────────

    def _build_ui(self):
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        self.text = ScrolledText(paned, wrap=tk.WORD, undo=True,
                                 font=("Mono", 16), padx=10, pady=10)
        paned.add(self.text, weight=1)

        self.preview = ScrolledText(paned, wrap=tk.WORD, state=tk.DISABLED,
                                    font=("Serif", 16), padx=10, pady=10)
        paned.add(self.preview, weight=1)

    def _setup_preview_tags(self):
        p = self.preview
        p.tag_configure("h1", font=("Sans", 24, "bold"), spacing1=12, spacing3=6)
        p.tag_configure("h2", font=("Sans", 18, "bold"), spacing1=10, spacing3=5)
        p.tag_configure("h3", font=("Sans", 16, "bold"), spacing1=8, spacing3=4)
        p.tag_configure("bold", font=("Serif", 16, "bold"))
        p.tag_configure("italic", font=("Serif", 16, "italic"))
        p.tag_configure("bold_italic", font=("Serif", 16, "bold italic"))
        p.tag_configure("code", font=("Mono", 16), background="#f5f5f5")
        p.tag_configure("code_block", font=("Mono", 16), background="#f0f0f0",
                        spacing1=5, spacing3=5, lmargin1=10, lmargin2=10)
        p.tag_configure("blockquote", foreground="#666", font=("Serif", 16, "italic"),
                        lmargin1=20, lmargin2=20, spacing1=3, spacing3=3)
        p.tag_configure("strikethrough", overstrike=True)
        p.tag_configure("underline", underline=True)
        p.tag_configure("furigana", font=("Serif", 16), foreground="#888")
        p.tag_configure("link", foreground="#0645AD", underline=True)
        p.tag_configure("hr", foreground="#ccc")
        p.tag_configure("footnote_ref", font=("Serif", 16), offset=4)
        p.tag_configure("footnote_def", font=("Serif", 16), foreground="#666",
                        lmargin1=20, lmargin2=20, spacing1=2, spacing3=2)
        p.tag_configure("image", font=("Serif", 16, "italic"), foreground="#888",
                        background="#fafafa", spacing1=4, spacing3=4)
        p.tag_configure("table", font=("Mono", 16), spacing1=2, spacing3=2,
                        background="#fcfcfc")
        p.tag_configure("table_header", font=("Mono", 16),
                        background="#e8e8e8")
        p.tag_configure("table_sep", font=("Mono", 16), foreground="#aaa")

    def _setup_bindings(self):
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-N>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-S>", lambda e: self.save_as())
        self.root.bind("<Control-r>", lambda e: self.reopen_file())
        self.root.bind("<Control-R>", lambda e: self.reopen_file())
        self.root.bind("<Control-l>", lambda e: self.delete_line())
        self.root.bind("<Control-L>", lambda e: self.delete_line())
        self.root.bind("<Control-f>", lambda e: self.find_dialog())
        self.root.bind("<Control-F>", lambda e: self.find_dialog())
        self.root.bind("<Control-b>", lambda e: self.wrap_selection("**", "**") or "break")
        self.root.bind("<Control-B>", lambda e: self.wrap_selection("**", "**") or "break")
        self.root.bind("<Control-t>", lambda e: self.wrap_selection("*", "*") or "break")
        self.root.bind("<Control-T>", lambda e: self.wrap_selection("*", "*") or "break")
        self.root.bind("<Control-u>", lambda e: self.wrap_selection("<u>", "</u>") or "break")
        self.root.bind("<Control-U>", lambda e: self.wrap_selection("<u>", "</u>") or "break")
        self.root.bind("<Control-g>", lambda e: self.wrap_selection("~~", "~~") or "break")
        self.root.bind("<Control-G>", lambda e: self.wrap_selection("~~", "~~") or "break")
        self.root.bind("<Control-k>", lambda e: self.wrap_selection("`", "`") or "break")
        self.root.bind("<Control-K>", lambda e: self.wrap_selection("`", "`") or "break")
        self.root.bind("<Control-m>", lambda e: self.insert_comment())
        self.root.bind("<Control-M>", lambda e: self.insert_comment_block())
        self.root.bind("<Control-p>", lambda e: self.text.insert(tk.INSERT, "\n\n") or "break")
        self.root.bind("<Control-P>", lambda e: self.text.insert(tk.INSERT, "\n\n") or "break")
        self.root.bind("<Control-q>", lambda e: self._on_close())
        self.root.bind("<Control-Q>", lambda e: self._on_close())
        self.root.bind("<Control-plus>", lambda e: self.zoom_in())
        self.root.bind("<Control-KP_Add>", lambda e: self.zoom_in())
        self.root.bind("<Control-minus>", lambda e: self.zoom_out())
        self.root.bind("<Control-KP_Subtract>", lambda e: self.zoom_out())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Window helpers ──────────────────────────────────────────

    def _on_modified(self, event=None):
        if self.text.edit_modified():
            self.modified = True
            self._update_title()
            self.text.edit_modified(False)

    def _on_key_release(self, event=None):
        self._render_preview()

    def _on_close(self):
        if self.modified:
            r = messagebox.askyesnocancel("Unsaved Changes", "Save changes before closing?")
            if r is None:
                return
            if r:
                self.save_file()
        self.root.destroy()

    def _update_title(self):
        t = "CommonMark Editor"
        if self.filepath:
            t = f"{os.path.basename(self.filepath)} - {t}"
        if self.modified:
            t = f"* {t}"
        self.root.title(t)

    def about_dialog(self):
        messagebox.showinfo("About", "CommonMarkdown Editor\nversion 0.1, 2026-06-23",
                            parent=self.root)

    # ── View / Zoom ─────────────────────────────────────────────

    def zoom_in(self):
        self.font_size = min(self.font_size + 2, 40)
        self.text.config(font=("Mono", self.font_size))

    def zoom_out(self):
        self.font_size = max(self.font_size - 2, 6)
        self.text.config(font=("Mono", self.font_size))

    # ── File operations ─────────────────────────────────────────

    def new_file(self):
        if self.modified:
            r = messagebox.askyesnocancel("Unsaved Changes", "Save changes before creating new file?")
            if r is None:
                return
            if r:
                self.save_file()
        self.text.delete(1.0, tk.END)
        self.filepath = None
        self.modified = False
        self._update_title()
        self._render_preview()

    def open_file(self):
        if self.modified:
            r = messagebox.askyesnocancel("Unsaved Changes", "Save changes before opening?")
            if r is None:
                return
            if r:
                self.save_file()
        path = filedialog.askopenfilename(
            filetypes=[("Markdown files", "*.md *.markdown"), ("All files", "*.*")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.text.delete(1.0, tk.END)
                self.text.insert(1.0, f.read())
            self.filepath = path
            self.modified = False
            self._update_title()
            self._render_preview()

    def save_file(self):
        if not self.filepath:
            self.save_as()
            return
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(self.text.get(1.0, tk.END))
        self.modified = False
        self._update_title()

    def save_as(self):
        path = filedialog.asksaveasfilename(
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")],
            defaultextension=".md")
        if path:
            self.filepath = path
            self.save_file()

    def reopen_file(self):
        if not self.filepath:
            self.text.delete(1.0, tk.END)
            self.modified = False
            self._update_title()
            self._render_preview()
            return
        if self.modified:
            r = messagebox.askyesnocancel("Unsaved Changes",
                "Discard changes and reopen?")
            if r is None or not r:
                return
        with open(self.filepath, "r", encoding="utf-8") as f:
            self.text.delete(1.0, tk.END)
            self.text.insert(1.0, f.read())
        self.modified = False
        self._update_title()
        self._render_preview()

    # ── Edit operations ─────────────────────────────────────────

    def find_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Find")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(dlg, text="Find:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        find_var = tk.StringVar()
        tk.Entry(dlg, textvariable=find_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        def find_one():
            find = find_var.get()
            if not find:
                return
            content = self.text.get(1.0, tk.END)
            pos = content.find(find)
            if pos == -1:
                return
            lineno = content[:pos].count("\n") + 1
            char = pos - content[:pos].rfind("\n") - 1
            start = f"{lineno}.{char}"
            end = f"{lineno}.{char + len(find)}"
            self.text.tag_remove(tk.SEL, 1.0, tk.END)
            self.text.tag_add(tk.SEL, start, end)
            self.text.mark_set(tk.INSERT, end)
            self.text.see(tk.INSERT)

        def find_all():
            find = find_var.get()
            if not find:
                return
            self.text.tag_remove(tk.SEL, 1.0, tk.END)
            content = self.text.get(1.0, tk.END)
            pos = 0
            while True:
                pos = content.find(find, pos)
                if pos == -1:
                    break
                lineno = content[:pos].count("\n") + 1
                char = pos - content[:pos].rfind("\n") - 1
                start = f"{lineno}.{char}"
                end = f"{lineno}.{char + len(find)}"
                self.text.tag_add(tk.SEL, start, end)
                pos += len(find)

        frame = tk.Frame(dlg)
        frame.grid(row=1, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Find", command=find_one, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Find All", command=find_all, width=10).pack(side=tk.LEFT, padx=5)

        try:
            find_var.set(self.text.selection_get())
        except tk.TclError:
            pass
        dlg.grid_slaves(row=0, column=1)[0].focus_set()

    def replace_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Replace")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(dlg, text="Find:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        find_var = tk.StringVar()
        tk.Entry(dlg, textvariable=find_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(dlg, text="Replace:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        repl_var = tk.StringVar()
        tk.Entry(dlg, textvariable=repl_var, width=30).grid(row=1, column=1, padx=5, pady=5)

        def replace_one():
            find, repl = find_var.get(), repl_var.get()
            if not find:
                return
            content = self.text.get(1.0, tk.END)
            pos = content.find(find)
            if pos == -1:
                return
            before = content[:pos]
            after = content[pos + len(find):]
            self.text.delete(1.0, tk.END)
            self.text.insert(1.0, before + repl + after)
            self.modified = True
            self._update_title()
            self._render_preview()

        def replace_all():
            find, repl = find_var.get(), repl_var.get()
            if not find:
                return
            content = self.text.get(1.0, tk.END)
            if find in content:
                content = content.replace(find, repl)
                if content.endswith("\n"):
                    content = content[:-1]
                self.text.delete(1.0, tk.END)
                self.text.insert(1.0, content)
                self.modified = True
                self._update_title()
                self._render_preview()

        frame = tk.Frame(dlg)
        frame.grid(row=2, column=0, columnspan=2, pady=10)
        tk.Button(frame, text="Replace", command=replace_one, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Replace All", command=replace_all, width=10).pack(side=tk.LEFT, padx=5)

        try:
            find_var.set(self.text.selection_get())
        except tk.TclError:
            pass
        dlg.grid_slaves(row=0, column=1)[0].focus_set()

    def wrap_selection(self, prefix, suffix):
        try:
            start = self.text.index(tk.SEL_FIRST)
            end = self.text.index(tk.SEL_LAST)
            sel = self.text.get(start, end)
            self.text.delete(start, end)
            self.text.insert(start, f"{prefix}{sel}{suffix}")
            ins = f"{start} + {len(prefix) + len(sel)}c"
            self.text.mark_set(tk.INSERT, ins)
        except tk.TclError:
            self.text.insert(tk.INSERT, f"{prefix}{suffix}")
            self.text.mark_set(tk.INSERT, f"{tk.INSERT} - {len(suffix)}c")

    def _get_input(self, title, fields):
        dlg = tk.Toplevel(self.root)
        dlg.title(title)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        entries = []
        for i, (label, default) in enumerate(fields):
            tk.Label(dlg, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="e")
            var = tk.StringVar(value=default)
            tk.Entry(dlg, textvariable=var, width=30).grid(row=i, column=1, padx=5, pady=5)
            entries.append(var)

        result = []

        def confirm():
            result.append([v.get() for v in entries])
            dlg.destroy()

        tk.Button(dlg, text="Insert", command=confirm).grid(
            row=len(fields), column=0, columnspan=2, pady=10)

        dlg.wait_window()
        return result[0] if result else []

    def insert_heading_id_tag(self):
        vals = self._get_input("Heading ID", [("ID:", "custom-id")])
        if vals:
            self.text.insert(tk.INSERT, f"{{#{vals[0]}}}")

    def insert_heading_id(self):
        vals = self._get_input("Heading ID", [("Text:", "link text"), ("Heading ID:", "section")])
        if vals:
            self.text.insert(tk.INSERT, f"[{vals[0]}](#{vals[1]})")

    def insert_footnote(self):
        vals = self._get_input("Insert Footnote", [("ID:", "note1"), ("Text:", "Footnote text")])
        if vals:
            self.text.insert(tk.INSERT, f"[^{vals[0]}]")
            self.text.insert(tk.END, f"\n[^{vals[0]}]: {vals[1]}\n")

    def insert_hyperlink(self):
        vals = self._get_input("Insert Hyperlink", [("Text:", "link text"), ("URL:", "https://")])
        if vals:
            self.text.insert(tk.INSERT, f"[{vals[0]}]({vals[1]})")

    def insert_furigana(self):
        vals = self._get_input("Insert Furigana", [("Kanji:", "\u6F22\u5B57"), ("Reading:", "\u304B\u3093\u3058")])
        if vals:
            self.text.insert(tk.INSERT, f"<ruby>{vals[0]}<rt>{vals[1]}</rt></ruby>")

    def insert_heading(self, level):
        self.text.insert(tk.INSERT, "#" * level + " ")

    def insert_code_block(self):
        vals = self._get_input("Code Block", [("Language (optional):", "")])
        if not vals:
            return
        lang = vals[0].strip()
        self.text.insert(tk.INSERT, f"\n```{lang}\n\n```\n")
        self.text.mark_set(tk.INSERT, "insert - 2 lines linestart")

    def insert_table(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Insert Table")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(dlg, text="Columns:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        col_var = tk.IntVar(value=3)
        tk.Spinbox(dlg, from_=1, to=20, textvariable=col_var, width=5).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(dlg, text="Rows:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        row_var = tk.IntVar(value=3)
        tk.Spinbox(dlg, from_=1, to=50, textvariable=row_var, width=5).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        result = []
        def confirm():
            result.append((col_var.get(), row_var.get()))
            dlg.destroy()

        tk.Button(dlg, text="Insert", command=confirm).grid(
            row=2, column=0, columnspan=2, pady=10)

        dlg.wait_window()
        if not result:
            return
        cols, rows = result[0]

        headers = [f"Header {i+1}" for i in range(cols)]
        data = [[f"Cell {r+1}-{c+1}" for c in range(cols)] for r in range(rows)]
        widths = [max(len(headers[c]), max(len(data[r][c]) for r in range(rows)), 3) for c in range(cols)]

        def fmt_row(cells):
            return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"

        header = fmt_row(headers)
        sep = "| " + " | ".join("-" * widths[i] for i in range(cols)) + " |"
        body = "\n".join(fmt_row(data[r]) for r in range(rows))
        self.text.insert(tk.INSERT, f"\n{header}\n{sep}\n{body}\n")

    def insert_image(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Insert Image")
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(dlg, text="Alt text:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        alt_var = tk.StringVar(value="image description")
        tk.Entry(dlg, textvariable=alt_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        tk.Label(dlg, text="URL / Path:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        url_var = tk.StringVar()
        url_entry = tk.Entry(dlg, textvariable=url_var, width=30)
        url_entry.grid(row=1, column=1, padx=5, pady=5)

        def browse():
            path = filedialog.askopenfilename(
                filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.svg *.bmp"), ("All files", "*.*")])
            if path:
                url_var.set(path)

        tk.Button(dlg, text="Browse...", command=browse).grid(row=1, column=2, padx=2, pady=5)

        result = []
        def confirm():
            result.append((alt_var.get(), url_var.get()))
            dlg.destroy()

        tk.Button(dlg, text="Insert", command=confirm).grid(
            row=2, column=0, columnspan=3, pady=10)

        dlg.wait_window()
        if result:
            self.text.insert(tk.INSERT, f"![{result[0][0]}]({result[0][1]})")

    def delete_line(self):
        lineno = int(self.text.index(tk.INSERT).split(".")[0])
        start = f"{lineno}.0"
        end = f"{lineno}.end + 1c"
        self.text.delete(start, end)
        self.modified = True
        self._update_title()
        self._render_preview()

    def insert_comment(self):
        self.wrap_selection("<!-- ", " -->")

    def insert_comment_block(self):
        self.text.insert(tk.INSERT, "\n<!--\n\n-->\n")
        self.text.mark_set(tk.INSERT, "insert - 2 lines linestart")

    # ── Preview rendering ───────────────────────────────────────

    def _render_preview(self):
        content = self.text.get(1.0, tk.END)
        self.preview.config(state=tk.NORMAL)
        self.preview.delete(1.0, tk.END)

        lines = content.split("\n")
        i, n = 0, len(lines)
        in_code = False
        code_buf = []

        while i < n:
            line = lines[i]

            # ── fenced code block ──
            if line.strip().startswith("```"):
                if in_code:
                    self.preview.insert(tk.END, "\n".join(code_buf) + "\n", "code_block")
                    code_buf.clear()
                in_code = not in_code
                i += 1
                continue

            if in_code:
                code_buf.append(line)
                i += 1
                continue

            # ── empty line ──
            if not line.strip():
                i += 1
                continue

            # ── ATX heading ──
            m = re.match(r"^(#{1,3})\s+(.+)", line)
            if m:
                self._render_inline(m.group(2), (f"h{len(m.group(1))}",))
                self.preview.insert(tk.END, "\n")
                i += 1
                continue

            # ── thematic break ──
            if re.match(r"^[-*_]{3,}\s*$", line.strip()):
                self.preview.insert(tk.END, "\u2500" * 40 + "\n", "hr")
                i += 1
                continue

            # ── blockquote ──
            if line.startswith(">"):
                txt = re.sub(r"^>\s?", "", line)
                self._render_inline(txt, ("blockquote",))
                self.preview.insert(tk.END, "\n")
                i += 1
                continue

            # ── unordered list ──
            m = re.match(r"^[\*\-\+]\s+(.+)", line)
            if m:
                self.preview.insert(tk.END, "  \u2022  ")
                self._render_inline(m.group(1))
                self.preview.insert(tk.END, "\n")
                i += 1
                continue

            # ── ordered list ──
            m = re.match(r"^(\d+)\.\s+(.+)", line)
            if m:
                self.preview.insert(tk.END, f"  {m.group(1)}.  ")
                self._render_inline(m.group(2))
                self.preview.insert(tk.END, "\n")
                i += 1
                continue

            # ── table ──
            if line.startswith("|"):
                table_lines = []
                while i < n and lines[i].startswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                for tl in table_lines:
                    cells = [c.strip() for c in tl.split("|")[1:-1]]
                    row_text = " | ".join(cells)
                    if re.match(r"^[\|:\- ]+$", tl.strip().replace("|", "").strip()):
                        self.preview.insert(tk.END, f"  {row_text}  \n", "table_sep")
                    elif tl is table_lines[0]:
                        self.preview.insert(tk.END, f"  {row_text}  \n", "table_header")
                    else:
                        self.preview.insert(tk.END, f"  {row_text}  \n", "table")
                continue

            # ── footnote definition ──
            m = re.match(r"^\[\^(.+?)\]:\s*(.*)", line)
            if m:
                self.preview.insert(tk.END, f"[{m.group(1)}] ", "footnote_ref")
                self._render_inline(m.group(2), ("footnote_def",))
                self.preview.insert(tk.END, "\n")
                i += 1
                continue

            # ── paragraph (gather consecutive non-special lines) ──
            para = [line]
            i += 1
            while i < n:
                l = lines[i]
                if (not l.strip()
                    or re.match(r"^#{1,3}\s", l)
                    or re.match(r"^[-*_]{3,}\s*$", l.strip())
                    or l.startswith(">")
                    or re.match(r"^[\*\-\+]\s", l)
                    or re.match(r"^\d+\.\s", l)
                    or l.strip().startswith("```")
                    or l.startswith("|")):
                    break
                para.append(l)
                i += 1
            txt = " ".join(p.strip() for p in para if p.strip())
            self._render_inline(txt)
            self.preview.insert(tk.END, "\n\n")

        self.preview.config(state=tk.DISABLED)

    def _render_inline(self, text, extra_tags=()):
        et = tuple(extra_tags) if extra_tags else ()
        pattern = re.compile(
            r"\*\*\*(?P<bi>.+?)\*\*\*|"
            r"\*\*(?P<b>.+?)\*\*|"
            r"(?<!\*)\*(?!\*)(?P<i>.+?)(?<!\*)\*(?!\*)|"
            r"`(?P<code>.+?)`|"
            r"<u>(?P<u>.+?)</u>|"
            r"~~(?P<s>.+?)~~|"
            r"<ruby>(?P<kanji>.+?)<rt>(?P<reading>.+?)</rt></ruby>|"
            r"\[\^(?P<fn>.+?)\]|"
            r"\[(?P<lt>.+?)\]\((?P<lu>.+?)\)|"
            r"!\[(?P<ia>.+?)\]\((?P<is>.+?)\)"
        )

        last = 0
        for m in pattern.finditer(text):
            if m.start() > last:
                self.preview.insert(tk.END, text[last:m.start()], et)
            if m.group("bi"):
                self.preview.insert(tk.END, m.group("bi"), ("bold", "italic") + et)
            elif m.group("b"):
                self.preview.insert(tk.END, m.group("b"), ("bold",) + et)
            elif m.group("i"):
                self.preview.insert(tk.END, m.group("i"), ("italic",) + et)
            elif m.group("code"):
                self.preview.insert(tk.END, m.group("code"), ("code",) + et)
            elif m.group("u"):
                self.preview.insert(tk.END, m.group("u"), ("underline",) + et)
            elif m.group("s"):
                self.preview.insert(tk.END, m.group("s"), ("strikethrough",) + et)
            elif m.group("kanji"):
                self.preview.insert(tk.END, m.group("kanji"), et)
                self.preview.insert(tk.END, f"({m.group('reading')})", ("furigana",) + et)
            elif m.group("fn"):
                self.preview.insert(tk.END, f"[{m.group('fn')}]", ("footnote_ref",) + et)
            elif m.group("lt"):
                self.preview.insert(tk.END, m.group("lt"), ("link",) + et)
            elif m.group("ia"):
                self.preview.insert(tk.END, f"\u2500 Image: {m.group('ia')} \u2500\n",
                                    ("image",) + et)
            last = m.end()

        if last < len(text):
            self.preview.insert(tk.END, text[last:], et)


if __name__ == "__main__":
    root = tk.Tk()
    MarkdownEditor(root)
    root.mainloop()
