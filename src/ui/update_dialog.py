"""
Update dialog UI for Pomponio Ranch Labeling System.
Shows update availability, download progress, and handles installation.
"""

import customtkinter as ctk
from typing import Optional, Callable
from pathlib import Path

from ..updater import (
    ReleaseInfo, UpdateChecker, UpdateDownloader,
    get_current_version, apply_update, restart_application
)
from .theme import COLORS, FONTS


class UpdateDialog(ctk.CTkToplevel):
    """
    Modal dialog for handling application updates.
    """

    def __init__(
        self,
        parent,
        release: ReleaseInfo,
        on_close: Optional[Callable[[], None]] = None
    ):
        super().__init__(parent)

        self.release = release
        self.on_close = on_close
        self._downloader: Optional[UpdateDownloader] = None
        self._download_path: Optional[Path] = None

        # Window setup
        self.title("Update Available")
        self.geometry("500x400")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        self.geometry(f"+{x}+{y}")

        # Build UI
        self._build_ui()

        # Close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Build dialog UI."""
        # Main container
        container = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'])
        container.pack(fill='both', expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkFrame(container, fg_color='transparent')
        header.pack(fill='x', pady=(0, 20))

        ctk.CTkLabel(
            header,
            text="Update Available",
            font=('Segoe UI', 24, 'bold'),
            text_color=COLORS['text_primary']
        ).pack(anchor='w')

        # Version info
        version_frame = ctk.CTkFrame(container, fg_color=COLORS['bg_medium'], corner_radius=10)
        version_frame.pack(fill='x', pady=(0, 15))

        version_inner = ctk.CTkFrame(version_frame, fg_color='transparent')
        version_inner.pack(fill='x', padx=15, pady=12)

        ctk.CTkLabel(
            version_inner,
            text=f"Current version: {get_current_version()}",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        ).pack(anchor='w')

        ctk.CTkLabel(
            version_inner,
            text=f"New version: {self.release.version}",
            font=('Segoe UI', 16, 'bold'),
            text_color=COLORS['success']
        ).pack(anchor='w', pady=(5, 0))

        # Release name
        ctk.CTkLabel(
            version_inner,
            text=self.release.name,
            font=FONTS['body_sm'],
            text_color=COLORS['text_muted']
        ).pack(anchor='w')

        # Release notes
        notes_label = ctk.CTkLabel(
            container,
            text="Release Notes:",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        )
        notes_label.pack(anchor='w', pady=(0, 5))

        notes_box = ctk.CTkTextbox(
            container,
            font=FONTS['body_sm'],
            fg_color=COLORS['bg_medium'],
            text_color=COLORS['text_primary'],
            height=100,
            corner_radius=8
        )
        notes_box.pack(fill='x', pady=(0, 15))
        notes_box.insert('1.0', self.release.body or 'No release notes available.')
        notes_box.configure(state='disabled')

        # Progress area (hidden initially)
        self.progress_frame = ctk.CTkFrame(container, fg_color='transparent')

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Downloading...",
            font=FONTS['body'],
            text_color=COLORS['text_secondary']
        )
        self.progress_label.pack(anchor='w')

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            fg_color=COLORS['bg_medium'],
            progress_color=COLORS['primary'],
            height=20
        )
        self.progress_bar.pack(fill='x', pady=(5, 5))
        self.progress_bar.set(0)

        self.progress_detail = ctk.CTkLabel(
            self.progress_frame,
            text="0 MB / 0 MB",
            font=FONTS['body_sm'],
            text_color=COLORS['text_muted']
        )
        self.progress_detail.pack(anchor='w')

        # Status message (for errors/success)
        self.status_label = ctk.CTkLabel(
            container,
            text="",
            font=FONTS['body'],
            text_color=COLORS['text_primary']
        )

        # Buttons
        self.button_frame = ctk.CTkFrame(container, fg_color='transparent')
        self.button_frame.pack(fill='x', side='bottom')

        self.later_btn = ctk.CTkButton(
            self.button_frame,
            text="Later",
            font=FONTS['button'],
            fg_color='transparent',
            hover_color=COLORS['bg_light'],
            text_color=COLORS['text_secondary'],
            height=45,
            corner_radius=8,
            command=self._on_close
        )
        self.later_btn.pack(side='left')

        self.update_btn = ctk.CTkButton(
            self.button_frame,
            text="Download & Install",
            font=FONTS['button'],
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            text_color=COLORS['text_primary'],
            height=45,
            corner_radius=8,
            command=self._start_download
        )
        self.update_btn.pack(side='right')

    def _start_download(self):
        """Start downloading the update."""
        # Show progress
        self.progress_frame.pack(fill='x', pady=(0, 15))
        self.update_btn.configure(state='disabled', text="Downloading...")
        self.later_btn.configure(text="Cancel", command=self._cancel_download)

        # Start download
        self._downloader = UpdateDownloader(
            self.release,
            on_progress=self._on_progress,
            on_complete=self._on_download_complete,
            on_error=self._on_download_error
        )
        self._downloader.download_async()

    def _cancel_download(self):
        """Cancel download."""
        if self._downloader:
            self._downloader.cancel()
        self._on_close()

    def _on_progress(self, downloaded: int, total: int):
        """Update progress bar."""
        def update():
            if total > 0:
                progress = downloaded / total
                self.progress_bar.set(progress)

                dl_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                self.progress_detail.configure(
                    text=f"{dl_mb:.1f} MB / {total_mb:.1f} MB"
                )
            else:
                # Unknown total, show downloaded only
                dl_mb = downloaded / (1024 * 1024)
                self.progress_detail.configure(text=f"{dl_mb:.1f} MB downloaded")

        self.after(0, update)

    def _on_download_complete(self, zip_path: Path):
        """Handle download completion."""
        self._download_path = zip_path

        def update():
            self.progress_label.configure(text="Download complete. Installing...")
            self.progress_bar.set(1.0)
            self.later_btn.configure(state='disabled')

            # Apply update
            self.after(500, self._apply_update)

        self.after(0, update)

    def _on_download_error(self, error: str):
        """Handle download error."""
        def update():
            self.progress_frame.pack_forget()
            self.status_label.configure(
                text=f"Download failed: {error}",
                text_color=COLORS['error']
            )
            self.status_label.pack(pady=(0, 15))
            self.update_btn.configure(state='normal', text="Retry")
            self.later_btn.configure(text="Close", command=self._on_close)

        self.after(0, update)

    def _apply_update(self):
        """Apply the downloaded update."""
        if not self._download_path:
            return

        self.progress_label.configure(text="Installing update...")

        # Apply in thread to not block UI
        import threading

        def apply():
            success = apply_update(self._download_path)

            def finish():
                if success:
                    self.progress_label.configure(text="Update installed successfully.")
                    self.status_label.configure(
                        text="The application will now restart.",
                        text_color=COLORS['success']
                    )
                    self.status_label.pack(pady=(0, 15))
                    self.update_btn.configure(
                        text="Restart Now",
                        state='normal',
                        command=restart_application
                    )
                    self.later_btn.configure(
                        text="Restart Later",
                        state='normal',
                        command=self._on_close
                    )
                else:
                    self.progress_label.configure(text="Installation failed.")
                    self.status_label.configure(
                        text="Update could not be installed. Please try again later.",
                        text_color=COLORS['error']
                    )
                    self.status_label.pack(pady=(0, 15))
                    self.update_btn.configure(state='disabled')
                    self.later_btn.configure(
                        text="Close",
                        state='normal',
                        command=self._on_close
                    )

            self.after(0, finish)

        threading.Thread(target=apply, daemon=True).start()

    def _on_close(self):
        """Close dialog."""
        if self._downloader:
            self._downloader.cancel()

        self.grab_release()
        self.destroy()

        if self.on_close:
            self.on_close()


class UpdateCheckingDialog(ctk.CTkToplevel):
    """
    Small dialog shown while checking for updates.
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.title("")
        self.geometry("300x100")
        self.resizable(False, False)
        self.overrideredirect(True)  # No window decorations

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 300) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 100) // 2
        self.geometry(f"+{x}+{y}")

        # Build UI
        container = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], corner_radius=10)
        container.pack(fill='both', expand=True, padx=2, pady=2)

        ctk.CTkLabel(
            container,
            text="Checking for updates...",
            font=FONTS['body'],
            text_color=COLORS['text_primary']
        ).pack(expand=True)

        # Make modal
        self.transient(parent)
        self.grab_set()


def check_for_updates_ui(
    parent,
    on_no_update: Optional[Callable[[], None]] = None,
    silent: bool = False
):
    """
    Check for updates with UI feedback.

    Args:
        parent: Parent window
        on_no_update: Callback if no update available
        silent: If True, don't show dialog when no update
    """
    checking_dialog = None if silent else UpdateCheckingDialog(parent)

    def on_update_available(release: ReleaseInfo):
        def show():
            if checking_dialog:
                checking_dialog.destroy()
            UpdateDialog(parent, release)

        parent.after(0, show)

    def on_no_update_found():
        def show():
            if checking_dialog:
                checking_dialog.destroy()
            if on_no_update:
                on_no_update()
            elif not silent:
                # Show brief message
                dialog = ctk.CTkToplevel(parent)
                dialog.title("No Updates")
                dialog.geometry("300x120")
                dialog.resizable(False, False)
                dialog.transient(parent)
                dialog.grab_set()

                # Center
                dialog.update_idletasks()
                x = parent.winfo_x() + (parent.winfo_width() - 300) // 2
                y = parent.winfo_y() + (parent.winfo_height() - 120) // 2
                dialog.geometry(f"+{x}+{y}")

                ctk.CTkLabel(
                    dialog,
                    text="You're up to date.",
                    font=FONTS['body'],
                    text_color=COLORS['text_primary']
                ).pack(expand=True)

                ctk.CTkButton(
                    dialog,
                    text="OK",
                    font=FONTS['button'],
                    fg_color=COLORS['primary'],
                    command=dialog.destroy,
                    height=35,
                    width=80
                ).pack(pady=(0, 15))

        parent.after(0, show)

    def on_error(error: str):
        def show():
            if checking_dialog:
                checking_dialog.destroy()
            if not silent:
                print(f"Update check error: {error}")

        parent.after(0, show)

    # Run check
    checker = UpdateChecker(
        on_update_available=on_update_available,
        on_no_update=on_no_update_found,
        on_error=on_error
    )
    checker.check_async()
