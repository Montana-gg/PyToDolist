import tkinter as tk
from tkinter import ttk
from datetime import datetime
import json
from pathlib import Path


class ModernToDoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do")
        self.root.geometry("480x720")
        self.root.minsize(400, 500)
        self.root.configure(bg="#1a1a1a")

        self.colors = {
            "bg": "#1a1a1a",
            "card_bg": "#242424",
            "card_hover": "#2e2e2e",
            "accent": "#3b82f6",
            "accent_hover": "#60a5fa",
            "text": "#f5f5f5",
            "text_secondary": "#a3a3a3",
            "success": "#22c55e",
            "danger": "#ef4444",
            "border": "#333333",
            "input_bg": "#1f1f1f",
            "scrollbar": "#404040"
        }

        self.tasks = []
        self.filter_mode = "all"
        self.data_file = Path.home() / ".modern_todo.json"
        self.radius = 12

        self.load_tasks()
        self.create_ui()
        self.render_tasks()
        self.center_window()

    def center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def create_rounded_rect(self, canvas, x1, y1, x2, y2, radius, fill, outline=""):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, fill=fill, outline=outline)

    def create_ui(self):
        main = tk.Frame(self.root, bg=self.colors["bg"])
        main.pack(fill="both", expand=True, padx=20, pady=20)

        header = tk.Frame(main, bg=self.colors["bg"])
        header.pack(fill="x", pady=(0, 20))

        title = tk.Label(header, text="To-Do", font=("Inter", 28, "bold"), bg=self.colors["bg"], fg=self.colors["text"])
        title.pack(anchor="w")

        subtitle = tk.Label(header, text="Оставайся продуктивным", font=("Inter", 12), bg=self.colors["bg"],
                            fg=self.colors["text_secondary"])
        subtitle.pack(anchor="w")

        self.counter_label = tk.Label(header, text="0 задач", font=("Inter", 12, "bold"), bg=self.colors["card_bg"],
                                      fg=self.colors["accent"], padx=14, pady=6)
        self.counter_label.pack(side="right")

        input_canvas = tk.Canvas(main, bg=self.colors["bg"], highlightthickness=0, height=70)
        input_canvas.pack(fill="x", pady=(0, 14))
        self.create_rounded_rect(input_canvas, 0, 0, 440, 70, self.radius, self.colors["card_bg"])

        input_inner = tk.Frame(input_canvas, bg=self.colors["card_bg"])
        input_inner.place(x=14, y=14, width=412, height=42)

        self.task_entry = tk.Entry(input_inner, font=("Inter", 13), bg=self.colors["input_bg"], fg=self.colors["text"],
                                   insertbackground=self.colors["accent"], relief="flat", highlightthickness=1,
                                   highlightcolor=self.colors["accent"], highlightbackground=self.colors["border"])
        self.task_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        self.task_entry.bind("<Return>", lambda e: self.add_task())

        add_btn_canvas = tk.Canvas(input_inner, bg=self.colors["card_bg"], highlightthickness=0, width=42, height=42)
        add_btn_canvas.pack(side="right")
        self.create_rounded_rect(add_btn_canvas, 0, 0, 42, 42, 8, self.colors["accent"])
        add_btn_canvas.create_text(21, 21, text="+", font=("Inter", 18, "bold"), fill="white")
        add_btn_canvas.bind("<Button-1>", lambda e: self.add_task())

        filters_canvas = tk.Canvas(main, bg=self.colors["bg"], highlightthickness=0, height=38)
        filters_canvas.pack(fill="x", pady=(0, 14))

        self.filter_buttons = {}
        filter_data = [("all", "Все"), ("active", "Активные"), ("completed", "Выполненные")]
        x_offset = 0
        for mode, text in filter_data:
            w = 90 if mode == "all" else 100
            btn_canvas = tk.Canvas(filters_canvas, bg=self.colors["bg"], highlightthickness=0, width=w, height=32)
            btn_canvas.place(x=x_offset, y=3)
            fill = self.colors["accent"] if mode == "all" else self.colors["card_bg"]
            tag = self.create_rounded_rect(btn_canvas, 0, 0, w, 32, 8, fill)
            btn_canvas.create_text(w // 2, 16, text=text, font=("Inter", 10),
                                   fill="white" if mode == "all" else self.colors["text_secondary"])
            btn_canvas.bind("<Button-1>", lambda e, m=mode: self.set_filter(m))
            self.filter_buttons[mode] = (btn_canvas, tag, w)
            x_offset += w + 8

        clear_canvas = tk.Canvas(filters_canvas, bg=self.colors["bg"], highlightthickness=0, width=90, height=32)
        clear_canvas.place(x=360, y=3)
        self.create_rounded_rect(clear_canvas, 0, 0, 90, 32, 8, self.colors["card_bg"])
        clear_canvas.create_text(45, 16, text="Очистить", font=("Inter", 10), fill=self.colors["danger"])
        clear_canvas.bind("<Button-1>", lambda e: self.clear_completed())

        list_container = tk.Frame(main, bg=self.colors["bg"])
        list_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(list_container, bg=self.colors["bg"], highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview,
                                      bg=self.colors["scrollbar"], troughcolor=self.colors["bg"], width=8,
                                      relief="flat")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.tasks_frame = tk.Frame(self.canvas, bg=self.colors["bg"])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.tasks_frame, anchor="nw", width=440)

        self.tasks_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # --- ИСПРАВЛЕННЫЙ БЛОК ПРИВЯЗКИ СКРОЛЛА ---
        # Привязываем скролл к самому холсту
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel_linux)
        self.canvas.bind("<Button-5>", self.on_mousewheel_linux)

        # ВАЖНО: Привязываем скролл к фрейму с задачами (те самые "красные зоны")
        self.tasks_frame.bind("<MouseWheel>", self.on_mousewheel)
        self.tasks_frame.bind("<Button-4>", self.on_mousewheel_linux)
        self.tasks_frame.bind("<Button-5>", self.on_mousewheel_linux)
        # ------------------------------------------

        bottom = tk.Frame(main, bg=self.colors["bg"])
        bottom.pack(fill="x", pady=(14, 0))

        self.percent_label = tk.Label(bottom, text="0%", font=("Inter", 10, "bold"), bg=self.colors["bg"],
                                      fg=self.colors["accent"])
        self.percent_label.pack(side="left")

        self.progress_canvas = tk.Canvas(bottom, width=100, height=4, bg=self.colors["card_bg"], highlightthickness=0,
                                         bd=0)
        self.progress_canvas.pack(side="right")
        self.progress_rect = self.progress_canvas.create_rectangle(0, 0, 0, 4, fill=self.colors["accent"], outline="")

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_linux(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(3, "units")

    def create_card(self, task):
        card_height = 64
        # 1. Создаем холст карточки
        card_canvas = tk.Canvas(self.tasks_frame, bg=self.colors["bg"], highlightthickness=0, height=card_height)
        card_canvas.pack(fill="x", pady=(0, 8))

        # 2. Рисуем фон
        card_tag = self.create_rounded_rect(card_canvas, 0, 0, 440, card_height, self.radius, self.colors["card_bg"])

        # 3. Чекбокс
        cb_size = 22
        cb_x, cb_y = 14, (card_height - cb_size) // 2
        if task["completed"]:
            self.create_rounded_rect(card_canvas, cb_x, cb_y, cb_x + cb_size, cb_y + cb_size, 4, self.colors["success"])
            card_canvas.create_text(cb_x + cb_size//2, cb_y + cb_size//2, text="✓", font=("Inter", 10, "bold"), fill="white")
        else:
            self.create_rounded_rect(card_canvas, cb_x, cb_y, cb_x + cb_size, cb_y + cb_size, 4, self.colors["card_bg"], self.colors["border"])

        # 4. Текст задачи и дата
        text_x = cb_x + cb_size + 12
        text_color = self.colors["text_secondary"] if task["completed"] else self.colors["text"]
        strike = "overstrike" if task["completed"] else ""
        card_canvas.create_text(text_x, 20, text=task["text"], font=("Inter", 12, strike), fill=text_color, anchor="w")
        card_canvas.create_text(text_x, 42, text=task.get("created_at", ""), font=("Inter", 9), fill=self.colors["text_secondary"], anchor="w")

        # 5. Кнопка удаления (крестик)
        del_text_id = card_canvas.create_text(420, card_height//2, text="✕", font=("Inter", 13), fill=self.colors["text_secondary"], anchor="e")
        # Создаем невидимую зону для клика
        del_hit = card_canvas.create_rectangle(390, 10, 430, 54, fill="", outline="", tags="del_zone")

        # --- ОБРАБОТКА СОБЫТИЙ ---

        # Единая функция для клика (проверяет, попали ли в крестик)
        def on_click(event):
            # Проверяем, есть ли под курсором тег зоны удаления
            item = card_canvas.find_closest(event.x, event.y)
            tags = card_canvas.gettags(item)
            if "del_zone" in tags:
                self.delete_task(task["id"])
            else:
                self.toggle_task(task["id"])

        # Привязываем клик и скролл к САМОМУ холсту (это не вызовет ошибку)
        card_canvas.bind("<Button-1>", on_click)
        card_canvas.bind("<MouseWheel>", self.on_mousewheel)
        card_canvas.bind("<Button-4>", self.on_mousewheel_linux)
        card_canvas.bind("<Button-5>", self.on_mousewheel_linux)

        # Эффекты наведения
        card_canvas.bind("<Enter>", lambda e: card_canvas.itemconfig(card_tag, fill=self.colors["card_hover"]))
        card_canvas.bind("<Leave>", lambda e: card_canvas.itemconfig(card_tag, fill=self.colors["card_bg"]))

    def set_filter(self, mode):
        self.filter_mode = mode
        self.render_tasks()

    def add_task(self):
        text = self.task_entry.get().strip()
        if not text: return
        self.tasks.insert(0, {"id": datetime.now().timestamp(), "text": text, "completed": False,
                              "created_at": datetime.now().strftime("%d.%m.%Y %H:%M")})
        self.task_entry.delete(0, "end")
        self.save_tasks()
        self.render_tasks()

    def toggle_task(self, task_id):
        for t in self.tasks:
            if t["id"] == task_id: t["completed"] = not t["completed"]
        self.save_tasks();
        self.render_tasks()

    def delete_task(self, task_id):
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save_tasks();
        self.render_tasks()

    def clear_completed(self):
        self.tasks = [t for t in self.tasks if not t["completed"]]
        self.save_tasks();
        self.render_tasks()

    def render_tasks(self):
        for w in self.tasks_frame.winfo_children(): w.destroy()
        filtered = [t for t in self.tasks if
                    (self.filter_mode == "all") or (self.filter_mode == "active" and not t["completed"]) or (
                                self.filter_mode == "completed" and t["completed"])]

        for task in filtered: self.create_card(task)

        # Обновление счетчиков
        total = len(self.tasks)
        comp = len([t for t in self.tasks if t["completed"]])
        self.counter_label.config(text=f"{total} задач")
        percent = int(comp / total * 100) if total > 0 else 0
        self.percent_label.config(text=f"{percent}%")
        self.progress_canvas.coords(self.progress_rect, 0, 0, percent, 4)

    def save_tasks(self):
        with open(self.data_file, "w", encoding="utf-8") as f: json.dump(self.tasks, f, ensure_ascii=False)

    def load_tasks(self):
        if self.data_file.exists():
            with open(self.data_file, "r", encoding="utf-8") as f: self.tasks = json.load(f)


if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    ModernToDoApp(root)
    root.mainloop()

