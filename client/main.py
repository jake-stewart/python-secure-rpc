from rpc.client import connect
import threading
import tkinter as tk
from tkinter import font
from tkinter import messagebox
from tkinter import ttk
from widgets import ScrollableFrame, WrappingLabel

HOST = 'localhost'
PORT = 8080
POLLING_DELAY = 250

TITLE_TEXT = "Honours Study Evaluator"
SUBTITLE_TEXT = "Enter your unit codes and their marks, then click confirm."

class EvaluationPrompt:
    def __init__(self, parent, username, average, top_12_average, evaluation):
        self.parent = parent

        self.top = tk.Toplevel(parent)
        self.top.protocol("WM_DELETE_WINDOW", self.on_close)
        self.top.resizable(False, False)
        self.top.title("Evaluation")

        root_frame = tk.Frame(self.top)

        frame = tk.Frame(root_frame)
        bold_font = font.Font(font='TkDefaultFont')
        bold_font.config(weight="bold")

        tk.Label(frame, text="Username:", font=bold_font).pack(side="left", pady=5)
        tk.Label(frame, text=username).pack(side="left")
        frame.pack(side="top", anchor="w")

        frame = tk.Frame(root_frame)
        tk.Label(frame, text="Average Result:", font=bold_font).pack(side="left")
        tk.Label(frame, text=str(round(average, 2))).pack(side="left")
        frame.pack(side="top", anchor="w")

        frame = tk.Frame(root_frame)
        tk.Label(frame, text="Average Result (top 12 units):", font=bold_font).pack(side="left", pady=5)
        tk.Label(frame, text=str(round(top_12_average, 2))).pack(side="left")
        frame.pack(side="top", anchor="w")

        tk.Label(root_frame, text="Evaluation:", font=bold_font).pack(side="top", anchor="w")
        for line in evaluation.split("\n"):
            tk.Label(root_frame, text=line).pack(side="top", anchor="w")

        frame = tk.Frame(root_frame)
        tk.Button(frame, text="Ok", command=self.on_close).pack(side="left", pady=5)
        frame.pack(side="top", anchor="w")

        root_frame.pack(side="left", pady=0, padx=5)

    def on_close(self):
        self.top.destroy()
        self.parent.unblock_input()


class LoginPrompt:
    def __init__(self, parent, username_prompt="Username", password_prompt="Password", show="•"):
        self.parent = parent

        self.top = tk.Toplevel(parent)
        self.top.protocol("WM_DELETE_WINDOW", self.on_close)
        self.top.resizable(False, False)
        self.top.title("Log in")

        self.username_label = tk.Label(self.top, text=username_prompt)
        self.username_label.grid(row=0, column=0, pady=5, sticky="e")

        self.username = tk.StringVar()
        self.username_input = tk.Entry(self.top, textvariable=self.username)
        self.username_input.grid(row=0, column=1, pady=5)
        self.username_input.bind("<Return>", lambda e: self.login())

        self.password_label = tk.Label(self.top, text=password_prompt)
        self.password_label.grid(row=1, column=0, pady=5, sticky="e")

        self.password = tk.StringVar()
        self.password_input = tk.Entry(self.top, textvariable=self.password, show=show)
        self.password_input.grid(row=1, column=1, pady=0, padx=5)
        self.password_input.bind("<Return>", lambda e: self.login())

        self.error_message = tk.StringVar()
        self.error_label = tk.Label(self.top, textvariable=self.error_message, fg="red")
        self.error_label.grid(row=2, column=0, columnspan=2, pady=0, padx=5, sticky="W")

        self.login_button = tk.Button(self.top, text="Log in", command=self.login)
        self.login_button.grid(row=3, column=0, pady=5, padx=5)

        self.username_input.focus()

    def login(self):
        self.login_button.configure(state="disabled")
        self.parent.set_credentials(self.username.get(), self.password.get())

    def incorrect_credentials(self):
        self.error_message.set("Invalid username or password.")
        self.login_button.configure(state="normal")

    def close(self):
        self.top.destroy()

    def on_close(self):
        pass


class ResultsField(ScrollableFrame):
    def __init__(self, parent, max_results, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.records = {}
        self.row_n = 1
        self.input_blocked = False
        self.max_records = max_results
        self.construct()

    def construct(self):
        self.unit_heading = tk.Label(self.scrollable_frame, text="Unit Code", font="-weight bold")
        self.unit_heading.grid(sticky="W", pady=5)

        self.result_heading = tk.Label(self.scrollable_frame, text="Result (out of 100)", font="-weight bold")
        self.result_heading.grid(sticky="W", column=1, row=0, pady=5)

        self.unit_input = ttk.Entry(self.scrollable_frame)
        self.unit_input.focus()
        self.unit_input.grid(sticky="NSEW", padx=2, row=1)

        self.result_input = ttk.Entry(self.scrollable_frame)
        self.result_input.grid(sticky="NSEW", padx=2, row=1, column=1)

        self.unit_input.bind("<Return>", lambda e: self.result_input.focus())
        self.result_input.bind("<Return>", lambda e: self.on_record_add())

        self.add_button = ttk.Button(self.scrollable_frame, text="Add", command=self.on_record_add)
        self.add_button.grid(sticky="W", row=1, column=2)

        self.error_message = tk.StringVar()
        self.error_label = tk.Label(self.scrollable_frame, textvariable=self.error_message, fg="red")
        self.error_label.grid(sticky="W", row=2, columnspan=3)

    def set(self, results):
        self.error_message.set("")
        for _, _, *widgets in self.records.values():
            for widget in widgets:
                widget.grid_forget()
                widget.destroy()

        self.records = {}
        for unit_code, result in results:
            self.add_record(unit_code, result)


    def get(self):
        return [(record[0], record[1]) for record in self.records.values()]

    def handle_errors(self, unit_code, result):
        if not unit_code:
            self.error_message.set("Unit code cannot be blank.")
            return True

        if " " in unit_code or "\t" in unit_code:
            self.error_message.set("Unit code cannot contain spaces.")
            return True

        if not result:
            self.error_message.set("Result cannot be blank.")
            return True

        try:
            result = float(result)
        except ValueError:
            self.error_message.set("Invalid input for result.")
            return True

        if result < 0:
            self.error_message.set("Result cannot be less than 0.")
            return True

        if result > 100:
            self.error_message.set("Result cannot be greater than 100.")
            return True

        n_fails = 0
        passed = False
        for record in self.records.values():
            if record[0] != unit_code:
                continue
            if record[1] >= 50:
                passed = True
                break
            else:
                n_fails += 1

        if passed:
            self.error_message.set("This unit already been passed.")
            return True

        if n_fails >= 2 and result < 50:
            self.error_message.set("A unit cannot be failed more than twice.")
            return True

    def on_record_add(self):
        unit_code = self.unit_input.get().strip()
        result = self.result_input.get().strip()

        if self.handle_errors(unit_code, result):
            return

        self.error_message.set("")
        self.add_record(unit_code, result)

    def allow_new_records(self):
        if len(self.records) < self.max_records and self.input_blocked:
            self.input_blocked = False
            self.unit_input.config(state="normal")
            self.unit_input.focus()
            self.result_input.config(state="normal")
            self.add_button.config(state="normal")
            self.error_message.set("")

    def block_new_units(self, reached_max=True):
        self.input_blocked = True
        self.focus()
        self.unit_input.config(state="disabled")
        self.result_input.config(state="disabled")
        self.add_button.config(state="disabled")
        if reached_max:
            self.error_message.set("Reached maximum unit count.")

    def block_deletes(self):
        for _, _, _, _, delete_button in self.records.values():
            delete_button.configure(state="disabled")

    def allow_deletes(self):
        for _, _, _, _, delete_button in self.records.values():
            delete_button.configure(state="normal")

    def add_record(self, unit_code, result):
        result = round(float(result), 3)

        self.unit_input.grid_forget()
        self.result_input.grid_forget()
        self.error_label.grid_forget()
        self.add_button.grid_forget()

        self.unit_input.delete(0, "end")
        self.result_input.delete(0, "end")

        unit_code_label = tk.Label(
            self.scrollable_frame, text=unit_code
        )
        unit_code_label.grid(
            sticky="W", row=self.row_n, pady=0, padx=0
        )

        result_label = tk.Label(
            self.scrollable_frame, text=str(result)
        )
        result_label.grid(
            sticky="W", row=self.row_n, column=1, pady=0, padx=0
        )

        identifier = self.row_n
        delete_button = ttk.Button(
            self.scrollable_frame, text="Delete",
            command=lambda: self.delete_record(identifier)
        )
        delete_button.grid(sticky="W", row=self.row_n, column=2)

        self.row_n += 1
        self.unit_input.grid(row=self.row_n, sticky="NSEW", padx=2)
        self.unit_input.focus()
        self.result_input.grid(row=self.row_n, sticky="NSEW", padx=2, column=1)
        self.add_button.grid(row=self.row_n, sticky="W", column=2)
        self.error_label.grid(row=self.row_n + 1, sticky="W", columnspan=3)

        self.records[identifier] = (
            unit_code, result, unit_code_label, result_label, delete_button
        )

        if len(self.records) >= self.max_records and not self.input_blocked:
            self.block_new_records()

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1)

    def delete_record(self, identifier):
        _, _, *widgets = self.records[identifier]
        for widget in widgets:
            widget.grid_forget()
            widget.destroy()
        del self.records[identifier]
        self.error_message.set("")
        self.allow_new_records()



class ClientApplication(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)

        self.min_results = 12
        self.max_results = 30

        self.parent = parent
        self.login_prompt = None
        self.thread_running = False

        self.title = tk.Label(self, text=TITLE_TEXT, font="-size 25")
        self.title.pack(side="top", fill="x")

        self.subtitle = WrappingLabel(self, text=SUBTITLE_TEXT)
        self.subtitle.pack(side="top", fill="x")

        self.results_field = ResultsField(
            self, self.max_results, borderwidth=1,
            relief="solid", width=0, height=200
        )
        self.results_field.pack(
            side="top", pady=10, fill="both", expand=True
        )

        button_frame = ttk.Frame(self)

        self.confirm_button = ttk.Button(
            button_frame, text="Confirm Results", command=self.confirm_results
        )
        self.confirm_button.pack(side="right")

        self.download_button = ttk.Button(
            button_frame, text="Download Results", command=self.download_results
        )
        self.download_button.pack(side="left", anchor="w")

        self.upload_button = ttk.Button(
            button_frame, text="Upload Results", command=self.upload_results
        )
        self.upload_button.pack(side="left", anchor="w", padx=10)

        button_frame.pack(side="bottom", fill="x")

        self.block_input()
        self.start_connect_thread()

    def block_input(self):
        self.upload_button.config(state="disabled")
        self.download_button.config(state="disabled")
        self.results_field.block_new_units(reached_max=False)
        self.results_field.block_deletes()
        self.confirm_button.config(state="disabled")

    def unblock_input(self):
        self.results_field.allow_new_records()
        self.results_field.allow_deletes()
        self.confirm_button.config(state="normal")
        self.upload_button.config(state="normal")
        self.download_button.config(state="normal")

    def download_results(self):
        self.block_input()
        self.send_request(
            "get_results",
            self.on_downloaded_results,
            self.token
        )

    def on_downloaded_results(self):
        results = self.response
        if results:
            self.results_field.set(results)
            messagebox.showinfo(
                "Download Successful",
                "Your results have been downloaded and updated successfully."
            )
        else:
            messagebox.showerror(
                "Download Error",
                "No results contained in the database."
            )

        self.unblock_input()

    def upload_results(self):
        self.block_input()
        results = self.results_field.get()

        if not results:
            messagebox.showerror(
                "Upload Error",
                "You have no results to upload."
            )
            self.unblock_input()
            return

        self.send_request(
            "set_results",
            self.on_uploaded_results,
            self.token, results
        )

    def on_uploaded_results(self):
        messagebox.showinfo(
            "Upload Successful",
            "Your results are saved online for future use."
        )
        self.unblock_input()

    def confirm_results(self):
        if self.thread_running:
            return

        self.block_input()
        results = self.results_field.get()
        if len(results) < self.min_results:
            messagebox.showerror(
                "Insufficient Results",
                "Enter at least " + str(self.min_results) + \
                " results before checking eligibility."
            )
            self.unblock_input()
            return

        self.send_request(
            "evaluate_eligibility",
            self.eligibility_reply,
            self.token, results
        )

    def eligibility_reply(self):
        EvaluationPrompt(self, *self.response)

    def start_connect_thread(self):
        if self.thread_running:
            return
        self.thread_running = True
        self.handler = self.check_connection
        thread = threading.Thread(target=self.connect)
        self.after(POLLING_DELAY, self.check_thread_status)
        thread.start()

    def connect(self):
        try:
            self.conn = connect(HOST, PORT)
            self.connected = True
        except:
            self.connected = False
        self.thread_running = False

    def check_connection(self):
        if self.connected:
            self.login()
        else:
            if not messagebox.askretrycancel("Connection Error", "Cannot connect to server."):
                exit()
            else:
                self.start_connect_thread()

    def set_credentials(self, username, password):
        self.credentials = (username, password)
        self.send_request(
            "log_in",
            self.check_credentials_response,
            *self.credentials
        )

    def check_credentials_response(self):
        self.token = self.response
        if self.token:
            self.login_prompt.close()
            self.login_prompt = None
            self.unblock_input()
        else:
            self.login_prompt.incorrect_credentials()

    def login(self):
        self.login_prompt = LoginPrompt(self)

    def send_request(self, target, handler, *args, **kwargs):
        if self.thread_running:
            return
        self.thread_running = True
        self.handler = handler
        thread = threading.Thread(target=self.request_thread, args=(target, args, kwargs))
        self.after(POLLING_DELAY, self.check_thread_status)
        thread.start()

    def request_thread(self, target, args, kwargs):
        try:
            rp = self.conn.__getattr__(target)
            self.response = rp(*args, **kwargs)
            self.thread_running = False
        except ConnectionRefusedError:
            self.connected = False
            self.thread_running = False
        # except:
        #     messagebox.showerror(
        #         "Critical Error",
        #         "This error should be reported immediately."
        #     )
        #     exit(1)

    def check_thread_status(self):
        if self.thread_running:
            self.after(POLLING_DELAY, self.check_thread_status)
        elif not self.connected:
            if self.login_prompt:
                self.login_prompt.close()
                self.login_prompt = None
            self.check_connection()
        else:
            self.handler()



if __name__ == "__main__":
    import os

    root = tk.Tk()

    # use windows theme if on windows
    if os.name == "nt":
        style = ttk.Style(root)
        style.theme_use("xpnative")

    client_app = ClientApplication(root)
    client_app.pack(fill="both", expand=True, pady=10, padx=10)

    root.update()
    root.minsize(root.winfo_width(), root.winfo_height())
    root.resizable(False, True)

    print("HINT:")
    print("username: 'testuser'")
    print("password: 'testpassword'")

    root.mainloop()
