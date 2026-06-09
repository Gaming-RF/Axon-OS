import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import St from 'gi://St';
import Shell from 'gi://Shell';
import Meta from 'gi://Meta';
import Clutter from 'gi://Clutter';
import Gio from 'gi://Gio';
import Soup from 'gi://Soup?version=3.0';

import { Extension } from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';

import SpacesManager from './spaces.js';
import IntentBar from './intentbar.js';

// ─── AxonAIIndicator ──────────────────────────────────────────────────────────

const AxonAIIndicator = GObject.registerClass(
class AxonAIIndicator extends PanelMenu.Button {
    _init(extension) {
        super._init(0.0, 'Axon AI Indicator', false);

        this._extension = extension;
        this._pollTimerId = null;
        this._soupSession = null;

        // Build UI: "⬡ AI" label + status dot
        const box = new St.BoxLayout({
            style_class: 'axon-ai-indicator',
            vertical: false,
            x_align: Clutter.ActorAlign.CENTER,
            y_align: Clutter.ActorAlign.CENTER,
        });

        this._iconLabel = new St.Label({
            style_class: 'axon-ai-indicator-icon',
            text: '⬡ AI',
            y_align: Clutter.ActorAlign.CENTER,
            style: [
                'font-family: "Inter", "Ubuntu", system-ui, sans-serif;',
                'font-size: 12px;',
                'font-weight: 600;',
                'color: #8b5cf6;',
                'margin-right: 5px;',
            ].join(' '),
        });

        this._statusDot = new St.Label({
            style_class: 'axon-ai-indicator-dot',
            text: '●',
            y_align: Clutter.ActorAlign.CENTER,
            style: 'color: #ef4444; font-size: 10px;', // default: red (unreachable)
        });

        box.add_child(this._iconLabel);
        box.add_child(this._statusDot);
        this.add_child(box);

        // Initialise Soup session and do a first health check
        try {
            this._soupSession = new Soup.Session();
        } catch (e) {
            console.warn('AxonShell: could not create Soup.Session:', e.message);
        }

        this._checkOllamaHealth();

        // Poll every 30 seconds
        this._pollTimerId = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT,
            30,
            this._checkOllamaHealth.bind(this)
        );
    }

    _checkOllamaHealth() {
        if (!this._soupSession) return GLib.SOURCE_CONTINUE;

        try {
            const message = Soup.Message.new('GET', 'http://localhost:11434/api/tags');
            if (!message) {
                this._setDotColor(false);
                return GLib.SOURCE_CONTINUE;
            }

            this._soupSession.send_and_read_async(
                message,
                GLib.PRIORITY_DEFAULT,
                null,
                (session, result) => {
                    try {
                        session.send_and_read_finish(result);
                        const status = message.get_status();
                        this._setDotColor(
                            status === Soup.Status.OK || status === 200
                        );
                    } catch (e) {
                        this._setDotColor(false);
                    }
                }
            );
        } catch (e) {
            console.warn('AxonShell: Ollama health check failed:', e.message);
            this._setDotColor(false);
        }

        return GLib.SOURCE_CONTINUE;
    }

    _setDotColor(online) {
        const color = online ? '#10b981' : '#ef4444';
        this._statusDot.set_style(`color: ${color}; font-size: 10px;`);
    }

    destroy() {
        if (this._pollTimerId) {
            GLib.source_remove(this._pollTimerId);
            this._pollTimerId = null;
        }
        if (this._soupSession) {
            this._soupSession.abort();
            this._soupSession = null;
        }
        super.destroy();
    }
});

// ─── AxonShellExtension ───────────────────────────────────────────────────────

export default class AxonShellExtension extends Extension {
    constructor(metadata) {
        super(metadata);
        this._spacesManager = null;
        this._intentBar = null;
        this._aiIndicator = null;
        this._keybindingIds = [];
    }

    enable() {
        this._spacesManager = new SpacesManager(this);
        this._spacesManager.enable();

        this._intentBar = new IntentBar(this, this._spacesManager);
        this._intentBar.enable();

        this._aiIndicator = new AxonAIIndicator(this);
        Main.panel.addToStatusArea('axon-ai-indicator', this._aiIndicator, 0, 'right');

        this._registerKeybindings();
    }

    _registerKeybindings() {
        const settings = this.getSettings();

        // Super+1..9 to switch spaces
        for (let i = 1; i <= 9; i++) {
            const spaceIndex = i - 1;
            const bindingName = `switch-to-space-${i}`;
            try {
                Main.wm.addKeybinding(
                    bindingName,
                    settings,
                    Meta.KeyBindingFlags.NONE,
                    Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW,
                    () => {
                        this._spacesManager.switchToSpace(spaceIndex);
                    }
                );
                this._keybindingIds.push(bindingName);
            } catch (e) {
                console.warn(`AxonShell: could not bind ${bindingName}:`, e.message);
            }
        }

        // Super+Space → toggle intent bar
        try {
            Main.wm.addKeybinding(
                'toggle-intent-bar',
                settings,
                Meta.KeyBindingFlags.NONE,
                Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW,
                () => {
                    this._intentBar.toggle();
                }
            );
            this._keybindingIds.push('toggle-intent-bar');
        } catch (e) {
            console.warn('AxonShell: could not bind toggle-intent-bar:', e.message);
        }

        // Super+A → toggle AI panel
        try {
            Main.wm.addKeybinding(
                'toggle-ai-panel',
                settings,
                Meta.KeyBindingFlags.NONE,
                Shell.ActionMode.NORMAL | Shell.ActionMode.OVERVIEW,
                () => {
                    this._toggleAIPanel();
                }
            );
            this._keybindingIds.push('toggle-ai-panel');
        } catch (e) {
            console.warn('AxonShell: could not bind toggle-ai-panel:', e.message);
        }
    }

    _toggleAIPanel() {
        try {
            const panelScript = GLib.build_filenamev([
                GLib.get_home_dir(),
                '.local', 'share', 'axon-os', 'axon-ai-panel', 'main.py',
            ]);
            const proc = Gio.Subprocess.new(
                ['python3', panelScript],
                Gio.SubprocessFlags.NONE
            );
            proc.wait_async(null, (subprocess, result) => {
                try {
                    subprocess.wait_finish(result);
                } catch (e) {
                    console.warn('AxonShell: AI panel process error:', e.message);
                }
            });
        } catch (e) {
            console.warn('AxonShell: could not launch AI panel:', e.message);
        }
    }

    disable() {
        // Remove all registered keybindings
        for (const id of this._keybindingIds) {
            try {
                Main.wm.removeKeybinding(id);
            } catch (e) {
                console.warn(`AxonShell: could not remove keybinding ${id}:`, e.message);
            }
        }
        this._keybindingIds = [];

        if (this._aiIndicator) {
            this._aiIndicator.destroy();
            this._aiIndicator = null;
        }

        if (this._intentBar) {
            this._intentBar.disable();
            this._intentBar = null;
        }

        if (this._spacesManager) {
            this._spacesManager.disable();
            this._spacesManager = null;
        }
    }
}
