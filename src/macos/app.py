"""
macOS GUI wrapper for Docker Optimizer
Provides a tkinter interface for analyzing Dockerfiles and running the web dashboard.
"""
import sys
import os
import threading
import tempfile
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class DockerOptimizerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Docker Optimizer")
        self.root.geometry("850x650")
        self.root.configure(bg="#0d1117")

        self.server_thread = None
        self.server_running = False
        self.server_instance = None

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0d1117")
        style.configure("TLabel", background="#0d1117", foreground="#c9d1d9", font=("Helvetica", 12))
        style.configure("Header.TLabel", font=("Helvetica", 18, "bold"), foreground="#58a6ff")
        style.configure("Status.TLabel", font=("Helvetica", 11), foreground="#8b949e")

        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        ttk.Label(header, text="Docker Optimizer", style="Header.TLabel").pack(side=tk.LEFT)
        self.status_label = ttk.Label(header, text="Web Server: Stopped", style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT)

        # Server controls
        ctrl_frame = ttk.Frame(self.root)
        ctrl_frame.pack(fill=tk.X, padx=20, pady=10)

        self.start_btn = ttk.Button(ctrl_frame, text="Start Web Server", command=self.toggle_server)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(ctrl_frame, text="Open in Browser", command=self.open_browser).pack(side=tk.LEFT)

        port_frame = ttk.Frame(self.root)
        port_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value="8080")
        ttk.Entry(port_frame, textvariable=self.port_var, width=8).pack(side=tk.LEFT, padx=8)

        # Dockerfile input
        input_frame = ttk.LabelFrame(self.root, text="Dockerfile Content")
        input_frame.pack(fill=tk.BOTH, padx=20, pady=10, expand=True)

        btn_row = ttk.Frame(input_frame)
        btn_row.pack(fill=tk.X, padx=10, pady=(8, 4))
        ttk.Button(btn_row, text="Load File", command=self.load_file).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_row, text="Analyze", command=self.analyze).pack(side=tk.LEFT, padx=(0, 8))

        self.dockerfile_input = scrolledtext.ScrolledText(
            input_frame, height=10, bg="#161b22", fg="#c9d1d9",
            insertbackground="#c9d1d9", font=("SF Mono", 11), borderwidth=1, relief=tk.FLAT
        )
        self.dockerfile_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Results area
        ttk.Label(self.root, text="Results:").pack(anchor=tk.W, padx=20, pady=(10, 0))
        self.log_area = scrolledtext.ScrolledText(
            self.root, height=10, bg="#161b22", fg="#c9d1d9",
            insertbackground="#c9d1d9", font=("SF Mono", 11), borderwidth=1, relief=tk.FLAT
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=(4, 20))

    def log(self, msg):
        self.log_area.insert(tk.END, f"{msg}\n")
        self.log_area.see(tk.END)

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("Dockerfile", "Dockerfile*"), ("All files", "*.*")])
        if path:
            with open(path, "r") as f:
                self.dockerfile_input.delete("1.0", tk.END)
                self.dockerfile_input.insert(tk.END, f.read())
            self.log(f"Loaded: {path}")

    def analyze(self):
        content = self.dockerfile_input.get("1.0", tk.END).strip()
        if not content:
            messagebox.showwarning("Warning", "Please enter Dockerfile content.")
            return

        self.log("Analyzing Dockerfile...")
        try:
            from image_analyzer import analyze_dockerfile
            from optimizer import generate_suggestions, rewrite_dockerfile

            with tempfile.NamedTemporaryFile(mode="w", suffix="Dockerfile", delete=False) as f:
                f.write(content)
                tmp_path = f.name

            try:
                result = analyze_dockerfile(tmp_path)
                suggestions = generate_suggestions(result)
                result.suggestions = suggestions
                optimized = rewrite_dockerfile(result)
            finally:
                os.unlink(tmp_path)

            self.log(f"Base image: {result.base_image}")
            self.log(f"Layers: {result.total_layers}")
            self.log(f"Estimated size: {result.estimated_size_mb or 'unknown'} MB")
            self.log(f"Multi-stage: {'Yes' if result.has_multistage else 'No'}")
            self.log(f"Issues found: {len(result.issues)}")
            for issue in result.issues:
                self.log(f"  [{issue.severity.value}] {issue.title}: {issue.description}")
            self.log(f"\nOptimization suggestions: {len(suggestions)}")
            for s in suggestions:
                self.log(f"  #{s.priority} {s.title}: {s.estimated_savings}")
            self.log(f"\n--- Optimized Dockerfile ---\n{optimized}")
        except Exception as e:
            self.log(f"Error: {e}")

    def toggle_server(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        port = int(self.port_var.get())
        self.log(f"Starting web server on port {port}...")

        def run():
            try:
                import uvicorn
                from src.web.app import app
                self.server_instance = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning"))
                self.server_instance.run()
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Server error: {e}"))
                self.root.after(0, lambda: self._set_server_state(False))

        self.server_thread = threading.Thread(target=run, daemon=True)
        self.server_thread.start()
        self._set_server_state(True)
        self.log(f"Web server started at http://localhost:{port}")

    def stop_server(self):
        if self.server_instance:
            self.server_instance.should_exit = True
        self._set_server_state(False)
        self.log("Web server stopped.")

    def _set_server_state(self, running):
        self.server_running = running
        if running:
            self.start_btn.configure(text="Stop Web Server")
            self.status_label.configure(text="Web Server: Running", foreground="#3fb950")
        else:
            self.start_btn.configure(text="Start Web Server")
            self.status_label.configure(text="Web Server: Stopped", foreground="#8b949e")

    def open_browser(self):
        import webbrowser
        port = self.port_var.get()
        webbrowser.open(f"http://localhost:{port}")
        self.log(f"Opened browser at http://localhost:{port}")

    def run(self):
        self.root.mainloop()


def main():
    app = DockerOptimizerApp()
    app.run()


if __name__ == "__main__":
    main()
