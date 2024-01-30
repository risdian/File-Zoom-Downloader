import tkinter as tk
from gui.login_page import LoginPage
from gui.schedule_page import SchedulePage
from db.database import init_db
from core.zoom_auth import is_access_token_valid

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("My Schedule App")

        init_db()

        self.login_page = LoginPage(self, self)
        self.schedule_page = SchedulePage(self, self)

        if is_access_token_valid():
            self.show_schedule_page()
        else:
            self.show_login_page()

    def show_login_page(self):
        self.schedule_page.pack_forget()
        self.login_page.pack()

    def show_schedule_page(self):
        self.login_page.pack_forget()
        self.schedule_page.pack()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()