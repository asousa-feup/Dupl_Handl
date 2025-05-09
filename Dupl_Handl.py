import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import filecmp
import time
import datetime
import json
import shutil
import fnmatch

class DirectoryComparisonTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Directory Comparison Tool")
        self.root.geometry("1200x600")



        # Create status bar
        style = ttk.Style()
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure status bar style
        style.configure("Status.TLabel", font=('Default', 12, 'bold'))
        self.status_bar.configure(style="Status.TLabel")
        
        # Set initial message
        self.status_var.set("Select Dirs and press 'Compare' -- (C) Armando Sousa 2025 -- Free software, use at your own risk!")
        
        # Timer for clearing status messages
        self.status_timer = None





        # Load last used directories
        self.settings_file_path = os.path.dirname(os.path.abspath(__file__))+"\settings.json"
        print(self.settings_file_path)
        self.last_dirs = self.load_settings()
        
        # Create tooltip storage
        self.tooltips = {}
        
        # Create context menu
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Open", command=self.open_selected_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete This Column", command=lambda: self.delete_file_LRB("this"))
        self.context_menu.add_command(label="Delete Left", command=lambda: self.delete_file_LRB("left"))
        self.context_menu.add_command(label="Delete Right", command=lambda: self.delete_file_LRB("right"))
        self.context_menu.add_command(label="Delete Both", command=lambda: self.delete_file_LRB("both"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Explorer Left", command=lambda: self.reveal("left"))
        self.context_menu.add_command(label="Explorer Right", command=lambda: self.reveal("right"))
        self.context_menu.add_command(label="Explorer Both", command=lambda: self.reveal("both"))

        # Directory selection frame
        dir_frame = ttk.Frame(root, padding="10")
        dir_frame.pack(fill=tk.X)
        
        # Left directory
        ttk.Label(dir_frame, text="Left Directory:").grid(column=0, row=0, sticky=tk.W)
        self.left_dir_var = tk.StringVar(value=self.last_dirs.get("left", ""))
        ttk.Entry(dir_frame, textvariable=self.left_dir_var, width=100).grid(column=1, row=0, padx=5, sticky=tk.W)
        ttk.Button(dir_frame, text="Browse", command=self.browse_left_dir).grid(column=2, row=0, padx=5)
        # Special Delete Left Dir Button
        ttk.Button(dir_frame, text="! Delete Dir !", command=self.delete_left_dir).grid(column=4, row=0, padx=5)
                
        # Right directory
        ttk.Label(dir_frame, text="Right Directory:").grid(column=0, row=1, sticky=tk.W, pady=5)
        self.right_dir_var = tk.StringVar(value=self.last_dirs.get("right", ""))
        ttk.Entry(dir_frame, textvariable=self.right_dir_var, width=100).grid(column=1, row=1, padx=5, sticky=tk.W, pady=5)
        ttk.Button(dir_frame, text="Browse", command=self.browse_right_dir).grid(column=2, row=1, padx=5, pady=5)
        
        # Include subdirectories checkbox and file filter in the same row
        self.include_subdirs = tk.BooleanVar(value=self.last_dirs.get("include_subdirs", False))
        ttk.Checkbutton(dir_frame, text="Include Subdirectories", variable=self.include_subdirs).grid(column=1, row=2, sticky=tk.W)

        # Show equal files
        self.show_equal_files = tk.BooleanVar(value=self.last_dirs.get("show_equal_files", False))
        ttk.Checkbutton(dir_frame, text="Show Equal Files", variable=self.show_equal_files).grid(column=5, row=1, sticky=tk.W)

        # Long Win filenames
        self.long_win_fnames = tk.BooleanVar(value=self.last_dirs.get("long_win_fnames", False))
        ttk.Checkbutton(dir_frame, text="Long Win FNames", variable=self.long_win_fnames).grid(column=3, row=1, sticky=tk.W)


        # File filter
        ttk.Label(dir_frame, text="File Filter:").grid(column=2, row=2, sticky=tk.W, padx=(10, 0))
        self.file_filter = tk.StringVar(value=self.last_dirs.get("file_filter", "*"))
        ttk.Entry(dir_frame, textvariable=self.file_filter, width=20).grid(column=3, row=2, sticky=tk.W)
        ttk.Label(dir_frame, text="(use * and ? as wildcards)").grid(column=4, row=2, sticky=tk.W)
        
        # Compare button
        compare_button = ttk.Button(dir_frame, text="Compare", command=self.compare_directories)
        compare_button.grid(column=5, row=2, padx=5, pady=10)
        
        ## # Make Compare button the default button
        ## self.root.bind('<Return>', lambda event: self.compare_directories())
        
        # Add 'C' shortcut key
        self.root.bind('c', lambda event: self.compare_directories())
        self.root.bind('C', lambda event: self.compare_directories())
        
        # Create main frame for table
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create table frame
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview for file comparison
        columns = ("suggestion", "left_file", "del_left", "right_file", "del_right", "copy_left", "copy_right", "comparison", 
                  "size_left", "size_right", "created_left", "created_right", 
                  "modified_left", "modified_right")
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        
        # Define headings
        self.tree.heading("suggestion", text="Suggestion")
        self.tree.heading("left_file", text="Left File")
        self.tree.heading("del_left", text="Del ←×")
        self.tree.heading("right_file", text="Right File")
        self.tree.heading("del_right", text="Del →×")
        self.tree.heading("copy_left", text="Copy ←")
        self.tree.heading("copy_right", text="Copy →")
        self.tree.heading("comparison", text="Comparison")
        self.tree.heading("size_left", text="Size (Left)")
        self.tree.heading("size_right", text="Size (Right)")
        self.tree.heading("created_left", text="Created (Left)")
        self.tree.heading("created_right", text="Created (Right)")
        self.tree.heading("modified_left", text="Modified (Left)")
        self.tree.heading("modified_right", text="Modified (Right)")
        
        # Define column widths
        self.tree.column("suggestion", width=50, anchor=tk.CENTER)
        self.tree.column("left_file", width=150)
        self.tree.column("del_left", width=30, anchor=tk.CENTER)
        self.tree.column("right_file", width=150)
        self.tree.column("del_right", width=30, anchor=tk.CENTER)
        self.tree.column("copy_left", width=30, anchor=tk.CENTER)
        self.tree.column("copy_right", width=30, anchor=tk.CENTER)
        self.tree.column("comparison", width=100)
        self.tree.column("size_left", width=80)
        self.tree.column("size_right", width=80)
        self.tree.column("created_left", width=120)
        self.tree.column("created_right", width=120)
        self.tree.column("modified_left", width=120)
        self.tree.column("modified_right", width=120)
        
        # Add visible grid lines
        style.configure("Treeview", rowheight=30)  # Increase row height for larger font
        #style.configure("Treeview", font=('Arial', 11))  # Increase font size
        #style.configure("Treeview.Heading", font=('Arial', 11, 'bold'))  # Increase heading font size
        
        # Configure grid lines
        style.configure("Treeview", background="#f0f0f0", fieldbackground="#f0f0f0")
        style.map('Treeview', background=[('selected', '#0078D7')])
        
        # Enable grid lines
        self.tree.tag_configure('oddrow', background='#f0f0f0')
        self.tree.tag_configure('evenrow', background='#ffffff')
        self.tree.tag_configure('match', background='#e6ffe6')  # Light green for matching files
        self.tree.tag_configure('match_odd', background='#c6ffc6')  # Darker green for matching files in odd rows
        self.tree.tag_configure('danger_even', background='#ffC0C0')  # Lighter red for newer left files in even rows
        self.tree.tag_configure('danger_odd', background='#FF9090')  # Darker red for  for newer left files in odd rows
        self.tree.tag_configure('delete', font=('Default', 16, 'bold'))  # Bold font for delete symbols
        
        # Pack the treeview
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Bind click events for copy buttons
        self.tree.bind("<ButtonRelease-1>", self.on_tree_click)
        # Bind double-click event for opening files
        self.tree.bind("<Double-1>", self.on_double_click)
        # Bind right-click event for context menu
        self.tree.bind("<Button-3>", self.show_context_menu)
        ## Bind the hover movement - demo code
        #self.tree.bind("<Motion>", self.on_treeview_motion)
        # Add tooltip for suggestion column
        self.tree.bind("<Motion>", self.show_suggestion_tooltip)
    


        

    def reveal(self, target):
        """Reveal the specified file in the system's file explorer."""

        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.tree.item(item, "values")
        left_dir = self.left_dir_var.get()
        right_dir = self.right_dir_var.get()
        
        # Get the column that was right-clicked
        column = self.tree.identify_column(self.tree.winfo_pointerx() - self.tree.winfo_rootx())
        
        files_to_reveal = []
        
        if target == "this":
            if column == "#1" and values[1]:  # Left file column
                files_to_reveal.append((os.path.join(left_dir, values[1]), "left"))
            elif column == "#3" and values[3]:  # Right file column
                files_to_reveal.append((os.path.join(right_dir, values[3]), "right"))
        elif target == "left" and values[1]:
            files_to_reveal.append((os.path.join(left_dir, values[1]), "left"))
        elif target == "right" and values[3]:
            files_to_reveal.append((os.path.join(right_dir, values[3]), "right"))
        elif target == "both":
            if values[1]:
                files_to_reveal.append((os.path.join(left_dir, values[1]), "left"))
            if values[3]:
                files_to_reveal.append((os.path.join(right_dir, values[3]), "right"))
        
        if not files_to_reveal:
            return
            
        # Delete files
        for file_path, _ in files_to_reveal:
            try:
                self.reveal_one_file(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to reveal {file_path}: {str(e)}")
                return
            

    def reveal_one_file(self, file_path):
        """Really Reveal the (only) specified file in the system's file explorer"""
                
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.")
            return False
            
        # Handle different platforms
        try:
            if os.name == 'nt':  # Windows
                # Use explorer.exe to select the file
                subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])
            elif os.name == 'posix':  # macOS or Linux
                if os.uname().sysname == 'Darwin':  # macOS
                    # Use AppleScript to reveal in Finder
                    subprocess.run(['osascript', '-e', 
                                f'tell application "Finder" to reveal POSIX file "{os.path.abspath(file_path)}"'])
                    subprocess.run(['osascript', '-e', 'tell application "Finder" to activate'])
                else:  # Linux
                    # Try common file managers
                    file_dir = os.path.dirname(os.path.abspath(file_path))
                    if os.path.exists('/usr/bin/nautilus'):  # GNOME
                        subprocess.run(['nautilus', file_dir])
                    elif os.path.exists('/usr/bin/dolphin'):  # KDE
                        subprocess.run(['dolphin', '--select', file_path])
                    elif os.path.exists('/usr/bin/nemo'):  # Cinnamon
                        subprocess.run(['nemo', file_dir])
                    elif os.path.exists('/usr/bin/thunar'):  # XFCE
                        subprocess.run(['thunar', file_dir])
                    else:
                        print("Could not find a suitable file manager.")
                        return False
            return True
        except Exception as e:
            print(f"Error revealing file: {e}")
            return False


    def load_settings(self):
        # Check if the settings file exists
        if not os.path.exists(self.settings_file_path):
            return {"left": "", "right": "", "include_subdirs": False, "file_filter": "*", "show_equal_files": True, "long_win_fnames": True}
            
        try:
            with open(self.settings_file_path, "r") as f:
                data = json.load(f)
                return {
                    "left": data.get("left", ""),
                    "right": data.get("right", ""),
                    "include_subdirs": data.get("include_subdirs", False),
                    "file_filter": data.get("file_filter", "*"),
                    "show_equal_files": data.get("show_equal_files", "*"),
                    "long_win_fnames":  data.get("long_win_fnames", True)
                }
        # except json.JSONDecodeError:
        except Exception as e:    
            print(f"An error occurred: {e}")  # Print the error message
            self.show_status_message(f"An error occurred: {e}")
            # If the file exists but is corrupted, return default values
            return {"left": "", "right": "", "include_subdirs": False, "file_filter": "*", "show_equal_files": True, "long_win_fnames": True}
    
    def save_settings(self):
        with open(self.settings_file_path, "w") as f:
            json.dump({
                "left": self.left_dir_var.get(),
                "right": self.right_dir_var.get(),
                "include_subdirs": self.include_subdirs.get(),
                "file_filter": self.file_filter.get(),
                "show_equal_files": self.show_equal_files.get(),
                "long_win_fnames":  self.long_win_fnames.get()
            }, f)

    def delete_left_dir(self):
        self.delete_single_file(self.left_dir_var.get())

    def get_parent_directory(self, path):
        """
        Returns the parent directory of the given path.
        If the path is a root directory, returns the path itself.
        """
        parent_dir = os.path.dirname(os.path.abspath(path))
        # If we're at the root directory, just return the original path
        if parent_dir == path:
            return path
        return parent_dir


    def browse_left_dir(self):
        ini_dir = self.left_dir_var.get()
        if ini_dir[:4] != "\\\\?\\":
            ini = ini_dir[4:]
        while not os.path.isdir(ini_dir):
            ini_dir=self.get_parent_directory(ini_dir)            
        directory = filedialog.askdirectory(initialdir=ini_dir)
        if directory:
            self.left_dir_var.set(directory)
    
    def browse_right_dir(self):
        ini_dir = self.right_dir_var.get()
        if ini_dir[:4] != "\\\\?\\":
            ini = ini_dir[4:]
        directory = filedialog.askdirectory(initialdir=ini_dir)
        if directory:
            self.right_dir_var.set(directory)
    
    def compare_directories(self):
        self.tree.delete(*self.tree.get_children())
        self.tooltips.clear()  # Clear previous tooltips
        left_dir = self.left_dir_var.get()
        right_dir = self.right_dir_var.get()
        
        # Check if directories are empty
        if not left_dir and not right_dir:
            self.show_status_message("Please select both directories and press 'Compare' to compare")
            return
        
        # Check if directories exist
        if not os.path.isdir(left_dir):
            self.show_status_message(f"Left directory does not exist or is not accessible: {left_dir}")
            return
        
        if not os.path.isdir(right_dir):
            self.show_status_message(f"Right directory does not exist or is not accessible: {right_dir}")
            return

        # Save last used directories
        self.save_settings()

        # Normalize (not needed but prettier) CAREFUL: Windows specific...
        if self.long_win_fnames.get():
            if left_dir[:4] != "\\\\?\\":
                left_dir = "\\\\?\\"+left_dir
            if right_dir[:4] != "\\\\?\\":
                right_dir = "\\\\?\\"+right_dir

            left_dir = os.path.normpath(left_dir)
            left_dir = left_dir.replace("/", "\\") 
            right_dir = os.path.normpath(right_dir)
            right_dir = right_dir.replace("/", "\\") 
            self.left_dir_var.set(left_dir)
            self.right_dir_var.set(right_dir)
            # Save last used directories
            self.save_settings()


        self.show_status_message(f"Comparing ... {left_dir}<->{right_dir}")
        root.update()


        # Get file lists
        start_time = time.perf_counter()  # Start timer
        left_files = self.get_files(left_dir)
        right_files = self.get_files(right_dir)
        print(f"Get Files: {(time.perf_counter() - start_time) * 1000:.3f} ms")


        # Combine file lists
        # all_files = sorted(set(left_files) | set(right_files)) --#### AJS with SORTING
        start_time = time.perf_counter()  # Start timer
        all_files = set(left_files).union(right_files)
        print(f"Get Files: {(time.perf_counter() - start_time) * 1000:.3f} ms")

        start_time = time.perf_counter()  # Start timer
        for i, file in enumerate(all_files):

            if (i%10)==9:
                self.show_status_message(f" {i:5d} -> {(time.perf_counter() - start_time) * 1000:5.1f} ms ~~ {left_dir}<->{right_dir} ")
                #print((f" {i:5d} -> {(time.perf_counter() - start_time) * 1000:5.1f} ms ~~ {left_dir}<->{right_dir} "))
                root.update()
                #root.update_idletasks

            left_path = os.path.join(left_dir, file) if file in left_files else ""
            right_path = os.path.join(right_dir, file) if file in right_files else ""
            
            comparison = ""
            size_left = ""
            size_right = ""
            created_left = ""
            created_right = ""
            modified_left = ""
            modified_right = ""
            suggestion = "--"
            suggestion_tooltip = "No suggestion"
            
            if file in left_files:
                try:
                    stats = os.stat(left_path)
                    size_left = f"{stats.st_size:_}".replace('_', ' ')
                    created_left = datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    modified_left = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            if file in right_files:
                try:
                    stats = os.stat(right_path)
                    size_right = f"{stats.st_size:_}".replace('_', ' ')
                    created_right = datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    modified_right = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            if file in left_files and file in right_files:
                if os.path.isdir(left_path) and os.path.isdir(right_path):
                    comparison = "Both directories"
                elif os.path.isfile(left_path) and os.path.isfile(right_path):
                    if filecmp.cmp(left_path, right_path, shallow=False):
                        comparison = "Identical"
                        # For identical files, use the same modified date
                        modified_right = modified_left
                        suggestion = "XDL="
                        suggestion_tooltip = "Files are identical - Suggestion: Delete left file"
                    else:
                        comparison = "Different"
                        # Compare modification dates
                        if modified_left and modified_right:
                            left_date = datetime.datetime.strptime(modified_left, '%Y-%m-%d %H:%M:%S')
                            right_date = datetime.datetime.strptime(modified_right, '%Y-%m-%d %H:%M:%S')
                            if left_date < right_date:
                                suggestion = "XDL<"
                                suggestion_tooltip = "Right file is newer - Suggestion: Delete left file"
                            elif left_date > right_date:
                                suggestion = "CL>R"
                                suggestion_tooltip = "Left file is newer - Suggestion: Copy from left to right"
            elif file in left_files:
                comparison = "Left only"
            else:
                comparison = "Right only"
            
            # Add copy and delete button placeholders
            copy_left = "|←|" if file in right_files else ""
            copy_right = "|→|" if file in left_files else ""
            del_left = "|×|" if file in left_files else ""
            del_right = "|×|" if file in right_files else ""
            
            # Insert with alternating row colors
            is_odd = i % 2 == 1
            tag = 'oddrow' if is_odd else 'evenrow'
            
            # Check if size and modification date match
            if (size_left and size_right and size_left == size_right and 
                modified_left and modified_right and modified_left == modified_right):
                tag = 'match_odd' if is_odd else 'match'

            if modified_left > modified_right:
                tag = 'danger_even' if is_odd else 'danger_odd'

            if (size_left and size_right and (size_left > size_right) ):
                tag = 'danger_even' if is_odd else 'danger_odd'

            if (size_left and not size_right):
                tag = 'danger_even' if is_odd else 'danger_odd'


            if (tag == 'match_odd' or tag == 'match') and not self.show_equal_files.get():
                continue

            # Create item with base tag
            item = self.tree.insert("", tk.END, values=(
                suggestion,
                file if file in left_files else "",
                del_left,
                file if file in right_files else "",
                del_right,
                copy_left,
                copy_right,
                comparison,
                size_left,
                size_right,
                created_left,
                created_right,
                modified_left,
                modified_right
            ), tags=(tag,))
            
            # Store suggestion tooltip
            self.tree.set(item, "suggestion", suggestion)
            self.tooltips[item] = suggestion_tooltip  # Store tooltip in dictionary
            
            # Bind suggestion click only if there's a suggestion
            if suggestion != "--":
                self.tree.tag_bind(item, "<Button-1>", lambda e, s=suggestion, l=left_path, r=right_path: self.handle_suggestion_click(e, s, l, r))
            
            # Add delete tag to specific cells if they contain the × symbol
            if del_left:
                self.tree.set(item, "del_left", del_left)
                self.tree.tag_configure(f"delete_{item}", font=('Default', 12, 'bold'))
                self.tree.tag_bind(f"delete_{item}", "<Button-1>", lambda e, p=os.path.join(left_dir, file): self.delete_single_file(p))
            if del_right:
                self.tree.set(item, "del_right", del_right)
                self.tree.tag_configure(f"delete_{item}", font=('Default', 12, 'bold'))
                self.tree.tag_bind(f"delete_{item}", "<Button-1>", lambda e, p=os.path.join(right_dir, file): self.delete_single_file(p))
        
    def get_files(self, directory):
        if not self.include_subdirs.get():
            return [f for f in os.listdir(directory) 
                   if os.path.isfile(os.path.join(directory, f)) 
                   and self.matches_filter(f)]
        else:
            result = []
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                rel_path = os.path.relpath(root, directory)
                if rel_path == ".":
                    result.extend(f for f in files if self.matches_filter(f))
                else:
                    result.extend(os.path.join(rel_path, f) for f in files if self.matches_filter(f))
            return result

    def matches_filter(self, filename):
        pattern = self.file_filter.get()
        return fnmatch.fnmatch(filename.lower(), pattern.lower())
    
    def on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item:
            return
            
        values = self.tree.item(item, "values")
        left_dir = self.left_dir_var.get()
        right_dir = self.right_dir_var.get()
        
        # Treat things (actions) by the order of the column

        if column == "#1" and values[0]:  # Do Suggestion
            if values[0] == "--": 
                return
            
            if values[0] == "XDL<" or values[0] == "XDL=":
                column = "#3" # implying will delete left file

        # Delete left file (column #3)
        if column == "#3" and values[1]:  # Delete left button Col=#3 also by suggestion!
            left_file = values[1]
            if left_file:
                file_path = os.path.join(left_dir, left_file)
                self.delete_single_file(file_path)

        # Delete right file (column #5)
        elif column == "#5" and values[3]:  # Delete right button
            right_file = values[3]
            if right_file:
                file_path = os.path.join(right_dir, right_file)
                self.delete_single_file(file_path)
    
        # Copy right to left (column #5)
        elif column == "#6" and values[3]:  # Copy RL
            right_file = values[3]
            if right_file:
                source = os.path.join(right_dir, right_file)
                dest = os.path.join(left_dir, right_file)
                self.copy_file(source, dest, "right to left")
        
        # Copy left to right (column #6)
        elif column == "#7" and values[1]:  # Copy LR
            left_file = values[1]
            if left_file:
                source = os.path.join(left_dir, left_file)
                dest = os.path.join(right_dir, left_file)
                self.copy_file(source, dest, "left to right")
        
    def copy_file(self, source, dest, direction):
        if messagebox.askyesno("Copy File", f"Copy from {direction}?\n{source} -> {dest}"):
            try:
                if os.path.isdir(source):
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(source, dest)
                else:
                    os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else dest, exist_ok=True)
                    shutil.copy2(source, dest)
                self.show_status_message("File copied successfully")
                self.compare_directories()  # Refresh the comparison
            except Exception as e:
                self.show_status_message(f"Failed to copy file: {str(e)}")
    
    def on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item:
            return
            
        values = self.tree.item(item, "values")
        left_dir = self.left_dir_var.get()
        right_dir = self.right_dir_var.get()
        
        # Open file from left directory (column #1)
        if column == "#1" and values[1]:  # Left file column
            file_path = os.path.join(left_dir, values[1])
            self.open_file(file_path)
        
        # Open file from right directory (column #2)
        elif column == "#3" and values[3]:  # Right file column
            file_path = os.path.join(right_dir, values[3])
            self.open_file(file_path)
    
    def open_file(self, file_path):
        try:
            if os.path.exists(file_path):
                if os.path.isdir(file_path):
                    # Open directory in file explorer
                    os.startfile(file_path)
                else:
                    # Open file with default application
                    os.startfile(file_path)
            else:
                messagebox.showerror("Error", f"File not found: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def show_context_menu(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        item = self.tree.identify_row(event.y)
        if not item:
            return
            
        # Select the item under cursor
        self.tree.selection_set(item)
        
        # Show context menu at cursor position
        self.context_menu.post(event.x_root, event.y_root)
    
    def open_selected_file(self):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.tree.item(item, "values")
        left_dir = self.left_dir_var.get()
        right_dir = self.right_dir_var.get()
        
        # Get the column that was right-clicked
        column = self.tree.identify_column(self.tree.winfo_pointerx() - self.tree.winfo_rootx())
        
        if column == "#1" and values[1]:  # Left file column
            file_path = os.path.join(left_dir, values[1])
            self.open_file(file_path)
        elif column == "#2" and values[2]:  # Right file column
            file_path = os.path.join(right_dir, values[2])
            self.open_file(file_path)
    
    def delete_file_LRB(self, target):
        selection = self.tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.tree.item(item, "values")
        left_dir = self.left_dir_var.get()
        right_dir = self.right_dir_var.get()
        
        # Get the column that was right-clicked
        column = self.tree.identify_column(self.tree.winfo_pointerx() - self.tree.winfo_rootx())
        
        files_to_delete = []
        
        if target == "this":
            if column == "#1" and values[1]:  # Left file column
                files_to_delete.append((os.path.join(left_dir, values[1]), "left"))
            elif column == "#3" and values[3]:  # Right file column
                files_to_delete.append((os.path.join(right_dir, values[3]), "right"))
        elif target == "left" and values[1]:
            files_to_delete.append((os.path.join(left_dir, values[1]), "left"))
        elif target == "right" and values[3]:
            files_to_delete.append((os.path.join(right_dir, values[3]), "right"))
        elif target == "both":
            if values[1]:
                files_to_delete.append((os.path.join(left_dir, values[1]), "left"))
            if values[3]:
                files_to_delete.append((os.path.join(right_dir, values[3]), "right"))
        
        if not files_to_delete:
            return
            
        # Confirm deletion
        files_list = "\n".join(f"- {path}" for path, _ in files_to_delete)
        if not messagebox.askyesno("Confirm Delete", 
            f"Are you sure you want to delete these files?\n\n{files_list}"):
            return
        
        # Delete files
        for file_path, _ in files_to_delete:
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete {file_path}: {str(e)}")
                return
            
        # Refresh the comparison
        self.compare_directories()

    def delete_single_file(self, file_path):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this file?\n\n{file_path}"):
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                self.show_status_message(f"File deleted successfully -- {file_path}")
                self.compare_directories()  # Refresh the comparison
            except Exception as e:
                self.show_status_message(f"Failed to delete file: {str(e)} -- {file_path}")

    def show_status_message(self, message, duration=6000):
        """Show a temporary message in the status bar"""
        self.status_var.set(message)
        # Temporarily disable timer
        # if self.status_timer:
        #    self.root.after_cancel(self.status_timer)
        #self.status_timer = self.root.after(duration, lambda: self.status_var.set(""))

    
    def on_treeview_motion(self, event):
        # Get the item under the cursor
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        self.show_status_message(f"Cursor at ({item}{column})")

#        if item and column:
#             # Get the content of the cell
#            cell_value = self.tree.item(item, "values")[int(column[1:]) - 1]
#            #print(f"Cursor at ({event.x}, {event.y}), Cell content: {cell_value}")
#            self.show_status_message(f"Cursor at ({event.x}, {event.y}), Cell{item}{column} => {cell_value}")


    def show_suggestion_tooltip(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        if column != "#1":  # Suggestion column
            self.tree.bind(self.on_treeview_motion(event))
            return
            
        item = self.tree.identify_row(event.y)
        if not item:
            return
            
        tooltip = self.tooltips.get(item, "")
        if tooltip:
            self.status_var.set(tooltip)
        else:
            self.status_var.set("")

    def handle_suggestion_click(self, event, suggestion, left_path, right_path):
        # Check if click was in the suggestion column
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        if column != "#1":  # Suggestion column
            return
            
        if suggestion == "XDL=" or suggestion == "XDL<":
            self.delete_single_file(left_path)
        elif suggestion == "CL>R":
            self.copy_file(left_path, right_path, "left to right")

if __name__ == "__main__":
    root = tk.Tk()
    app = DirectoryComparisonTool(root)
    root.mainloop()



