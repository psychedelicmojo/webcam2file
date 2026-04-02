"""Settings dialog UI for the Webcam-to-ComfyUI Desktop Application."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from src.models.application_settings import ApplicationSettings
from src.services.comfyui_service import IComfyUIService
from src.services.settings_service import SettingsService


class SettingsDialog:
    """Settings dialog for configuring application preferences.

    This dialog allows users to configure:
    - Output folder for captured images
    - ComfyUI API endpoint
    - 4 Workflow JSON file paths (each with a name)
    - Email address for notifications
    - API timeout settings
    """

    def __init__(
        self,
        parent: tk.Tk,
        settings_service: SettingsService,
        comfyui_service: Optional[IComfyUIService] = None,
    ):
        """Initialize the settings dialog.

        Args:
            parent: Parent window
            settings_service: Service for managing settings
            comfyui_service: Optional service for testing ComfyUI connection
        """
        self._parent = parent
        self._settings_service = settings_service
        self._comfyui_service = comfyui_service

        # Create dialog window
        self._dialog = tk.Toplevel(parent)
        self._dialog.title("Settings")
        self._dialog.geometry("700x900")
        self._dialog.resizable(False, False)

        # Center dialog on parent
        self._dialog.transient(parent)
        self._dialog.grab_set()

        # Result storage
        self._result: Optional[ApplicationSettings] = None
        self._settings_changed = False

        # Workflow config variables storage (name + path pairs)
        self._workflow_name_vars: list[tk.StringVar] = []
        self._workflow_path_vars: list[tk.StringVar] = []

        # Email address variable
        self._email_address_var = tk.StringVar()

        # Build UI
        self._build_ui()

        # Load current settings
        self._load_settings()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Main frame
        main_frame = ttk.Frame(self._dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights
        self._dialog.columnconfigure(0, weight=1)
        self._dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Output folder section
        ttk.Label(main_frame, text="Output Folder:").grid(
            row=0, column=0, sticky="w", pady=5
        )
        self._output_folder_var = tk.StringVar()
        self._output_folder_entry = ttk.Entry(
            main_frame, textvariable=self._output_folder_var, width=50
        )
        self._output_folder_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        self._output_folder_button = ttk.Button(
            main_frame, text="Browse...", command=self._browse_output_folder
        )
        self._output_folder_button.grid(row=0, column=2, pady=5, padx=5)

        # ComfyUI endpoint section
        ttk.Label(main_frame, text="ComfyUI Endpoint:").grid(
            row=1, column=0, sticky="w", pady=5
        )
        self._comfyui_endpoint_var = tk.StringVar()
        self._comfyui_endpoint_entry = ttk.Entry(
            main_frame, textvariable=self._comfyui_endpoint_var, width=50
        )
        self._comfyui_endpoint_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        self._test_connection_button = ttk.Button(
            main_frame, text="Test Connection", command=self._test_connection
        )
        self._test_connection_button.grid(row=1, column=2, pady=5, padx=5)

        # Workflow JSON path sections (4 configurations)
        workflow_start_row = 2
        for i in range(4):
            ttk.Label(main_frame, text=f"Workflow {i + 1} Name:").grid(
                row=workflow_start_row + i * 2, column=0, sticky="w", pady=2
            )
            name_var = tk.StringVar()
            self._workflow_name_vars.append(name_var)
            name_entry = ttk.Entry(main_frame, textvariable=name_var, width=50)
            name_entry.grid(
                row=workflow_start_row + i * 2, column=1, sticky="ew", pady=2, padx=5
            )

            ttk.Label(main_frame, text=f"Workflow {i + 1} JSON:").grid(
                row=workflow_start_row + i * 2 + 1, column=0, sticky="w", pady=2
            )
            path_var = tk.StringVar()
            self._workflow_path_vars.append(path_var)
            path_entry = ttk.Entry(main_frame, textvariable=path_var, width=50)
            path_entry.grid(
                row=workflow_start_row + i * 2 + 1,
                column=1,
                sticky="ew",
                pady=2,
                padx=5,
            )
            browse_button = ttk.Button(
                main_frame,
                text="Browse...",
                command=lambda idx=i: self._browse_workflow_json(idx),
            )
            browse_button.grid(
                row=workflow_start_row + i * 2 + 1, column=2, pady=2, padx=5
            )

        # Email address section (placed after workflow selection)
        ttk.Label(main_frame, text="Email Address:").grid(
            row=10, column=0, sticky="w", pady=5
        )
        self._email_address_entry = ttk.Entry(
            main_frame, textvariable=self._email_address_var, width=50
        )
        self._email_address_entry.grid(row=10, column=1, sticky="ew", pady=5, padx=5)

        # API timeout section (placed after email address)
        ttk.Label(main_frame, text="API Timeout (seconds):").grid(
            row=11, column=0, sticky="w", pady=5
        )
        self._api_timeout_var = tk.StringVar(value="30")
        self._api_timeout_entry = ttk.Entry(
            main_frame, textvariable=self._api_timeout_var, width=10
        )
        self._api_timeout_entry.grid(row=11, column=1, sticky="w", pady=5, padx=5)

        # Status label
        self._status_label = ttk.Label(main_frame, text="", foreground="blue")
        self._status_label.grid(row=12, column=0, columnspan=3, pady=10)

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=13, column=0, columnspan=3, pady=10)

        # Save button
        self._save_button = ttk.Button(
            buttons_frame, text="Save", command=self._on_save
        )
        self._save_button.pack(side=tk.LEFT, padx=5)

        # Cancel button
        self._cancel_button = ttk.Button(
            buttons_frame, text="Cancel", command=self._on_cancel
        )
        self._cancel_button.pack(side=tk.LEFT, padx=5)

    def _load_settings(self) -> None:
        """Load current settings into the dialog fields."""
        try:
            settings = self._settings_service.get_current_settings()
            if settings:
                self._output_folder_var.set(settings.output_folder)
                self._comfyui_endpoint_var.set(settings.comfyui_endpoint)
                # Load workflow configs
                for i, config in enumerate(settings.workflow_configs):
                    if i < len(self._workflow_name_vars):
                        self._workflow_name_vars[i].set(config.name)
                        self._workflow_path_vars[i].set(config.path)
                self._email_address_var.set(settings.email_address)
                self._api_timeout_var.set(str(settings.api_timeout))
            else:
                # Use defaults if settings not loaded
                defaults = self._settings_service.get_default_settings()
                self._output_folder_var.set(defaults.get("output_folder", "captures"))
                self._comfyui_endpoint_var.set(
                    defaults.get("comfyui_endpoint", "http://127.0.0.1:8188")
                )
                # Set default workflow configs
                for i in range(4):
                    if i < len(self._workflow_path_vars):
                        self._workflow_path_vars[i].set(
                            defaults.get(f"workflow_{i}_path", "")
                        )
                        self._workflow_name_vars[i].set(
                            defaults.get(f"workflow_{i}_name", f"Workflow {i + 1}")
                        )
                self._email_address_var.set(defaults.get("email_address", ""))
                self._api_timeout_var.set(str(defaults.get("api_timeout", 30)))
        except Exception:
            # Use defaults if settings not loaded
            defaults = self._settings_service.get_default_settings()
            self._output_folder_var.set(defaults.get("output_folder", "captures"))
            self._comfyui_endpoint_var.set(
                defaults.get("comfyui_endpoint", "http://127.0.0.1:8188")
            )
            # Set default workflow configs
            for i in range(4):
                if i < len(self._workflow_path_vars):
                    self._workflow_path_vars[i].set(
                        defaults.get(f"workflow_{i}_path", "")
                    )
                    self._workflow_name_vars[i].set(
                        defaults.get(f"workflow_{i}_name", f"Workflow {i + 1}")
                    )
            self._email_address_var.set(defaults.get("email_address", ""))
            self._api_timeout_var.set(str(defaults.get("api_timeout", 30)))

    def _browse_output_folder(self) -> None:
        """Open folder dialog to select output folder."""
        folder = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self._output_folder_var.get() or ".",
        )
        if folder:
            self._output_folder_var.set(folder)

    def _browse_workflow_json(self, index: int) -> None:
        """Open file dialog to select workflow JSON file.

        Args:
            index: Index of the workflow config (0-3)
        """
        file_path = filedialog.askopenfilename(
            title="Select Workflow JSON",
            initialdir=self._workflow_path_vars[index].get() or ".",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if file_path:
            self._workflow_path_vars[index].set(file_path)

    def _test_connection(self) -> None:
        """Test connection to ComfyUI API."""
        endpoint = self._comfyui_endpoint_var.get().strip()

        if not endpoint:
            messagebox.showerror("Error", "Please enter a ComfyUI endpoint")
            return

        # Create temporary service for testing
        from src.services.comfyui_service_impl import ComfyUIService

        try:
            timeout = int(self._api_timeout_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid timeout value")
            return

        service = ComfyUIService(endpoint=endpoint, timeout=timeout)
        result = service.is_available()

        if result:
            self._status_label.config(
                text=f"Connected to {endpoint}", foreground="green"
            )
        else:
            self._status_label.config(
                text=f"Cannot connect to {endpoint}", foreground="red"
            )

    def _validate_settings(self) -> bool:
        """Validate all settings before saving.

        Returns:
            True if settings are valid, False otherwise
        """
        output_folder = self._output_folder_var.get().strip()
        comfyui_endpoint = self._comfyui_endpoint_var.get().strip()
        api_timeout = self._api_timeout_var.get().strip()

        # Validate output folder
        if not output_folder:
            messagebox.showerror("Error", "Please select an output folder")
            return False

        # Validate ComfyUI endpoint
        if not comfyui_endpoint:
            messagebox.showerror("Error", "Please enter a ComfyUI endpoint")
            return False

        # At least one workflow must have a path
        has_workflow = any(var.get().strip() for var in self._workflow_path_vars)
        if not has_workflow:
            messagebox.showerror(
                "Error", "Please select at least one workflow JSON file"
            )
            return False

        # Validate API timeout
        try:
            timeout = int(api_timeout)
            if timeout < 1:
                raise ValueError("Timeout must be at least 1 second")
        except ValueError:
            messagebox.showerror("Error", "API timeout must be a positive integer")
            return False

        return True

    def _on_save(self) -> None:
        """Handle save button press."""
        if not self._validate_settings():
            return

        try:
            # Collect workflow configs
            workflow_configs = []
            for i in range(4):
                name = self._workflow_name_vars[i].get().strip()
                path = self._workflow_path_vars[i].get().strip()
                if path:  # Only add if path is provided
                    workflow_configs.append({"name": name, "path": path})

            # Create settings object
            from src.models.application_settings import WorkflowConfig

            settings = ApplicationSettings(
                output_folder=self._output_folder_var.get().strip(),
                comfyui_endpoint=self._comfyui_endpoint_var.get().strip(),
                workflow_configs=[
                    WorkflowConfig(name=c["name"], path=c["path"])
                    for c in workflow_configs
                ],
                api_timeout=int(self._api_timeout_var.get().strip()),
                email_address=self._email_address_var.get().strip(),
            )

            # Validate settings
            settings.validate()

            # Save settings
            self._settings_service.save_settings(settings)

            self._result = settings
            self._settings_changed = True
            self._dialog.destroy()

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def _on_cancel(self) -> None:
        """Handle cancel button press."""
        self._result = None
        self._settings_changed = False
        self._dialog.destroy()

    def show(self) -> tuple[Optional[ApplicationSettings], bool]:
        """Show the dialog and return the result.

        Returns:
            Tuple of (settings, settings_changed)
        """
        self._dialog.wait_window()
        return self._result, self._settings_changed
