#!/usr/bin/env python3
"""
Axon OS Desktop Preview Generator
Generates a 1920x1080 pixel-perfect desktop preview image.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math
import os

# ─── Constants ────────────────────────────────────────────────────────────────
W, H = 1920, 1080
OUT_PATH = os.path.join(os.path.dirname(__file__), "desktop-preview.png")

# Fonts
FONT_DIR_SG   = "/usr/share/fonts/truetype/space-grotesk-zorin-os"
FONT_DIR_DEJA = "/usr/share/fonts/truetype/dejavu"
FONT_DIR_MONO = "/usr/share/fonts/truetype/liberation"

def load_font(size, bold=False):
    try:
        path = f"{FONT_DIR_SG}/SpaceGrotesk-{'Bold' if bold else 'Regular'}.ttf"
        return ImageFont.truetype(path, size)
    except:
        try:
            path = f"{FONT_DIR_DEJA}/DejaVuSans{'-Bold' if bold else ''}.ttf"
            return ImageFont.truetype(path, size)
        except:
            return ImageFont.load_default()

def load_mono(size, bold=False):
    try:
        path = f"{FONT_DIR_MONO}/LiberationMono{'-Bold' if bold else '-Regular'}.ttf"
        return ImageFont.truetype(path, size)
    except:
        return load_font(size, bold)

# ─── Color Palette ────────────────────────────────────────────────────────────
C = {
    "bg_dark":      (9,   9,  15),
    "bg_mid":      (15,  10,  30),
    "menubar":     (10,  10,  20),
    "menubar_border": (30, 30, 48),
    "window_bg":   (13,  13,  26),
    "window_title":(17,  17,  25),
    "dock_bg":     (17,  17,  25),
    "dock_border": (40,  40,  60),
    "violet":      (139, 92, 246),
    "violet_dim":  (80,  50, 160),
    "cyan":        (34, 211, 238),
    "green":       (74, 222, 128),
    "white":       (255,255,255),
    "gray":        (160,160,180),
    "dim":         (100,100,120),
    "panel_bg":    (12,  12,  22),
    "intent_bg":   (9,   9,  15),
    "chip_bg":     (25,  25,  45),
    "chip_border": (50,  50,  80),
    "bubble_user": (50,  35, 100),
    "bubble_ai":   (20,  20,  38),
    "red":         (255, 95, 87),
    "yellow":      (255,189, 46),
    "green_btn":   (40, 200, 65),
    "code_kw":     (139, 92, 246),
    "code_str":    (74, 222, 128),
    "code_fn":     (96, 165, 250),
    "code_comment":(80, 100, 120),
    "code_num":    (251,191,  36),
    "code_op":     (248,113,113),
    "scrollbar":   (40,  40,  65),
}

def rgba(c, a=255):
    if len(c) == 3:
        return c + (a,)
    return c

# ─── Helpers ──────────────────────────────────────────────────────────────────

def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = xy
    if fill:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)
    else:
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=outline, width=width)

def text_center(draw, text, cx, y, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    draw.text((cx - tw//2, y), text, font=font, fill=fill)

def text_right(draw, text, rx, y, font, fill):
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    draw.text((rx - tw, y), text, font=font, fill=fill)

def draw_circle(draw, cx, cy, r, fill, outline=None, width=1):
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=fill, outline=outline, width=width)

def hex_icon(draw, cx, cy, size, fill):
    """Draw a hexagon icon."""
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
    draw.polygon(pts, fill=fill)

def hex_outline(draw, cx, cy, size, outline, width=2):
    pts = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        pts.append((cx + size * math.cos(angle), cy + size * math.sin(angle)))
    draw.polygon(pts, outline=outline, width=width)

# ─── Background ───────────────────────────────────────────────────────────────

def draw_background(img):
    draw = ImageDraw.Draw(img)
    # Base dark gradient (top to bottom)
    for y in range(H):
        t = y / H
        r = int(9  + (15-9)  * t)
        g = int(9  + (10-9)  * t)
        b = int(15 + (30-15) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Subtle radial purple glow in center
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = W // 2, H // 2 + 80
    for radius in range(420, 0, -4):
        alpha = int(28 * (1 - radius / 420) ** 2.2)
        gd.ellipse(
            [cx - radius, cy - int(radius * 0.55),
             cx + radius, cy + int(radius * 0.55)],
            fill=(90, 30, 160, alpha)
        )
    img.paste(glow, (0, 0), glow)

    # Tiny star field
    import random
    rng = random.Random(42)
    for _ in range(180):
        sx = rng.randint(0, W-1)
        sy = rng.randint(32, H - 100)
        alpha = rng.randint(40, 160)
        size = rng.choice([1, 1, 1, 2])
        draw.ellipse([sx, sy, sx+size, sy+size], fill=(255, 255, 255, alpha))

# ─── Menu Bar ─────────────────────────────────────────────────────────────────

def draw_menubar(img):
    draw = ImageDraw.Draw(img)
    # Background
    draw.rectangle([0, 0, W, 32], fill=C["menubar"])
    # Bottom border
    draw.line([(0, 32), (W, 32)], fill=C["menubar_border"])

    f_sm   = load_font(12)
    f_sm_b = load_font(13, bold=True)
    f_icon = load_font(14, bold=True)

    # Left: Axon logo hex + name
    hex_icon(draw, 18, 16, 8, C["violet"])
    draw.text((32, 5), "Axon", font=f_sm_b, fill=C["white"])

    # Menu items
    items = ["File", "Edit", "View", "Go", "Window", "Help"]
    x = 82
    for item in items:
        draw.text((x, 9), item, font=f_sm, fill=(200, 200, 215))
        bb = draw.textbbox((0, 0), item, font=f_sm)
        x += bb[2] - bb[0] + 20

    # Right side elements
    rx = W - 12
    clock_text = "Mon 09 Jun  9:32 AM"
    f_clock = load_font(12)
    bb = draw.textbbox((0, 0), clock_text, font=f_clock)
    tw = bb[2] - bb[0]
    draw.text((rx - tw, 9), clock_text, font=f_clock, fill=(220, 220, 230))
    rx -= tw + 22

    # AI status
    ai_text = "⬡ AI"
    bb = draw.textbbox((0, 0), ai_text, font=f_sm_b)
    tw = bb[2] - bb[0]
    draw.text((rx - tw - 14, 9), ai_text, font=f_sm_b, fill=C["violet"])
    # green dot
    draw_circle(draw, rx - 4, 16, 4, C["green"])
    rx -= tw + 30

    # Battery (simple pill)
    draw.rounded_rectangle([rx-34, 10, rx-4, 22], radius=3, outline=(180,180,200), width=1)
    draw.rectangle([rx-34+2, 12, rx-34+2+20, 20], fill=(74, 222, 128))
    draw.rectangle([rx-3, 13, rx, 19], fill=(180,180,200))
    rx -= 52

    # Wifi arcs
    wc = rx - 10
    wy = 20
    for i, (sz, al) in enumerate([(3,255),(6,200),(9,140)]):
        a_col = (200,200,220, al)
        draw.arc([wc-sz, wy-sz, wc+sz, wy+sz], start=200, end=340,
                 fill=(200,200,220), width=1)
    draw_circle(draw, wc, wy+2, 1, (200,200,220))

# ─── Window Helper ────────────────────────────────────────────────────────────

def draw_window_frame(img_layer, x, y, w, h, title, radius=12):
    draw = ImageDraw.Draw(img_layer)
    # Shadow
    for i in range(18, 0, -1):
        alpha = int(80 * (i/18)**2)
        shadow = Image.new("RGBA", img_layer.size, (0,0,0,0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle([x+i, y+i, x+w+i, y+h+i], radius=radius,
                              fill=(0,0,0,alpha))
        img_layer.paste(shadow, (0,0), shadow)

    # Window body
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=C["window_bg"])
    # Titlebar
    draw.rounded_rectangle([x, y, x+w, y+36], radius=radius, fill=C["window_title"])
    draw.rectangle([x, y+24, x+w, y+36], fill=C["window_title"])
    # Bottom part fill (fix rounded corners showing bg)
    draw.rectangle([x, y+h-radius, x+w, y+h], fill=C["window_bg"])
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, outline=C["dock_border"], width=1)

    # Traffic lights
    draw_circle(draw, x+18, y+18, 6, C["red"])
    draw_circle(draw, x+38, y+18, 6, C["yellow"])
    draw_circle(draw, x+58, y+18, 6, C["green_btn"])

    # Title
    f = load_font(12)
    text_center(draw, title, x + w//2, y + 10, f, (180,180,200))

    return draw

# ─── Code Editor Window ───────────────────────────────────────────────────────

def draw_code_editor(img, x, y, w, h):
    layer = img.copy().convert("RGBA")
    draw = draw_window_frame(layer, x, y, w, h, "main.py — Axon OS", radius=12)

    # Tabs bar
    tabs_y = y + 36
    draw.rectangle([x, tabs_y, x+w, tabs_y+28], fill=(11,11,20))
    tabs = ["main.py", "ai_core.py", "intent_bar.py", "config.toml"]
    tx = x + 8
    f_tab = load_font(11)
    for i, tab in enumerate(tabs):
        bb = draw.textbbox((0,0), tab, font=f_tab)
        tw = bb[2]-bb[0]
        if i == 0:
            draw.rounded_rectangle([tx-6, tabs_y+4, tx+tw+6, tabs_y+24],
                                    radius=4, fill=C["window_bg"])
            draw.text((tx, tabs_y+7), tab, font=f_tab, fill=(220,220,235))
        else:
            draw.text((tx, tabs_y+7), tab, font=f_tab, fill=C["dim"])
        tx += tw + 22

    # Line numbers + code area
    code_y = tabs_y + 28
    line_w = 42
    draw.rectangle([x, code_y, x+line_w, y+h], fill=(10,10,18))
    draw.rectangle([x+line_w, code_y, x+w, y+h], fill=C["window_bg"])
    draw.line([(x+line_w, code_y), (x+line_w, y+h)], fill=(25,25,45))

    f_code = load_mono(12)
    f_code_b = load_mono(12, bold=True)

    # Code lines with syntax highlighting
    code_lines = [
        # ([(color, text), ...])
        [(C["code_comment"], "# Axon OS — Intent Engine Core")],
        [],
        [(C["code_kw"], "import"), (C["white"], " asyncio"), (C["white"], ", "), (C["code_kw"], "json")],
        [(C["code_kw"], "from"), (C["white"], " pathlib "), (C["code_kw"], "import"), (C["white"], " Path")],
        [(C["code_kw"], "from"), (C["white"], " axon.ai "), (C["code_kw"], "import"), (C["white"], " IntentParser, ModelRouter")],
        [],
        [(C["code_comment"], "# ─── Configuration ───────────────────────────")],
        [(C["code_kw"], "class"), (C["white"], " "), (C["code_fn"], "AxonConfig"), (C["white"], ":")],
        [(C["white"], "    model:  "), (C["code_str"], '"llama3.2:3b"')],
        [(C["white"], "    host:   "), (C["code_str"], '"localhost:11434"')],
        [(C["white"], "    theme:  "), (C["code_str"], '"axon-dark"')],
        [(C["white"], "    stream: "), (C["code_kw"], "True")],
        [],
        [(C["code_comment"], "# ─── Intent Handler ──────────────────────────")],
        [(C["code_kw"], "async"), (C["white"], " "), (C["code_kw"], "def"), (C["white"], " "), (C["code_fn"], "handle_intent"), (C["white"], "(query: "), (C["code_fn"], "str"), (C["white"], ") -> "), (C["code_fn"], "dict"), (C["white"], ":")],
        [(C["white"], "    parser  = "), (C["code_fn"], "IntentParser"), (C["white"], "()")],
        [(C["white"], "    router  = "), (C["code_fn"], "ModelRouter"), (C["white"], ".from_config()")],
        [(C["white"], "    intent  = "), (C["code_kw"], "await"), (C["white"], " parser."), (C["code_fn"], "parse"), (C["white"], "(query)")],
        [],
        [(C["white"], "    "), (C["code_kw"], "if"), (C["white"], " intent.type == "), (C["code_str"], '"run_command"'), (C["white"], ":")],
        [(C["white"], "        result = "), (C["code_kw"], "await"), (C["white"], " "), (C["code_fn"], "exec_shell"), (C["white"], "(intent.payload)")],
        [(C["white"], "    "), (C["code_kw"], "elif"), (C["white"], " intent.type == "), (C["code_str"], '"open_app"'), (C["white"], ":")],
        [(C["white"], "        result = "), (C["code_fn"], "launch_app"), (C["white"], "(intent.payload)")],
        [(C["white"], "    "), (C["code_kw"], "else"), (C["white"], ":")],
        [(C["white"], "        result = "), (C["code_kw"], "await"), (C["white"], " router."), (C["code_fn"], "stream"), (C["white"], "(intent)")],
        [],
        [(C["white"], "    "), (C["code_kw"], "return"), (C["white"], " {"), (C["code_str"], '"status"'), (C["white"], ": "), (C["code_str"], '"ok"'), (C["white"], ", "), (C["code_str"], '"data"'), (C["white"], ": result}")],
    ]

    line_height = 18
    for i, line_tokens in enumerate(code_lines):
        ly = code_y + 8 + i * line_height
        if ly > y + h - 8:
            break
        # Line number
        ln_text = str(i + 1)
        draw.text((x + line_w - 6 - draw.textbbox((0,0),ln_text,font=f_code)[2], ly),
                  ln_text, font=f_code, fill=C["dim"])
        # Code tokens
        cx2 = x + line_w + 12
        for color, token in line_tokens:
            draw.text((cx2, ly), token, font=f_code, fill=color)
            cx2 += draw.textbbox((0,0), token, font=f_code)[2]

    # Scrollbar
    draw.rounded_rectangle([x+w-8, code_y+4, x+w-2, y+h-4], radius=3, fill=C["scrollbar"])
    draw.rounded_rectangle([x+w-8, code_y+4, x+w-2, code_y+80], radius=3, fill=(70,70,100))

    img.paste(layer, (0,0), layer)

# ─── File Manager Window ──────────────────────────────────────────────────────

def draw_file_manager(img, x, y, w, h):
    layer = img.copy().convert("RGBA")
    draw = draw_window_frame(layer, x, y, w, h, "Files — /home/hxshin", radius=12)

    # Toolbar
    tool_y = y + 36
    draw.rectangle([x, tool_y, x+w, tool_y+36], fill=(12,12,22))
    f_sm = load_font(11)
    f_sm_b = load_font(12, bold=True)

    # Path breadcrumb
    path_parts = [("~", C["violet"]), (" / ", C["dim"]), ("projects", C["gray"]),
                  (" / ", C["dim"]), ("Axon OS", C["white"])]
    px = x + 16
    for text, col in path_parts:
        draw.text((px, tool_y + 10), text, font=f_sm_b, fill=col)
        px += draw.textbbox((0,0), text, font=f_sm_b)[2]

    # View toggle buttons
    for bx, icon in [(x+w-58, "⊞"), (x+w-34, "☰")]:
        draw.rounded_rectangle([bx, tool_y+8, bx+20, tool_y+28], radius=4,
                                fill=C["chip_bg"], outline=C["chip_border"], width=1)
        text_center(draw, icon, bx+10, tool_y+9, f_sm, C["gray"])

    # Sidebar
    sidebar_w = 130
    side_y = tool_y + 36
    draw.rectangle([x, side_y, x+sidebar_w, y+h], fill=(10,10,18))
    draw.line([(x+sidebar_w, side_y), (x+sidebar_w, y+h)], fill=(25,25,40))

    sidebar_items = [
        ("FAVORITES", True),
        ("  Home", False),
        ("  Desktop", False),
        ("  Documents", False),
        ("  Downloads", False),
        ("  Projects", False),
        ("DEVICES", True),
        ("  Disk (500GB)", False),
        ("  USB Drive", False),
    ]
    sy = side_y + 10
    for item, is_header in sidebar_items:
        if is_header:
            draw.text((x+10, sy), item, font=load_font(9, bold=True), fill=C["dim"])
        else:
            col = C["violet"] if item.strip() == "Projects" else C["gray"]
            bg = C["chip_bg"] if item.strip() == "Projects" else None
            if bg:
                draw.rounded_rectangle([x+4, sy-2, x+sidebar_w-4, sy+14], radius=4, fill=bg)
            draw.text((x+10, sy), item, font=f_sm, fill=col)
        sy += 18

    # File grid
    grid_x = x + sidebar_w + 12
    grid_y = side_y + 12
    folders = [
        ("axon-core",    (80, 60, 140)),
        ("ai-models",    (60, 100, 160)),
        ("ui",           (100, 70, 50)),
        ("config",       (50, 120, 80)),
        ("scripts",      (120, 80, 40)),
        ("logs",         (80, 80, 100)),
        ("screenshots",  (60, 130, 110)),
        ("tests",        (100, 60, 100)),
        ("docs",         (50, 80, 140)),
    ]
    cols = 4
    cell_w = (w - sidebar_w - 24) // cols
    cell_h = 72

    f_folder = load_font(10)
    for idx, (name, color) in enumerate(folders):
        col_idx = idx % cols
        row_idx = idx // cols
        fx = grid_x + col_idx * cell_w
        fy = grid_y + row_idx * cell_h
        if fy + cell_h > y + h - 8:
            break

        # Folder icon background
        icon_x, icon_y = fx + (cell_w-44)//2, fy + 4
        # Draw folder shape
        draw.rounded_rectangle([icon_x, icon_y+6, icon_x+44, icon_y+36],
                                radius=4, fill=color)
        draw.rounded_rectangle([icon_x, icon_y+8, icon_x+22, icon_y+14],
                                radius=3, fill=(
                                    min(color[0]+30,255),
                                    min(color[1]+30,255),
                                    min(color[2]+30,255)))
        # Label
        text_center(draw, name, fx + cell_w//2, fy + 44, f_folder, C["gray"])

    img.paste(layer, (0,0), layer)

# ─── Bottom Dock ──────────────────────────────────────────────────────────────

def draw_dock(img):
    layer = img.copy().convert("RGBA")
    draw = ImageDraw.Draw(layer)

    dock_h = 72
    icon_size = 48
    icon_margin = 10
    n_icons = 11
    sep_idx = 9  # separator before last 2

    # Calculate dock width
    total_icons_w = (icon_size + icon_margin) * n_icons + icon_margin + 16  # +16 for separator
    dock_w = total_icons_w + 24
    dock_x = (W - dock_w) // 2
    dock_y = H - dock_h - 8

    # Frosted glass pill
    # Shadow
    for i in range(12, 0, -1):
        alpha = int(60 * (i/12)**2)
        draw.rounded_rectangle([dock_x-i, dock_y+i, dock_x+dock_w+i, dock_y+dock_h+i],
                                radius=36, fill=(0,0,0,alpha))

    draw.rounded_rectangle([dock_x, dock_y, dock_x+dock_w, dock_y+dock_h],
                            radius=36, fill=(*C["dock_bg"], 230))
    draw.rounded_rectangle([dock_x, dock_y, dock_x+dock_w, dock_y+dock_h],
                            radius=36, outline=(*C["dock_border"], 180), width=1)

    # Top gloss line
    draw.arc([dock_x+4, dock_y+2, dock_x+dock_w-4, dock_y+dock_h-2],
             start=200, end=340, fill=(255,255,255,30), width=1)

    # Icons
    app_icons = [
        ("Files",    (60, 130, 200),  "⊞"),
        ("Firefox",  (210, 100, 40),  "◎"),
        ("Terminal", (40, 180, 120),  ">_"),
        ("Code",     (30, 120, 220),  "{}"),
        ("Settings", (120, 120, 140), "⚙"),
        ("Calendar", (220, 60, 80),   "31"),
        ("Photos",   (200, 150, 40),  "⬡"),
        ("Music",    (180, 60, 200),  "♪"),
        ("Mail",     (60, 160, 220),  "@"),
        # separator before these
        ("AI Panel", (139, 92, 246),  "⬡"),
        ("Intent",   (34, 211, 238),  "✦"),
    ]

    ix = dock_x + 12
    f_icon_label = load_font(9)
    f_icon_sym   = load_font(16, bold=True)
    f_icon_sym_sm = load_font(13, bold=True)

    for idx, (name, color, sym) in enumerate(app_icons):
        if idx == sep_idx:
            # separator
            sep_cx = ix + 4
            draw.line([(sep_cx, dock_y+14), (sep_cx, dock_y+dock_h-14)],
                      fill=(*C["dock_border"], 160), width=1)
            ix += 16

        # Magnification effect: icons near center are slightly larger
        center_offset = abs(idx - (n_icons / 2))
        scale = max(0.78, 1.0 - center_offset * 0.04)
        sz = int(icon_size * scale)
        cy = dock_y + dock_h//2 - 8

        # Icon circle
        icx = ix + icon_size//2
        draw_circle(draw, icx, cy - (sz-icon_size)//2, sz//2,
                    fill=(*color, 230))

        # Glossy highlight on icon
        draw.arc([icx - sz//2 + 2, cy - (sz-icon_size)//2 - sz//2 + 2,
                  icx + sz//2 - 2, cy - (sz-icon_size)//2 + sz//2 - 2],
                 start=200, end=360, fill=(255,255,255,50), width=2)

        # Symbol
        f_use = f_icon_sym if len(sym) <= 2 else f_icon_sym_sm
        bb = draw.textbbox((0,0), sym, font=f_use)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        draw.text((icx - tw//2, cy - (sz-icon_size)//2 - th//2 - 2),
                  sym, font=f_use, fill=(255,255,255,220))

        # Label
        text_center(draw, name, icx, dock_y + dock_h - 14, f_icon_label, C["dim"])

        # Dot indicator for running apps (first 4)
        if idx < 4:
            draw_circle(draw, icx, dock_y + dock_h - 5, 2, (200,200,220,160))

        ix += icon_size + icon_margin

    img.paste(layer, (0,0), layer)

# ─── Intent Bar ───────────────────────────────────────────────────────────────

def draw_intent_bar(img):
    layer = img.copy().convert("RGBA")
    draw = ImageDraw.Draw(layer)

    bar_w, bar_h = 680, 86
    bar_x = (W - bar_w) // 2
    bar_y = 420

    # Glow behind
    glow = Image.new("RGBA", (W, H), (0,0,0,0))
    gd = ImageDraw.Draw(glow)
    for r in range(120, 0, -3):
        alpha = int(40 * (1 - r/120)**1.8)
        gd.ellipse([bar_x + bar_w//2 - r, bar_y - r//3,
                    bar_x + bar_w//2 + r, bar_y + bar_h + r//3],
                   fill=(139, 92, 246, alpha))
    layer.paste(glow, (0,0), glow)

    # Shadow
    for i in range(20, 0, -1):
        alpha = int(100 * (i/20)**2)
        draw.rounded_rectangle([bar_x - i, bar_y + i, bar_x + bar_w + i, bar_y + bar_h + i],
                                radius=18, fill=(0,0,0,alpha))

    # Main bar
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                            radius=18, fill=(*C["intent_bg"], 248))
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                            radius=18, outline=(60, 40, 100, 200), width=1)

    # Top highlight
    draw.rounded_rectangle([bar_x+1, bar_y+1, bar_x+bar_w-1, bar_y+2],
                            radius=17, fill=(255,255,255,18))

    # Hex logo
    hex_icon(draw, bar_x + 22, bar_y + 24, 9, C["violet"])

    # Placeholder text
    f_placeholder = load_font(15)
    draw.text((bar_x + 40, bar_y + 16), "Ask anything or type a command...",
              font=f_placeholder, fill=(90, 80, 130))

    # Cursor blink
    draw.rectangle([bar_x + 40, bar_y + 18,
                    bar_x + 41, bar_y + 30], fill=(139, 92, 246, 180))

    # Right badges
    f_badge = load_font(11, bold=True)
    # Code badge
    code_label = "● Code"
    bb = draw.textbbox((0,0), code_label, font=f_badge)
    bw = bb[2]-bb[0] + 16
    bx = bar_x + bar_w - 14 - bw
    draw.rounded_rectangle([bx, bar_y + 10, bx+bw, bar_y + 30],
                            radius=8, fill=(50, 30, 100, 200),
                            outline=(139, 92, 246, 180), width=1)
    draw.text((bx+8, bar_y+12), code_label, font=f_badge, fill=C["violet"])
    bx -= bw + 8

    model_label = "llama3.2:3b"
    bb = draw.textbbox((0,0), model_label, font=f_badge)
    bw = bb[2]-bb[0] + 16
    bx2 = bx - bw
    draw.rounded_rectangle([bx2, bar_y + 10, bx2+bw, bar_y + 30],
                            radius=8, fill=(10, 50, 70, 200),
                            outline=(34, 211, 238, 160), width=1)
    draw.text((bx2+8, bar_y+12), model_label, font=f_badge, fill=C["cyan"])

    # Bottom chips row
    chips = ["Open App", "Run Command", "Search Web", "Summarize", "Write Code"]
    f_chip = load_font(11)
    cx = bar_x + 14
    for chip in chips:
        bb = draw.textbbox((0,0), chip, font=f_chip)
        cw = bb[2]-bb[0] + 18
        draw.rounded_rectangle([cx, bar_y + 56, cx+cw, bar_y + 76],
                                radius=8, fill=(*C["chip_bg"], 200),
                                outline=(*C["chip_border"], 180), width=1)
        draw.text((cx+9, bar_y+58), chip, font=f_chip, fill=C["gray"])
        cx += cw + 8

    img.paste(layer, (0,0), layer)

# ─── AI Panel ─────────────────────────────────────────────────────────────────

def draw_ai_panel(img):
    layer = img.copy().convert("RGBA")
    draw = ImageDraw.Draw(layer)

    panel_w = 420
    panel_x = W - panel_w + 30  # slightly off-screen / sliding in
    panel_y = 32
    panel_h = H - 32 - 84

    # Shadow on left edge
    for i in range(30, 0, -1):
        alpha = int(80 * (i/30)**2)
        draw.rectangle([panel_x - i, panel_y, panel_x, panel_y + panel_h],
                       fill=(0,0,0,alpha))

    # Panel background
    draw.rounded_rectangle([panel_x, panel_y, panel_x+panel_w-30, panel_y+panel_h],
                            radius=0, fill=(*C["panel_bg"], 240))
    draw.line([(panel_x, panel_y), (panel_x, panel_y+panel_h)], fill=(40,40,65), width=1)

    f_title  = load_font(14, bold=True)
    f_sm     = load_font(12)
    f_sm_b   = load_font(12, bold=True)
    f_body   = load_font(12)
    f_badge  = load_font(10, bold=True)

    # Panel header
    draw.rectangle([panel_x, panel_y, panel_x+panel_w-30, panel_y+52], fill=(10,10,20))
    draw.line([(panel_x, panel_y+52), (panel_x+panel_w-30, panel_y+52)], fill=(30,30,50))
    hex_icon(draw, panel_x+22, panel_y+26, 9, C["violet"])
    draw.text((panel_x+38, panel_y+14), "Axon AI", font=f_title, fill=C["white"])

    # Model badge in header
    mb = "llama3.2:3b"
    bb = draw.textbbox((0,0), mb, font=f_badge)
    mw = bb[2]-bb[0]+12
    mx = panel_x + panel_w - 30 - mw - 10
    draw.rounded_rectangle([mx, panel_y+16, mx+mw, panel_y+36],
                            radius=6, fill=(10,50,70,200),
                            outline=(34,211,238,140), width=1)
    draw.text((mx+6, panel_y+18), mb, font=f_badge, fill=C["cyan"])

    # Chat area
    chat_y = panel_y + 62
    cw = panel_w - 30 - 20  # content width

    # User message bubble
    user_msg = "How does the Intent Engine work?"
    user_bubble_w = 220
    user_bx = panel_x + panel_w - 30 - 10 - user_bubble_w
    draw.rounded_rectangle([user_bx, chat_y, user_bx+user_bubble_w, chat_y+38],
                            radius=12, fill=(*C["bubble_user"], 220))
    draw.text((user_bx+12, chat_y+8), user_msg, font=f_sm, fill=(220,200,255))
    chat_y += 50

    # AI response bubble
    ai_lines = [
        "The Intent Engine parses your",
        "natural language input and routes",
        "it to the right action handler:",
        "",
        "  • run_command  → shell exec",
        "  • open_app     → launcher",
        "  • query        → LLM stream",
        "",
        "All streamed in real-time via",
        "Ollama running locally.",
    ]
    ai_bh = len(ai_lines) * 17 + 20
    draw.rounded_rectangle([panel_x+10, chat_y, panel_x+10+cw, chat_y+ai_bh],
                            radius=12, fill=(*C["bubble_ai"], 220),
                            outline=(40,40,70,180), width=1)

    # AI icon
    hex_icon(draw, panel_x+22, chat_y+16, 7, C["violet"])

    for i, line in enumerate(ai_lines):
        col = C["gray"] if not line.startswith("  •") else (200, 200, 220)
        if line.startswith("  • "):
            parts = line.split("→")
            draw.text((panel_x+22, chat_y+10+i*17), parts[0], font=f_sm, fill=(180,180,200))
            if len(parts) > 1:
                p0w = draw.textbbox((0,0), parts[0], font=f_sm)[2]
                draw.text((panel_x+22+p0w, chat_y+10+i*17), "→"+parts[1], font=f_sm, fill=C["dim"])
        else:
            draw.text((panel_x+22, chat_y+10+i*17), line, font=f_sm, fill=col)

    # Streaming indicator
    chat_y += ai_bh + 8
    dot_x = panel_x + 16
    for d in range(3):
        alpha = 200 if d == 0 else (140 if d == 1 else 80)
        draw_circle(draw, dot_x + d*14, chat_y + 8, 4, (*C["violet"], alpha))

    # Input field at bottom
    input_y = panel_y + panel_h - 52
    draw.rectangle([panel_x, input_y-1, panel_x+panel_w-30, panel_y+panel_h], fill=(10,10,20))
    draw.rounded_rectangle([panel_x+10, input_y+8, panel_x+panel_w-50, input_y+36],
                            radius=8, fill=(20,20,36), outline=(45,45,75), width=1)
    draw.text((panel_x+22, input_y+14), "Ask Axon AI...", font=f_sm, fill=C["dim"])

    # Send button
    sbx = panel_x + panel_w - 46
    draw.rounded_rectangle([sbx, input_y+8, sbx+28, input_y+36],
                            radius=8, fill=(*C["violet_dim"], 220))
    f_send = load_font(14, bold=True)
    text_center(draw, "↑", sbx+14, input_y+9, f_send, C["white"])

    img.paste(layer, (0,0), layer)

# ─── Compose ──────────────────────────────────────────────────────────────────

def main():
    print("Generating Axon OS desktop preview...")
    img = Image.new("RGBA", (W, H), (9, 9, 15, 255))

    print("  Drawing background...")
    draw_background(img)

    print("  Drawing file manager window...")
    draw_file_manager(img, 980, 80, 520, 500)

    print("  Drawing code editor window...")
    draw_code_editor(img, 60, 60, 840, 560)

    print("  Drawing AI panel...")
    draw_ai_panel(img)

    print("  Drawing menu bar...")
    draw_menubar(img)

    print("  Drawing intent bar...")
    draw_intent_bar(img)

    print("  Drawing dock...")
    draw_dock(img)

    # Convert to RGB for PNG
    final = Image.new("RGB", (W, H), (9, 9, 15))
    final.paste(img, (0,0), img)

    # Slight sharpness post-process
    from PIL import ImageEnhance
    final = ImageEnhance.Sharpness(final).enhance(1.1)

    final.save(OUT_PATH, "PNG", optimize=False, compress_level=6)
    print(f"  Saved: {OUT_PATH}")
    return OUT_PATH

if __name__ == "__main__":
    main()
