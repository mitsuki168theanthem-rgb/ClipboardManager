import customtkinter as ctk
import tkinter as tk
from data_handler import DataHandler
import ctypes

# Configuration
FONT_FAMILY = "Yu Gothic UI"
FONT_SIZE_NORMAL = 14
FONT_SIZE_LARGE = 16

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self, on_paste_callback, on_edit_callback=None, data_handler=None):
        super().__init__()
        self.title("Paste Template")
        self.geometry("600x400")
        self.center_window()
        self.on_paste_callback = on_paste_callback
        self.on_edit_callback = on_edit_callback
        self.data_handler = data_handler or DataHandler()
        self.templates = []
        self.item_widgets = [] # Track widgets for safe removal
        
        self.create_widgets()
        self.refresh_list()
        
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def create_widgets(self):
        # Font settings
        self.main_font = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)
        
        # Search Bar
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_list)
        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search...", textvariable=self.search_var, font=self.main_font)
        self.search_entry.pack(fill="x", padx=10, pady=10)
        self.search_entry.bind("<Return>", self.on_enter_pressed)

        # Scrollable Frame for List
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def refresh_list(self):
        try:
            raw_data = self.data_handler.load_data()
            # Sort by Category then Title
            self.templates = sorted(raw_data, key=lambda x: (x.get('category', 'ZZZ'), x.get('title', '')))
            self.update_view(self.templates)
        except Exception as e:
            print(f"Error refreshing list: {e}")

    def update_view(self, items, query=""):
        try:
            # Safely clear: Only destroy widgets we created
            for w in self.item_widgets:
                try:
                    w.destroy()
                except:
                    pass
            self.item_widgets = []

            for idx, item in enumerate(items):
                # Container for each item
                frame = ctk.CTkFrame(self.scroll_frame)
                frame.pack(fill="x", pady=2)
                self.item_widgets.append(frame)
                
                # Header Frame (Title + Buttons)
                header_frame = ctk.CTkFrame(frame, fg_color="transparent")
                header_frame.pack(fill="x")

                # Delete Button (Right)
                del_btn = ctk.CTkButton(
                    header_frame, text="🗑️", width=30, fg_color="transparent", hover_color=("gray70", "gray30"), text_color=("gray10", "gray90"),
                    font=self.main_font,
                    command=lambda tid=item.get('id'): self.delete_item(tid)
                )
                del_btn.pack(side="right", padx=2)

                # Edit Button (Right)
                edit_btn = ctk.CTkButton(
                    header_frame, text="✏️", width=30, fg_color="transparent", hover_color=("gray70", "gray30"), text_color=("gray10", "gray90"),
                    font=self.main_font,
                    command=lambda i=item: self.edit_item(i)
                )
                edit_btn.pack(side="right", padx=2)

                # Title (Left, fills remaining)
                btn = ctk.CTkButton(
                    header_frame, 
                    text=f"{item.get('title')} ({item.get('category', 'General')})", 
                    anchor="w",
                    fg_color="transparent",
                    text_color=("gray10", "gray90"),
                    hover_color=("gray70", "gray30"),
                    font=self.main_font,
                    command=lambda text=item.get('content'): self.on_select(text)
                )
                btn.pack(fill="x", side="left", expand=True)
                
                # Search Highlight Snippet
                content = item.get('content', '')
                if query and query in content.lower():
                    try:
                        # Find match
                        lower_content = content.lower()
                        start_idx = lower_content.find(query)
                        
                        # Extract snippet (e.g. 15 chars before/after)
                        snip_start = max(0, start_idx - 15)
                        snip_end = min(len(content), start_idx + len(query) + 15)
                        
                        prefix = "..." if snip_start > 0 else ""
                        suffix = "..." if snip_end < len(content) else ""
                        snippet_text = f"└ {prefix}{content[snip_start:snip_end]}{suffix}"
                        
                        # Create minimal textbox for highlight
                        # Check height needed? 1 line usually ~20-30px
                        snippet_box = ctk.CTkTextbox(
                            frame, 
                            height=25, 
                            fg_color="transparent", 
                            text_color="gray",
                            font=self.main_font, 
                            activate_scrollbars=False
                        )
                        snippet_box.pack(fill="x", padx=(40, 0), pady=(0, 2)) # Increased indent
                        
                        snippet_box.insert("1.0", snippet_text)
                        
                        # Highlight
                        # Calculate position in snippet_text
                        # "└ ..." length depends on prefix
                        match_pos_in_snippet = len(f"└ {prefix}") + (start_idx - snip_start)
                        
                        tag_start = f"1.{match_pos_in_snippet}"
                        tag_end = f"1.{match_pos_in_snippet + len(query)}"
                        
                        snippet_box.tag_config("highlight", background="yellow", foreground="black")
                        snippet_box.tag_add("highlight", tag_start, tag_end)
                        
                        snippet_box.configure(state="disabled")
                    except Exception as e:
                        print(f"Snippet error: {e}")

        except Exception as e:
            print(f"Error updating view: {e}")

    def delete_item(self, item_id):
        self.data_handler.delete_template(item_id)
        self.refresh_list()

    def edit_item(self, item):
        if hasattr(self, 'on_edit_callback') and self.on_edit_callback:
            self.on_edit_callback(item)

    def filter_list(self, *args):
        query = self.search_var.get().lower()
        if not query:
            self.update_view(self.templates)
            return

        filtered = [
            t for t in self.templates 
            if query in t.get('title', '').lower() or query in t.get('content', '').lower() or query in t.get('category', '').lower()
        ]
        self.update_view(filtered, query=query)

    def on_select(self, text):
        self.withdraw() # Hide immediately
        if self.on_paste_callback:
            self.on_paste_callback(text)

    def on_enter_pressed(self, event):
        query = self.search_var.get().lower()
        if not query:
            filtered = self.templates
        else:
            filtered = [
                t for t in self.templates 
                if query in t.get('title', '').lower() or query in t.get('content', '').lower() or query in t.get('category', '').lower()
            ]
        
        if filtered:
            self.on_select(filtered[0]['content'])

    def reset_and_show(self):
        print("Resetting and showing MainWindow...")
        self.search_var.set("") # Clear search
        self.refresh_list()
        self.deiconify()
        
        # Robust 'Front' logic for Main Window
        try:
            self.attributes('-topmost', True)
            self.lift()
            self.focus_force()
            self.search_entry.focus()
            # Turn off topmost after 200ms
            self.after(200, lambda: self.attributes('-topmost', False))
        except Exception as e:
            print(f"Focus error: {e}")

        self.search_entry.focus()
        
        # Try to enable IME
        self.after(100, lambda: self.enable_ime(self.search_entry.winfo_id()))
        
        print("MainWindow shown.")

    def enable_ime(self, hwnd):
        try:
            imm32 = ctypes.windll.imm32
            hIMC = imm32.ImmGetContext(hwnd)
            if hIMC:
                imm32.ImmSetOpenStatus(hIMC, True)
                imm32.ImmReleaseContext(hwnd, hIMC)
        except Exception as e:
            print(f"IME Error: {e}")

class SaveWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback=None, on_cancel_callback=None):
        super().__init__(parent)
        self.title("Save Template")
        self.geometry("500x500")
        self.center_window()
        self.on_save_callback = on_save_callback
        self.on_cancel_callback = on_cancel_callback
        self.data_handler = DataHandler()
        
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')

    def create_widgets(self):
        # Font settings
        self.main_font = ctk.CTkFont(family=FONT_FAMILY, size=FONT_SIZE_NORMAL)

        # Title
        ctk.CTkLabel(self, text="Title", font=self.main_font).pack(anchor="w", padx=10, pady=(10, 0))
        self.title_entry = ctk.CTkEntry(self, placeholder_text="Template Name", font=self.main_font)
        self.title_entry.pack(fill="x", padx=10, pady=5)
        
        # Store default border color for reset
        self.default_border_color = self.title_entry.cget("border_color")
        # Bind key event to reset border on typing
        self.title_entry.bind("<Key>", lambda e: self.title_entry.configure(border_color=self.default_border_color))

        # Category
        ctk.CTkLabel(self, text="Category", font=self.main_font).pack(anchor="w", padx=10)
        self.category_combobox = ctk.CTkComboBox(self, values=["General"], font=self.main_font, dropdown_font=self.main_font)
        self.category_combobox.pack(fill="x", padx=10, pady=5)

        # Content
        ctk.CTkLabel(self, text="Content", font=self.main_font).pack(anchor="w", padx=10)
        self.content_text = ctk.CTkTextbox(self, height=200, font=self.main_font)
        self.content_text.pack(fill="both", expand=True, padx=10, pady=5)

        # Buttons
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_frame, text="Cancel", fg_color="gray", command=self.cancel, font=self.main_font).pack(side="right", padx=5)
        # Assuming 'Save' implies create or update depending on state
        ctk.CTkButton(btn_frame, text="Save", command=self.save_template, font=self.main_font).pack(side="right", padx=5)

    def cancel(self):
        if self.on_cancel_callback:
            try:
                self.on_cancel_callback()
            except Exception as e:
                print(f"Cancel callback failed: {e}")
        self.withdraw()

    def reset_and_show(self, content, template_id=None, title="", category="General"):
        self.template_id = template_id # Store ID if editing
        
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, title)
        # Reset border color
        self.title_entry.configure(border_color=self.default_border_color)
        
        # Update categories
        current_cats = self.data_handler.get_categories()
        options = ["General"] 
        for c in current_cats:
            if c not in options:
                options.append(c)
        
        self.category_combobox.configure(values=options)
        self.category_combobox.set(category if category else "General")

        self.content_text.delete("1.0", "end")
        self.content_text.insert("1.0", content)
        
        self.deiconify()
        
        # Robust 'Front' logic
        try:
            self.attributes('-topmost', True)
            self.lift()
            self.focus_force()
            self.title_entry.focus()
            # Turn off topmost after 200ms
            self.after(200, lambda: self.attributes('-topmost', False))
            
            # Try IME enable
            self.after(200, lambda: self.enable_ime(self.title_entry.winfo_id()))
        except Exception as e:
            print(f"Focus error: {e}")
            
        self.center_window()

    def enable_ime(self, hwnd):
        try:
            imm32 = ctypes.windll.imm32
            hIMC = imm32.ImmGetContext(hwnd)
            if hIMC:
                imm32.ImmSetOpenStatus(hIMC, True)
                imm32.ImmReleaseContext(hwnd, hIMC)
        except Exception as e:
            print(f"IME Error: {e}")

    def save_template(self):
        title = self.title_entry.get()
        
        raw_cat = self.category_combobox.get()
        category = raw_cat or "General"

        content = self.content_text.get("1.0", "end-1c")

        if not title:
            # Highlight title entry with red border
            self.title_entry.configure(border_color="red")
            self.title_entry.focus()
            return

        print(f"Saving/Updating template: {title} ({category})")
        try:
            if hasattr(self, 'template_id') and self.template_id:
                self.data_handler.update_template(self.template_id, title, content, category)
            else:
                self.data_handler.add_template(title, content, category)
        except Exception as e:
            print(f"FAILED to save to file: {e}")
        
        if self.on_save_callback:
            try:
                self.on_save_callback()
            except Exception as e:
                print(f"Callback failed: {e}")

        self.withdraw()
