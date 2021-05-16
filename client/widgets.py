import tkinter as tk
from tkinter import ttk

class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._on_scrollbar_scroll)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind('<Enter>', self._focus_gained)
        self.canvas.bind('<Leave>', self._focus_lost)

        self.scrollbar.pack(side="right", fill="y")

    def _on_scrollbar_scroll(self, *args):
        command, n, *junk = args

        if command == "moveto":
            self.canvas.yview(command, n)
            return

        if int(n) < 0 and not self.scrollbar.get()[0]:
            return

        self.canvas.yview(command, n, "units")

    def _on_mousewheel(self, event):
        n = -1 if event.delta < 0 else 1
        self.canvas.yview_scroll(n, "units")

    def _scroll_down(self, event):
        if not self.scrollbar.get()[0]:
            return
        self.canvas.yview_scroll(-1, "units")

    def _scroll_up(self, event):
        self.canvas.yview_scroll(1, "units")

    def _focus_gained(self, event):
        self.canvas.bind_all("<Button-4>", self._scroll_down)
        self.canvas.bind_all("<Button-5>", self._scroll_up)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _focus_lost(self, event):
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
        self.canvas.unbind_all("<MouseWheel>")


class WrappingLabel(tk.Label):
    '''a type of Label that automatically adjusts the wrap to the size'''
    def __init__(self, master=None, **kwargs):
        tk.Label.__init__(self, master, **kwargs)
        self.bind('<Configure>', lambda e: self.config(wraplength=self.winfo_width()))
