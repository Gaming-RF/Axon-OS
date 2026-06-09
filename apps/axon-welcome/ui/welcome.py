"""Axon OS Welcome App — WelcomeWindow (4-page onboarding wizard)."""

import os
import shutil
import subprocess
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib, Gtk

# ---------------------------------------------------------------------------
# Embedded CSS
# ---------------------------------------------------------------------------

_CSS = b"""
.welcome-window {
    background-color: #09090f;
}
.hero-logo {
    font-size: 52px;
    color: #8b5cf6;
}
.hero-title {
    font-size: 32px;
    font-weight: bold;
    color: #e8e8f4;
}
.hero-subtitle {
    font-size: 16px;
    color: #9090b8;
}
.chip {
    background-color: rgba(139, 92, 246, 0.18);
    color: #8b5cf6;
    border-radius: 9999px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: bold;
    border: 1px solid rgba(139, 92, 246, 0.35);
}
.feature-card {
    background-color: #111119;
    border-radius: 16px;
    border: 1px solid #2a2a42;
    padding: 20px;
}
.feature-icon {
    font-size: 32px;
}
.feature-title {
    font-size: 14px;
    font-weight: bold;
    color: #e8e8f4;
}
.feature-desc {
    font-size: 12px;
    color: #9090b8;
}
.model-row {
    background-color: #111119;
    border-radius: 12px;
    border: 1px solid #2a2a42;
    padding: 12px 16px;
}
.model-name {
    font-size: 14px;
    font-weight: bold;
    color: #e8e8f4;
}
.model-desc {
    font-size: 12px;
    color: #9090b8;
}
.model-size {
    font-size: 11px;
    color: #50507a;
}
.page-title {
    font-size: 24px;
    font-weight: bold;
    color: #e8e8f4;
}
.page-subtitle {
    font-size: 14px;
    color: #9090b8;
}
.nav-btn-next {
    background-color: #8b5cf6;
    color: white;
    border-radius: 9999px;
    border: none;
    padding: 10px 28px;
    font-size: 15px;
}
.nav-btn-next:hover {
    background-color: #7c3aed;
}
.nav-btn-back {
    background-color: transparent;
    color: #9090b8;
    border: 1px solid #3a3a58;
    border-radius: 9999px;
    padding: 10px 22px;
}
.page-indicator-dot {
    font-size: 8px;
}
.check-icon {
    font-size: 64px;
    color: #10b981;
}
.status-online {
    color: #10b981;
    font-size: 12px;
}
.status-offline {
    color: #ef4444;
    font-size: 12px;
}
"""

# ---------------------------------------------------------------------------
# Helper: apply CSS class safely
# ---------------------------------------------------------------------------

def _add_class(widget: Gtk.Widget, css_class: str) -> None:
    widget.get_style_context().add_class(css_class)


def _remove_class(widget: Gtk.Widget, css_class: str) -> None:
    widget.get_style_context().remove_class(css_class)


# ---------------------------------------------------------------------------
# WelcomeWindow
# ---------------------------------------------------------------------------

class WelcomeWindow(Adw.Window):
    _PAGE_NAMES = ["welcome", "setup", "features", "ready"]

    def __init__(self, app: Adw.Application):
        super().__init__(application=app)

        # --- Window properties ---
        self.set_title("Welcome to Axon OS")
        self.set_default_size(640, 560)
        self.set_decorated(True)

        # --- Load CSS ---
        provider = Gtk.CssProvider()
        provider.load_from_data(_CSS)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        # --- Root layout ---
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        _add_class(root_box, "welcome-window")

        clamp = Adw.Clamp()
        clamp.set_maximum_size(560)
        clamp.set_vexpand(True)

        # Main stack
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self._stack.set_vexpand(True)

        # Page indicator
        self._dot_labels: list[Gtk.Label] = []
        indicator_row = self._build_indicator()

        # Build pages
        self._stack.add_named(self._build_page_welcome(), "welcome")
        self._stack.add_named(self._build_page_setup(), "setup")
        self._stack.add_named(self._build_page_features(), "features")
        self._stack.add_named(self._build_page_ready(), "ready")

        inner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        inner_box.append(self._stack)
        inner_box.append(indicator_row)

        clamp.set_child(inner_box)
        root_box.append(clamp)
        self.set_content(root_box)

        # Track current page index
        self._current_page = 0
        self._update_indicator()

        # Start Ollama check in background
        t = threading.Thread(target=self._check_ollama, daemon=True)
        t.start()

    # ------------------------------------------------------------------
    # Page indicator
    # ------------------------------------------------------------------

    def _build_indicator(self) -> Gtk.Box:
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.set_halign(Gtk.Align.CENTER)
        row.set_margin_bottom(16)
        row.set_margin_top(6)

        for _ in self._PAGE_NAMES:
            dot = Gtk.Label(label="●")
            _add_class(dot, "page-indicator-dot")
            dot.set_opacity(0.3)
            self._dot_labels.append(dot)
            row.append(dot)

        return row

    def _update_indicator(self) -> None:
        for i, dot in enumerate(self._dot_labels):
            if i == self._current_page:
                dot.set_opacity(1.0)
                dot.set_markup('<span color="#8b5cf6">●</span>')
            else:
                dot.set_opacity(0.3)
                dot.set_markup('<span color="#50507a">●</span>')

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _go_to(self, page_name: str) -> None:
        idx = self._PAGE_NAMES.index(page_name)
        current_idx = self._current_page

        if idx > current_idx:
            self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        else:
            self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)

        self._stack.set_visible_child_name(page_name)
        self._current_page = idx
        self._update_indicator()

    # ------------------------------------------------------------------
    # PAGE 1 — Welcome
    # ------------------------------------------------------------------

    def _build_page_welcome(self) -> Gtk.Box:
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        page.set_halign(Gtk.Align.CENTER)
        page.set_valign(Gtk.Align.FILL)
        page.set_margin_top(40)
        page.set_margin_bottom(24)
        page.set_margin_start(40)
        page.set_margin_end(40)

        # Hero logo glyph
        logo = Gtk.Label(label="⬡")
        _add_class(logo, "hero-logo")
        logo.set_margin_bottom(8)
        page.append(logo)

        # Title
        title = Gtk.Label(label="Welcome to Axon OS")
        _add_class(title, "hero-title")
        title.set_wrap(True)
        title.set_justify(Gtk.Justification.CENTER)
        page.append(title)

        # Subtitle
        subtitle = Gtk.Label(label="Your AI-native desktop. Fully private. Entirely local.")
        _add_class(subtitle, "hero-subtitle")
        subtitle.set_wrap(True)
        subtitle.set_justify(Gtk.Justification.CENTER)
        page.append(subtitle)

        # Chips
        chips_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        chips_row.set_halign(Gtk.Align.CENTER)
        chips_row.set_margin_top(20)
        for chip_text in ["100% Local AI", "Zero Cloud", "GNOME Native"]:
            chip = Gtk.Label(label=chip_text)
            _add_class(chip, "chip")
            chips_row.append(chip)
        page.append(chips_row)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        page.append(spacer)

        # Get Started button
        btn = Gtk.Button(label="Get Started")
        _add_class(btn, "nav-btn-next")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda _: self._go_to("setup"))
        page.append(btn)

        return page

    # ------------------------------------------------------------------
    # PAGE 2 — Setup
    # ------------------------------------------------------------------

    def _build_page_setup(self) -> Gtk.Box:
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(32)
        page.set_margin_bottom(24)
        page.set_margin_start(32)
        page.set_margin_end(32)

        # Title
        title = Gtk.Label(label="Set Up Your AI")
        _add_class(title, "page-title")
        title.set_halign(Gtk.Align.START)
        page.append(title)

        subtitle = Gtk.Label(label="Axon runs AI models locally on your hardware.")
        _add_class(subtitle, "page-subtitle")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.set_wrap(True)
        page.append(subtitle)

        # Ollama status row
        ollama_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ollama_row.set_margin_top(8)
        ollama_lbl = Gtk.Label(label="Ollama")
        _add_class(ollama_lbl, "model-name")
        ollama_row.append(ollama_lbl)

        status_spacer = Gtk.Box()
        status_spacer.set_hexpand(True)
        ollama_row.append(status_spacer)

        self._ollama_status_label = Gtk.Label(label="Checking…")
        self._ollama_status_label.set_halign(Gtk.Align.END)
        ollama_row.append(self._ollama_status_label)
        page.append(ollama_row)

        # Model rows — radio group
        models = [
            ("llama3.2:3b", "Fast — great for everyday tasks", "~2 GB"),
            ("mistral:7b", "Balanced — excellent for coding", "~4 GB"),
            ("qwen2.5:7b", "Multilingual — best quality", "~4 GB"),
            ("deepseek-r1:8b", "Reasoning specialist", "~5 GB"),
        ]

        self._model_checks: list[Gtk.CheckButton] = []
        self._selected_model = models[0][0]
        first_check = None

        for model_id, model_desc, model_size in models:
            outer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
            _add_class(outer, "model-row")

            check = Gtk.CheckButton()
            if first_check is None:
                first_check = check
                check.set_active(True)
            else:
                check.set_group(first_check)

            # Label box inside the checkbutton area
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            inner.set_hexpand(True)

            name_lbl = Gtk.Label(label=model_id)
            _add_class(name_lbl, "model-name")
            name_lbl.set_halign(Gtk.Align.START)
            inner.append(name_lbl)

            desc_lbl = Gtk.Label(label=model_desc)
            _add_class(desc_lbl, "model-desc")
            desc_lbl.set_halign(Gtk.Align.START)
            inner.append(desc_lbl)

            size_lbl = Gtk.Label(label=model_size)
            _add_class(size_lbl, "model-size")
            size_lbl.set_halign(Gtk.Align.START)
            inner.append(size_lbl)

            check.set_child(inner)

            captured_id = model_id

            def _on_toggled(btn, mid=captured_id):
                if btn.get_active():
                    self._selected_model = mid

            check.connect("toggled", _on_toggled)
            self._model_checks.append(check)
            outer.append(check)
            page.append(outer)

        # Pull button + progress bar
        self._pull_btn = Gtk.Button(label="Pull Selected Model")
        _add_class(self._pull_btn, "nav-btn-next")
        self._pull_btn.set_halign(Gtk.Align.CENTER)
        self._pull_btn.set_margin_top(8)
        self._pull_btn.connect("clicked", self._on_pull_clicked)
        page.append(self._pull_btn)

        self._pull_progress = Gtk.ProgressBar()
        self._pull_progress.set_visible(False)
        self._pull_progress.set_margin_top(4)
        page.append(self._pull_progress)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        page.append(spacer)

        # Nav row
        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        nav.set_halign(Gtk.Align.CENTER)

        back_btn = Gtk.Button(label="← Back")
        _add_class(back_btn, "nav-btn-back")
        back_btn.connect("clicked", lambda _: self._go_to("welcome"))
        nav.append(back_btn)

        skip_btn = Gtk.Button(label="Skip")
        _add_class(skip_btn, "nav-btn-back")
        skip_btn.connect("clicked", lambda _: self._go_to("features"))
        nav.append(skip_btn)

        continue_btn = Gtk.Button(label="Continue →")
        _add_class(continue_btn, "nav-btn-next")
        continue_btn.connect("clicked", lambda _: self._go_to("features"))
        nav.append(continue_btn)

        page.append(nav)

        return page

    # ------------------------------------------------------------------
    # PAGE 3 — Features
    # ------------------------------------------------------------------

    def _build_page_features(self) -> Gtk.Box:
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(32)
        page.set_margin_bottom(24)
        page.set_margin_start(32)
        page.set_margin_end(32)

        title = Gtk.Label(label="What Axon Can Do")
        _add_class(title, "page-title")
        title.set_halign(Gtk.Align.START)
        page.append(title)

        # Feature grid 2x2
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(12)
        grid.set_margin_top(8)

        feature_data = [
            ("⬡", "Intent Bar", "Press Super+Space. Ask anything in natural language."),
            ("🤖", "AI Panel", "Press Super+A. Your persistent AI assistant."),
            ("🏠", "Spaces", "Super+1-9. Named workspaces for each project."),
            ("🔒", "Private", "All AI runs locally. Zero data leaves your machine."),
        ]

        positions = [(0, 0), (1, 0), (0, 1), (1, 1)]

        for (icon, feat_title, feat_desc), (col, row) in zip(feature_data, positions):
            card = self._build_feature_card(icon, feat_title, feat_desc)
            grid.attach(card, col, row, 1, 1)

        page.append(grid)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        page.append(spacer)

        # Nav row
        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        nav.set_halign(Gtk.Align.CENTER)

        back_btn = Gtk.Button(label="← Back")
        _add_class(back_btn, "nav-btn-back")
        back_btn.connect("clicked", lambda _: self._go_to("setup"))
        nav.append(back_btn)

        next_btn = Gtk.Button(label="Next →")
        _add_class(next_btn, "nav-btn-next")
        next_btn.connect("clicked", lambda _: self._go_to("ready"))
        nav.append(next_btn)

        page.append(nav)

        return page

    def _build_feature_card(self, icon: str, feat_title: str, feat_desc: str) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.set_hexpand(True)
        _add_class(card, "feature-card")

        icon_lbl = Gtk.Label(label=icon)
        _add_class(icon_lbl, "feature-icon")
        icon_lbl.set_halign(Gtk.Align.START)
        card.append(icon_lbl)

        title_lbl = Gtk.Label(label=feat_title)
        _add_class(title_lbl, "feature-title")
        title_lbl.set_halign(Gtk.Align.START)
        card.append(title_lbl)

        desc_lbl = Gtk.Label(label=feat_desc)
        _add_class(desc_lbl, "feature-desc")
        desc_lbl.set_halign(Gtk.Align.START)
        desc_lbl.set_wrap(True)
        desc_lbl.set_xalign(0.0)
        card.append(desc_lbl)

        return card

    # ------------------------------------------------------------------
    # PAGE 4 — Ready
    # ------------------------------------------------------------------

    def _build_page_ready(self) -> Gtk.Box:
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page.set_halign(Gtk.Align.CENTER)
        page.set_valign(Gtk.Align.FILL)
        page.set_margin_top(40)
        page.set_margin_bottom(24)
        page.set_margin_start(40)
        page.set_margin_end(40)

        check_lbl = Gtk.Label(label="✓")
        _add_class(check_lbl, "check-icon")
        check_lbl.set_margin_bottom(4)
        page.append(check_lbl)

        title = Gtk.Label(label="You're All Set!")
        _add_class(title, "page-title")
        title.set_justify(Gtk.Justification.CENTER)
        page.append(title)

        subtitle = Gtk.Label(label="Try Super+Space to open the Intent Bar.")
        _add_class(subtitle, "page-subtitle")
        subtitle.set_justify(Gtk.Justification.CENTER)
        subtitle.set_wrap(True)
        page.append(subtitle)

        # Show on startup toggle
        toggle_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        toggle_row.set_halign(Gtk.Align.CENTER)
        toggle_row.set_margin_top(16)

        toggle_lbl = Gtk.Label(label="Show on startup:")
        _add_class(toggle_lbl, "page-subtitle")
        toggle_row.append(toggle_lbl)

        switch = Gtk.Switch()
        switch.set_active(True)
        switch.connect("state-set", self._on_startup_toggle)
        toggle_row.append(switch)

        page.append(toggle_row)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        page.append(spacer)

        # Nav row
        nav = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        nav.set_halign(Gtk.Align.CENTER)

        back_btn = Gtk.Button(label="← Back")
        _add_class(back_btn, "nav-btn-back")
        back_btn.connect("clicked", lambda _: self._go_to("features"))
        nav.append(back_btn)

        start_btn = Gtk.Button(label="Start Using Axon")
        _add_class(start_btn, "nav-btn-next")
        start_btn.connect("clicked", lambda _: self.close())
        nav.append(start_btn)

        page.append(nav)

        return page

    # ------------------------------------------------------------------
    # Ollama background check
    # ------------------------------------------------------------------

    def _check_ollama(self) -> None:
        found = shutil.which("ollama") is not None
        GLib.idle_add(self._on_ollama_checked, found)

    def _on_ollama_checked(self, found: bool) -> bool:
        if found:
            self._ollama_status_label.set_text("● Installed")
            _remove_class(self._ollama_status_label, "status-offline")
            _add_class(self._ollama_status_label, "status-online")
        else:
            self._ollama_status_label.set_text("● Not Found")
            _remove_class(self._ollama_status_label, "status-online")
            _add_class(self._ollama_status_label, "status-offline")
        return GLib.SOURCE_REMOVE

    # ------------------------------------------------------------------
    # Pull model
    # ------------------------------------------------------------------

    def _on_pull_clicked(self, _btn: Gtk.Button) -> None:
        model = self._selected_model
        self._pull_btn.set_sensitive(False)
        self._pull_progress.set_visible(True)
        self._pull_progress.pulse()

        def _do_pull():
            try:
                subprocess.run(
                    ["ollama", "pull", model],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                GLib.idle_add(self._on_pull_done, True)
            except Exception:
                GLib.idle_add(self._on_pull_done, False)

        # Pulse the progress bar while pulling
        def _pulse_tick():
            if self._pull_progress.get_visible():
                self._pull_progress.pulse()
                return GLib.SOURCE_CONTINUE
            return GLib.SOURCE_REMOVE

        GLib.timeout_add(300, _pulse_tick)

        t = threading.Thread(target=_do_pull, daemon=True)
        t.start()

    def _on_pull_done(self, success: bool) -> bool:
        self._pull_progress.set_visible(False)
        self._pull_btn.set_sensitive(True)
        if success:
            self._pull_btn.set_label("✓ Model Ready")
        else:
            self._pull_btn.set_label("Pull Failed — Retry")
        return GLib.SOURCE_REMOVE

    # ------------------------------------------------------------------
    # Startup toggle
    # ------------------------------------------------------------------

    def _on_startup_toggle(self, switch: Gtk.Switch, state: bool) -> bool:
        config_dir = os.path.expanduser("~/.config/axon-os")
        marker = os.path.join(config_dir, ".firstboot-done")
        if state:
            # Show on startup → remove the "done" marker so it shows again
            if os.path.exists(marker):
                try:
                    os.remove(marker)
                except OSError:
                    pass
        else:
            # Do not show on startup → create the marker
            os.makedirs(config_dir, exist_ok=True)
            try:
                with open(marker, "w") as f:
                    f.write("")
            except OSError:
                pass
        return False
