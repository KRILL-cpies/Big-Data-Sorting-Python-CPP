import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import threading
import time
import queue
import csv
CREATE_NO_WINDOW = 0x08000000

class SortApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Внешняя сортировка больших файлов. Видеоигры")
        self.root.geometry("1150x800")
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=5)
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

        self.queue = queue.Queue()
        self.is_working = False
        self.process = None
        
        self.current_data = [] 
        self.filtered_data = [] 
        self.page_size = 100
        self.current_page = 0
        
        self.sort_columns = {} 
        self.current_sort_col = None

        self.input_file = tk.StringVar(value="data.csv")
        self.output_file = tk.StringVar(value="sorted.txt")
        self.sort_key = tk.StringVar(value="rating") 
        self.lang = tk.StringVar(value="python")
        self.file_size_var = tk.StringVar(value="1.1")

        self.filter_entries = {}
        self.create_widgets()
        self.process_queue()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        top_container = ttk.Frame(self.root)
        top_container.pack(fill="x", padx=10, pady=5)
        
        gen_frame = ttk.LabelFrame(top_container, text="1. Генератор данных", padding=10)
        gen_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        top_container.grid_columnconfigure(0, weight=1)

        ttk.Label(gen_frame, text="Размер файла (ГБ):", font=("Arial", 10)).grid(row=0, column=0, padx=10, sticky="e")
        self.size_entry = ttk.Entry(gen_frame, textvariable=self.file_size_var, width=10, font=("Arial", 10))
        self.size_entry.grid(row=0, column=1, padx=5, sticky="w")
        
        self.btn_gen = ttk.Button(gen_frame, text="📁 Сгенерировать файл", command=self.run_generator, style="Accent.TButton")
        self.btn_gen.grid(row=0, column=2, padx=20)

        self.status_var = tk.StringVar(value="● Готов к работе")
        self.lbl_status = ttk.Label(gen_frame, textvariable=self.status_var, font=("Arial", 10, "bold"), foreground="green")
        self.lbl_status.grid(row=0, column=3, padx=20, sticky="e")
        self.progress = ttk.Progressbar(gen_frame, mode='indeterminate', length=150)
        self.progress.grid(row=0, column=4, padx=10, sticky="w")
        
        sort_frame = ttk.LabelFrame(top_container, text="2. Настройки сортировки", padding=10)
        sort_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        keys_config = [
            ("name", "📝 Название"), ("company", "🏢 Компания"), ("date", "📅 Дата"),
            ("genre", "🎮 Жанр"), ("playtime", "⏱️ Время"), ("rating", "⭐ Оценка")
        ]
        key_frame = ttk.Frame(sort_frame)
        key_frame.grid(row=0, column=0, sticky="w")
    
        for i, (key_val, key_label) in enumerate(keys_config):
            btn = ttk.Radiobutton(key_frame, text=key_label, variable=self.sort_key, value=key_val)
            btn.grid(row=i//3, column=i%3, sticky="w", padx=10, pady=3)

        lang_frame = ttk.LabelFrame(sort_frame, text="Ядро выполнения", padding=5)
        lang_frame.grid(row=0, column=1, padx=20, sticky="n")
        ttk.Radiobutton(lang_frame, text="🐍 Python", variable=self.lang, value="python").pack(anchor="w", padx=5)
        ttk.Radiobutton(lang_frame, text="⚡ C++", variable=self.lang, value="cpp").pack(anchor="w", padx=5)
        self.btn_sort = ttk.Button(sort_frame, text="🚀 ЗАПУСТИТЬ СОРТИРОВКУ", command=self.run_sorter)
        self.btn_sort.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
        self.btn_sort.config(style="Accent.TButton")

        view_frame = ttk.LabelFrame(self.root, text="3. Просмотр результата", padding=5)
        view_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        view_frame.grid_rowconfigure(1, weight=1)
        view_frame.grid_columnconfigure(0, weight=1)

        filter_frame = ttk.Frame(view_frame)
        filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        columns = ["name", "company", "date", "genre", "coop", "playtime", "rating"]
        headers = ["Название", "Компания", "Дата", "Жанр", "Кооп", "Время", "Оценка"]
        ttk.Label(filter_frame, text="🔍 Фильтры:", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        
        for col, head in zip(columns, headers):
            f_frame = ttk.Frame(filter_frame)
            f_frame.pack(side="left", padx=2)
            ttk.Label(f_frame, text=head, font=("Arial", 7)).pack(anchor="w")
            entry = ttk.Entry(f_frame, width=9)
            entry.pack()
            entry.bind("<KeyRelease>", lambda e, c=col: self.apply_filters())
            self.filter_entries[col] = entry

        ttk.Button(filter_frame, text="✖ Сброс", command=self.reset_filters).pack(side="left", padx=10, pady=(15,0))

        self.tree = ttk.Treeview(view_frame, columns=columns, show="headings", height=15)
        
        for col, head in zip(columns, headers):
            self.tree.heading(col, text=head, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=100, anchor="center")
        
        vsb = ttk.Scrollbar(view_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(view_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        
        page_frame = ttk.Frame(view_frame)
        page_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Label(page_frame, text="Строк на странице:").pack(side="left", padx=5)
        self.page_combo = ttk.Combobox(page_frame, values=[50, 100, 200, 500], width=5, state="readonly")
        self.page_combo.set(100)
        self.page_combo.bind("<<ComboboxSelected>>", lambda e: self.load_page(0))
        self.page_combo.pack(side="left", padx=5)

        ttk.Button(page_frame, text="|< Первая", command=lambda: self.load_page(0)).pack(side="left", padx=5)
        ttk.Button(page_frame, text="< Назад", command=self.prev_page).pack(side="left", padx=5)
        
        self.lbl_page_info = ttk.Label(page_frame, text="Стр. 1")
        self.lbl_page_info.pack(side="left", padx=10)
        
        ttk.Button(page_frame, text="Вперед >", command=self.next_page).pack(side="left", padx=5)
        ttk.Button(page_frame, text="Последняя >|", command=self.load_last_page).pack(side="left", padx=5)

        ttk.Button(page_frame, text="🔄 Обновить", command=lambda: self.load_file_data(reset=True)).pack(side="right", padx=10)

        self.log_text = tk.Text(self.root, height=3, bg="#f0f0f0", font=("Consolas", 9))
        self.log_text.pack(fill="x", padx=10, pady=(0, 10))

    def sort_by_column(self, col):
        if not self.filtered_data:
            return
        if self.current_sort_col == col:
            current_dir = self.sort_columns.get(col, 1)
            new_dir = -current_dir
        else:
            if col in ["date", "playtime", "rating"]:
                new_dir = -1
            else:
                new_dir = 1   
        
        self.sort_columns[col] = new_dir
        self.current_sort_col = col
        col_idx = ["name", "company", "date", "genre", "coop", "playtime", "rating"].index(col)
        
        def sort_key(row):
            val = row[col_idx]
            if col in ["playtime", "rating"]:
                try:
                    return float(val)
                except:
                    return 0
            elif col == "date":
                return val
            else:
                return val.lower() if isinstance(val, str) else val
        
        self.filtered_data.sort(key=sort_key, reverse=(new_dir == -1))
        self.update_header_indicators(col, new_dir)
        self.current_page = 0
        self.render_table()
        self.log(f"Сортировка таблицы: {col} {'(убывание)' if new_dir == -1 else '(возрастание)'}")

    def update_header_indicators(self, sorted_col, direction):
        columns = ["name", "company", "date", "genre", "coop", "playtime", "rating"]
        headers = ["Название", "Компания", "Дата", "Жанр", "Кооп", "Время", "Оценка"]
        
        for col, head in zip(columns, headers):
            if col == sorted_col:
                indicator = " ▲" if direction == 1 else " ▼"
                self.tree.heading(col, text=head + indicator)
            else:
                self.tree.heading(col, text=head)
    def reset_filters(self):
        for entry in self.filter_entries.values():
            entry.delete(0, tk.END)
        self.sort_columns = {}
        self.current_sort_col = None
        self.update_header_indicators(None, 0)
        self.apply_filters()
    def apply_filters(self):
        filters = {k: v.get().lower() for k, v in self.filter_entries.items() if v.get()}
        if not filters:
            self.filtered_data = self.current_data[:]
        else:
            self.filtered_data = []
            for row in self.current_data:
                match = True
                for col, val_filter in filters.items():
                    idx = ["name", "company", "date", "genre", "coop", "playtime", "rating"].index(col)
                    cell_val = str(row[idx]).lower()
                    if val_filter not in cell_val:
                        match = False
                        break
                if match:
                    self.filtered_data.append(row)
        if self.current_sort_col:
            col_idx = ["name", "company", "date", "genre", "coop", "playtime", "rating"].index(self.current_sort_col)
            direction = self.sort_columns.get(self.current_sort_col, 1)
            
            def sort_key(row):
                val = row[col_idx]
                if self.current_sort_col in ["playtime", "rating"]:
                    try:
                        return float(val)
                    except:
                        return 0
                elif self.current_sort_col == "date":
                    return val
                else:
                    return val.lower() if isinstance(val, str) else val
            
            self.filtered_data.sort(key=sort_key, reverse=(direction == -1))
        
        self.current_page = 0
        self.render_table()
    def load_file_data(self, reset=False):
        if not os.path.exists(self.output_file.get()):
            messagebox.showwarning("Внимание", "Файл sorted.txt еще не создан")
            return
        if reset:
            self.current_data = []
            self.current_page = 0
            self.sort_columns = {}
            self.current_sort_col = None
            self.update_header_indicators(None, 0)
            self.log("Чтение файла с диска...")
            threading.Thread(target=self._read_file_thread, daemon=True).start()
        else:
            self.render_table()
    def _read_file_thread(self):
        try:
            data = []
            with open(self.output_file.get(), "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None) 
                limit = 1000 
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    data.append(row) 
            self.queue.put(("DATA_LOADED", data))
        except Exception as e:
            self.queue.put(("LOG", f"Ошибка чтения: {e}"))
    def load_page(self, page_idx):
        self.current_page = page_idx
        self.render_table()
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_table()
    def next_page(self):
        max_pages = (len(self.filtered_data) - 1) // self.page_size
        if self.current_page < max_pages:
            self.current_page += 1
            self.render_table()
    def load_last_page(self):
        if self.filtered_data:
            max_pages = (len(self.filtered_data) - 1) // self.page_size
            self.current_page = max_pages
            self.render_table()
    def render_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)  
        try:
            self.page_size = int(self.page_combo.get())
        except:
            self.page_size = 100
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_data = self.filtered_data[start:end]
        for row in page_data:
            self.tree.insert("", "end", values=row)   
        total_pages = (len(self.filtered_data) - 1) // self.page_size + 1 if self.filtered_data else 0
        self.lbl_page_info.config(text=f"Стр. {self.current_page + 1} из {total_pages} (Всего строк: {len(self.filtered_data)})")
    def log(self, message):
        self.queue.put(("LOG", message))
    def update_status(self, message, stop_progress=False):
        self.queue.put(("STATUS", (message, stop_progress)))
    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                if msg_type == "STATUS":
                    text, stop = data
                    self.status_var.set(text)
                    if stop: 
                        self.progress.stop()
                        self.lbl_status.config(foreground="green")
                    else: 
                        self.progress.start(10)
                        self.lbl_status.config(foreground="blue")
                elif msg_type == "LOG":
                    self.log_text.insert(tk.END, data + "\n")
                    self.log_text.see(tk.END)
                elif msg_type == "DATA_LOADED":
                    self.current_data = data
                    self.apply_filters()
                    self.log(f"✅ Загружено строк: {len(data)}")
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)
    def on_closing(self):
        if self.is_working:
            if messagebox.askokcancel("Выход", "Процесс выполняется. Прервать?"):
                if self.process: self.process.terminate()
                self.root.destroy()
        else:
            self.root.destroy()
    def run_generator(self):
        if self.is_working: return
        try:
            size = float(self.file_size_var.get())
            if size <= 0: raise ValueError
        except:
            messagebox.showerror("Ошибка", "Введите корректный размер")
            return
        self.is_working = True
        self.btn_gen.config(state="disabled")
        self.btn_sort.config(state="disabled")
        self.update_status("⏳ Генерация...")
        self.lbl_status.config(foreground="orange")
        threading.Thread(target=self._generate_thread, args=(size,), daemon=True).start()
    def _generate_thread(self, size_gb):
        start = time.time()
        try:
            cmd = ["python", "generator.py", str(size_gb)]
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=CREATE_NO_WINDOW)
            for line in self.process.stdout:
                self.log(line.strip())
            self.process.wait()
            if self.process.returncode == 0:
                dur = time.time()-start
                self.update_status(f"✅ Готово за {dur:.1f}с")
                self.lbl_status.config(foreground="green")
            else:
                self.update_status("❌ Ошибка")
                self.lbl_status.config(foreground="red")
        except Exception as e:
            self.log(f"Ошибка: {e}")
            self.update_status("❌ Сбой")
            self.lbl_status.config(foreground="red")
        finally:
            self.is_working = False
            self.btn_gen.config(state="normal")
            self.btn_sort.config(state="normal")
            self.process = None
            self.progress.stop()
    def run_sorter(self):
        if self.is_working: return
        if not os.path.exists(self.input_file.get()):
            messagebox.showerror("Ошибка", "Файл data.csv не найден.")
            return
        self.is_working = True
        self.btn_sort.config(state="disabled")
        self.update_status("⏳ Сортировка...")
        self.lbl_status.config(foreground="orange")
        threading.Thread(target=self._sort_thread, daemon=True).start()
    def _sort_thread(self):
        start = time.time()
        try:
            lang = self.lang.get()
            cmd = []
            if lang == "python":
                cmd = ["python", "sort_py.py", self.input_file.get(), self.output_file.get(), self.sort_key.get()]
            elif lang == "cpp":
                exe_path = "sort_cpp.exe"
                if not os.path.exists(exe_path):
                    self.log("❌ sort_cpp.exe не найден.")
                    self.is_working = False; return
                cmd = [exe_path, self.input_file.get(), self.output_file.get(), self.sort_key.get()]
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=CREATE_NO_WINDOW)
            for line in self.process.stdout:
                self.log(line.strip())
            self.process.wait()
            if self.process.returncode == 0:
                dur = time.time()-start
                self.update_status(f"✅ Сортировка за {dur:.1f}с")
                self.lbl_status.config(foreground="green")
                self.load_file_data(reset=True)
            else:
                self.update_status("❌ Ошибка")
                self.lbl_status.config(foreground="red")
        except Exception as e:
            self.log(f"Исключение: {e}")
            self.update_status("❌ Сбой")
            self.lbl_status.config(foreground="red")
        finally:
            self.is_working = False
            self.btn_sort.config(state="normal")
            self.process = None
            self.progress.stop()
if __name__ == "__main__":
    root = tk.Tk()
    app = SortApp(root)
    root.mainloop()
