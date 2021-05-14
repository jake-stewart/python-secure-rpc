from rpc_client import connect
import tkinter as tk
from tkinter import ttk

HOST = 'localhost'
PORT = 8080
POLLING_DELAY = 250

TITLE_TEXT = "Honours Study Evaluator"
SUBTITLE_TEXT = "Enter your unit codes and their marks, " + \
    "then click confirm to see if you are elegable for honours study."

class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

class WrappingLabel(tk.Label):
    '''a type of Label that automatically adjusts the wrap to the size'''
    def __init__(self, master=None, **kwargs):
        tk.Label.__init__(self, master, **kwargs)
        self.bind('<Configure>', lambda e: self.config(wraplength=self.winfo_width()))


class UnitsField(ScrollableFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.units = {}
        self.row_n = 1
        self.input_blocked = False
        self.max_units = 30
        self.construct()

    def construct(self):
        self.unit_heading = tk.Label(self.scrollable_frame, text="Unit Code", font="-weight bold")
        self.unit_heading.grid(sticky="W", pady=5, padx=5)

        self.grade_heading = tk.Label(self.scrollable_frame, text="Grade (out of 100)", font="-weight bold")
        self.grade_heading.grid(sticky="W", column=1, row=0, pady=5, padx=5)

        self.unit_input = tk.Entry(self.scrollable_frame)
        self.unit_input.focus()
        self.unit_input.grid(sticky="NSEW", padx=2, row=1)

        self.grade_input = tk.Entry(self.scrollable_frame)
        self.grade_input.grid(sticky="NSEW", padx=2, row=1, column=1)

        self.add_button = tk.Button(self.scrollable_frame, text="Add", command=self.on_click_unit_add)
        self.add_button.grid(sticky="W", row=1, column=2)

        self.error_message = tk.StringVar()
        self.error_label = tk.Label(self.scrollable_frame, textvariable=self.error_message, fg="red")
        self.error_label.grid(sticky="W", row=2, columnspan=3)

    def handle_errors(self, unit_code, grade):
        if not unit_code:
            self.error_message.set("Unit code cannot be blank.")
            return True

        if " " in unit_code or "\t" in unit_code:
            self.error_message.set("Unit code cannot contain spaces.")
            return True

        if unit_code in self.units:
            self.error_message.set("Unit code already exists.")
            return True

        if not grade:
            self.error_message.set("Grade cannot be blank.")
            return True

        try:
            grade = float(grade)
        except ValueError:
            self.error_message.set("Invalid input for grade.")
            return True

        if grade < 0:
            self.error_message.set("Grade cannot be less than 0.")
            return True

        if grade > 100:
            self.error_message.set("Grade cannot be greater than 100.")
            return True

    def on_click_unit_add(self):
        unit_code = self.unit_input.get().strip()
        grade = self.grade_input.get().strip()

        if self.handle_errors(unit_code, grade):
            return

        self.error_message.set("")
        self.add_unit(unit_code, grade)

    def allow_new_units(self):
        self.input_blocked = False
        self.unit_input.config(state="normal")
        self.unit_input.focus()
        self.grade_input.config(state="normal")
        self.add_button.config(state="normal")
        self.error_message.set("")

    def block_new_units(self):
        self.input_blocked = True
        self.focus()
        self.unit_input.config(state="disabled")
        self.grade_input.config(state="disabled")
        self.add_button.config(state="disabled")
        self.error_message.set("Reached maximum unit count.")

    def add_unit(self, unit_code, grade):
        grade = round(float(grade), 3)

        self.unit_input.grid_forget()
        self.grade_input.grid_forget()
        self.error_label.grid_forget()
        self.add_button.grid_forget()

        self.unit_input.delete(0, "end")
        self.grade_input.delete(0, "end")

        unit_code_label = tk.Label(self.scrollable_frame, text=unit_code)
        unit_code_label.grid(sticky="W", row=self.row_n, pady=0, padx=0)

        grade_label = tk.Label(self.scrollable_frame, text=str(grade))
        grade_label.grid(sticky="W", row=self.row_n, column=1, pady=0, padx=0)

        delete_button = tk.Button(
            self.scrollable_frame, text="Delete",
            command=lambda: self.delete_unit(unit_code)
        )
        delete_button.grid(sticky="W", row=self.row_n, column=2)

        self.row_n += 1
        self.unit_input.grid(row=self.row_n, sticky="NSEW", padx=2)
        self.unit_input.focus()
        self.grade_input.grid(row=self.row_n, sticky="NSEW", padx=2, column=1)
        self.add_button.grid(row=self.row_n, sticky="W", column=2)
        self.error_label.grid(row=self.row_n + 1, sticky="W", columnspan=3)

        self.units[unit_code] = [
            unit_code, grade, unit_code_label, grade_label, delete_button
        ]

        if len(self.units) >= self.max_units and not self.input_blocked:
            self.block_new_units()

    def delete_unit(self, unit_code):
        _, _, *widgets = self.units[unit_code]
        for widget in widgets:
            widget.grid_forget()
        del self.units[unit_code]

        if len(self.units) < self.max_units and self.input_blocked:
            self.allow_new_units()



class ClientApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.title = WrappingLabel(self, text=TITLE_TEXT, font="-size 25")
        self.title.pack(side="top", fill="x")

        self.subtitle = WrappingLabel(self, text=SUBTITLE_TEXT)
        self.subtitle.pack(side="top", fill="x")

        self.units_field = UnitsField(self, relief="ridge", borderwidth=1)
        self.units_field.pack(side="top", pady=10, fill="both", expand=True)

        # confirm_frame = tk.Frame()
        self.confirm_button = tk.Button(self, text="Confirm Units")
        self.confirm_button.pack(side=tk.BOTTOM)


if __name__ == "__main__":
    root = tk.Tk()
    client_app = ClientApplication(root)
    client_app.pack(fill="both", expand=True, pady=10, padx=10)
    root.resizable(width=False, height=True)
    root.minsize(450, 400)
    root.maxsize(450, 1000)
    root.mainloop()
