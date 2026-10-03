import json
import os
import re
import shutil
import sys
import tkinter as tk
import webbrowser
from collections import Counter
from pathlib import Path
from tkinter import messagebox, ttk


APP_NAME = 'D2RunewordTracker'


def get_resource_path(filename: str) -> Path:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parent
    return base_dir / filename


def get_user_data_dir() -> Path:

    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA')
        root = Path(base) if base else Path.home() / 'AppData' / 'Local'
    elif sys.platform == 'darwin':
        root = Path.home() / 'Library' / 'Application Support'
    else:
        root = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))

    app_dir = root / APP_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


DATA_FILE = get_resource_path('runewords.json')
USER_FILE = get_user_data_dir() / 'user_data.json'

RUNE_ORDER = [
    'El','Eld','Tir','Nef','Eth','Ith','Tal','Ral','Ort','Thul','Amn','Sol',
    'Shael','Dol','Hel','Io','Lum','Ko','Fal','Lem','Pul','Um','Mal','Ist',
    'Gul','Vex','Ohm','Lo','Sur','Ber','Jah','Cham','Zod'
]


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: Path, value):
    with path.open('w', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)


def load_runewords():
    loaded = load_json(DATA_FILE, {'items': []})

    if isinstance(loaded, list):
        return {'items': loaded}

    if not isinstance(loaded, dict) or 'items' not in loaded:
        return {'items': []}

    return loaded


def migrate_legacy_user_data():
    if USER_FILE.exists():
        return

    legacy_file = Path(__file__).resolve().parent / 'user_data.json'
    if legacy_file.exists() and legacy_file != USER_FILE:
        try:
            shutil.copy2(legacy_file, USER_FILE)
        except OSError:
            pass


def load_user_data():
    migrate_legacy_user_data()
    loaded = load_json(USER_FILE, {'inventory': {}, 'runewords': {}})
    loaded.setdefault('inventory', {})
    loaded.setdefault('runewords', {})
    for rune in RUNE_ORDER:
        loaded['inventory'].setdefault(rune, 0)
    return loaded


def save_all():
    save_json(USER_FILE, user_data)



def _hex_to_rgb(value):
    value = value.lstrip('#')
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def _blend_color(a, b, t):
    ar, ag, ab = _hex_to_rgb(a)
    br, bg, bb = _hex_to_rgb(b)
    return _rgb_to_hex((
        round(ar + (br - ar) * t),
        round(ag + (bg - ag) * t),
        round(ab + (bb - ab) * t),
    ))


def animate_button_bg(button, start, end, steps=5, delay=12):
    button._anim_token = getattr(button, '_anim_token', 0) + 1
    token = button._anim_token

    def step(i=1):
        if not button.winfo_exists() or getattr(button, '_anim_token', None) != token:
            return
        t = i / steps
        button.configure(bg=_blend_color(start, end, t))
        if i < steps:
            button.after(delay, lambda: step(i + 1))

    step()


def make_smooth_button(parent,
                       *, 
                       text, 
                       command, 
                       bg='#333333', 
                       fg='white',
                       hover_bg='#444444', 
                       press_bg='#555555',
                       active_fg='white', 
                       font=('Segoe UI', 10),
                       width=None, 
                       padx=8, 
                       pady=4, 
                       bd=0,
                       **kwargs):
    
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        activebackground=press_bg,
        activeforeground=active_fg,
        relief='flat',
        bd=bd,
        font=font,
        cursor='hand2',
        padx=padx,
        pady=pady,
        highlightthickness=0,
        **kwargs
    )

    if width is not None:
        btn.configure(width=width)

    def on_enter(_):
        btn.configure(bg=hover_bg)

    def on_leave(_):
        btn.configure(bg=bg)

    def on_press(_):
        btn.configure(bg=press_bg, relief='sunken')

    def on_release(_):
        btn.configure(bg=hover_bg, relief='flat')

    btn.bind('<Enter>', on_enter, add='+')
    btn.bind('<Leave>', on_leave, add='+')
    btn.bind('<ButtonPress-1>', on_press, add='+')
    btn.bind('<ButtonRelease-1>', on_release, add='+')

    return btn



def get_runeword_state(name):
    state = user_data['runewords'].setdefault(name, {'completed': False, 'favorite': False})
    state.setdefault('completed', False)
    state.setdefault('favorite', False)
    return state


def toggle_completed(name):
    state = get_runeword_state(name)
    state['completed'] = not state['completed']
    save_all()
    refresh_list()


def toggle_favorite(name):
    state = get_runeword_state(name)
    state['favorite'] = not state['favorite']
    save_all()
    refresh_list()


def reset_completed():
    if not messagebox.askyesno('Reset checklist', 'Uncheck every completed runeword?'):
        return
    for name in user_data['runewords']:
        user_data['runewords'][name]['completed'] = False
    save_all()
    refresh_list()


def get_missing_runes(item):
    needed = Counter(item.get('runes', []))
    missing = {}
    for rune, amount in needed.items():
        have = int(user_data['inventory'].get(rune, 0))
        if have < amount:
            missing[rune] = amount - have
    return missing


def can_craft(item):
    return not get_missing_runes(item)


def calculate_missing_rune_totals(items, states, inventory):
    """Count one copy of every unfinished runeword, sharing inventory once."""
    required = Counter()
    remaining = 0
    for item in items:
        if states.get(item['name'], {}).get('completed', False):
            continue
        remaining += 1
        required.update(item.get('runes', []))

    ordered = [rune for rune in RUNE_ORDER if rune in required]
    ordered.extend(sorted(set(required) - set(RUNE_ORDER)))
    rows = []
    for rune in ordered:
        needed = required[rune]
        owned = max(0, int(inventory.get(rune, 0)))
        rows.append((rune, needed, owned, max(0, needed - owned)))
    return remaining, rows


missing_runes_window = None


def open_missing_runes():
    global missing_runes_window
    if missing_runes_window is not None and missing_runes_window.winfo_exists():
        missing_runes_window.refresh_totals()
        missing_runes_window.lift()
        missing_runes_window.focus_set()
        return

    win = tk.Toplevel(root)
    missing_runes_window = win
    win.title('Runes for Missing Runewords')
    win.geometry('580x660')
    win.minsize(540, 420)
    win.configure(bg='#121212')
    tk.Label(win, text='Runes for Missing Runewords', bg='#121212',
             fg='white', font=('Segoe UI', 18, 'bold')).pack(
                 anchor='w', padx=20, pady=(20, 8))
    tk.Label(win, text='One copy of every uncompleted runeword, regardless of search or filter.\n'
             'Inventory is deducted once from the combined requirements.\n'
             'Direct rune requirements only; cube upgrades are not included.',
             bg='#121212', fg='#aaaaaa', font=('Segoe UI', 9),
             justify='left', anchor='w').pack(fill='x', padx=20)

    summary = tk.Label(win, bg='#121212', fg='#c9a85c',
                       font=('Segoe UI', 10, 'bold'), justify='left', anchor='w')
    summary.pack(fill='x', padx=20, pady=14)

    style = ttk.Style(win)
    style.configure('RuneTotals.Treeview', background='#1e1e1e',
                    fieldbackground='#1e1e1e', foreground='#dddddd',
                    rowheight=28, font=('Segoe UI', 10))
    style.map('RuneTotals.Treeview', background=[('selected', '#454035')],
              foreground=[('selected', 'white')])
    table_frame = tk.Frame(win, bg='#121212')
    table_frame.pack(fill='both', expand=True, padx=20)
    table = ttk.Treeview(table_frame, columns=('rune', 'required', 'owned', 'need'),
                         show='headings', style='RuneTotals.Treeview', selectmode='browse')
    for column, title in [('rune', 'Rune'), ('required', 'Required'),
                          ('owned', 'Owned'), ('need', 'Still needed')]:
        table.heading(column, text=title)
        table.column(column, width=120, minwidth=90,
                     anchor='w' if column == 'rune' else 'center')
    scroll = ttk.Scrollbar(table_frame, orient='vertical', command=table.yview,
                           style='Dark.Vertical.TScrollbar')
    table.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right', fill='y')
    table.pack(side='left', fill='both', expand=True)
    table.tag_configure('needed', foreground='#e6a15c')
    table.tag_configure('covered', foreground='#00dd88')

    def refresh_totals():
        remaining, rows = calculate_missing_rune_totals(
            data.get('items', []), user_data['runewords'], user_data['inventory'])
        position = table.yview()[0]
        children = table.get_children()
        if children:
            table.delete(*children)
        for rune, required, owned, needed in rows:
            table.insert('', 'end', values=(rune, required, owned, needed),
                         tags=('needed' if needed else 'covered',))
        table.yview_moveto(position)
        total = sum(row[1] for row in rows)
        shortage = sum(row[3] for row in rows)
        types = sum(row[3] > 0 for row in rows)
        if not remaining:
            text = 'No missing runewords — everything is completed.'
        else:
            text = (f'{remaining} missing runewords • {total} runes required\n'
                    f'Still needed: {shortage} runes across {types} rune types')
        summary.configure(text=text)

    win.refresh_totals = refresh_totals
    buttons = tk.Frame(win, bg='#121212')
    buttons.pack(fill='x', padx=20, pady=16)
    make_smooth_button(buttons, text='Edit inventory', command=open_inventory).pack(side='left')
    make_smooth_button(buttons, text='Close', command=win.destroy).pack(side='right')
    win.bind('<Escape>', lambda _: win.destroy())
    refresh_totals()


def craft_count(item):
    needed = Counter(item.get('runes', []))
    if not needed:
        return 0
    return min(int(user_data['inventory'].get(r, 0)) // n for r, n in needed.items())


def format_missing(missing):
    if not missing:
        return 'You have all runes'
    ordered = []
    for rune in RUNE_ORDER:
        if rune in missing:
            count = missing[rune]
            ordered.append(f'{rune} ×{count}' if count > 1 else rune)
    for rune, count in missing.items():
        if rune not in RUNE_ORDER:
            ordered.append(f'{rune} ×{count}' if count > 1 else rune)
    return 'Missing: ' + ', '.join(ordered)



def get_base_icon(bases):
    names = " ".join(bases).casefold()

    if any(word in names for word in ("shield", "voodoo head", "grimoire")):
        return "🛡"
    if any(word in names for word in ("helm", "helmet")):
        return "⛑"
    if "armor" in names:
        return "◆"
    if any(word in names for word in ("bow", "crossbow", "missile")):
        return "🏹"
    if any(word in names for word in ("staff", "wand")):
        return "✦"
    if any(word in names for word in ("claw", "knife")):
        return "🗡"
    if any(word in names for word in ("sword", "axe", "mace", "hammer", "scepter",
                                      "polearm", "spear", "weapon", "melee")):
        return "⚔"
    return "•"


def format_base_with_icon(item):
    bases = item.get("bases", [])
    if not bases:
        return ""
    return f"{get_base_icon(bases)} {', '.join(bases)}"

def get_filtered_items():
    query = search_var.get().strip().casefold()
    mode = filter_var.get()
    items = []

    for item in data.get('items', []):
        state = get_runeword_state(item['name'])
        missing = get_missing_runes(item)
        missing_count = sum(missing.values())

        if mode == 'Missing' and state['completed']:
            continue
        if mode == 'Completed' and not state['completed']:
            continue
        if mode == 'Can craft' and missing:
            continue
        if mode == 'Missing 1 rune' and missing_count != 1:
            continue
        if mode == 'Favorites' and not state['favorite']:
            continue

        searchable = ' '.join([
            item.get('name', ''),
            ' '.join(item.get('runes', [])),
            ' '.join(item.get('bases', [])),
            str(item.get('level', '')),
        ]).casefold()

        if query and query not in searchable:
            continue
        items.append(item)

    sort_mode = sort_var.get()
    if sort_mode == 'Name':
        items.sort(key=lambda i: i.get('name', '').casefold())
    elif sort_mode == 'Level':
        items.sort(key=lambda i: (i.get('level') is None, i.get('level') or 999, i.get('name', '').casefold()))
    elif sort_mode == 'Craftable first':
        items.sort(key=lambda i: (not can_craft(i), get_runeword_state(i['name'])['completed'], i.get('name', '').casefold()))
    else:
        items.sort(key=lambda i: (get_runeword_state(i['name'])['completed'], i.get('level') or 999, i.get('name', '').casefold()))
    return items





def open_details(item):
    state = get_runeword_state(item['name'])
    missing = get_missing_runes(item)
    win = tk.Toplevel(root)
    win.title(item['name'])
    win.geometry('430x600')
    win.configure(bg='#121212')
    win.resizable(False, False)

    tk.Label(win, text=item['name'], bg='#121212', fg='white', font=('Segoe UI', 20, 'bold')).pack(anchor='w', padx=20, pady=(20, 8))

    details = [
        f"Runes: {' → '.join(item.get('runes', []))}",
        f"Sockets: {item.get('sockets') or '-'}",
        f"Required level: {item.get('level') or '-'}",
        f"Craftable copies: {craft_count(item)}",
        f"Status: {'Completed' if state['completed'] else 'Not completed'}",
        format_missing(missing),
    ]

    for text in details[:2]:
        tk.Label(win, text=text, bg='#121212', fg='#c9a85c' if text.startswith('Runes:') else '#dddddd', font=('Segoe UI', 10, 'bold'), anchor='w', justify='left', wraplength=560).pack(fill='x', padx=20, pady=3)

    bases = item.get('bases', [])
    base_row = tk.Frame(win, bg='#121212')
    base_row.pack(fill='x', padx=20, pady=3)
    tk.Label(base_row, text='Bases:', bg='#121212', fg='#dddddd', font=('Segoe UI', 10, 'bold')).pack(side='left')
    if bases:
        tk.Label(base_row, text=get_base_icon(bases), bg='#121212', fg='white', font=('Segoe UI Symbol', 16, 'bold')).pack(side='left', padx=(6, 5))
        tk.Label(base_row, text=', '.join(bases), bg='#121212', fg='#dddddd', font=('Segoe UI', 10, 'bold')).pack(side='left')
    else:
        tk.Label(base_row, text='-', bg='#121212', fg='#dddddd', font=('Segoe UI', 10, 'bold')).pack(side='left', padx=(6, 0))

    for text in details[2:]:
        tk.Label(win, text=text, bg='#121212', fg='#dddddd', font=('Segoe UI', 10, 'bold'), anchor='w', justify='left', wraplength=560).pack(fill='x', padx=20, pady=3)

    tk.Label(win, text='Stats', bg='#121212', fg='white', font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=20, pady=(16, 5))
    stats = tk.Text(win, bg='#1e1e1e', fg='#dddddd', insertbackground='white', relief='flat', wrap='word', height=18, padx=10, pady=10)
    stats.pack(fill='both', expand=True, padx=20, pady=(0, 20))

    stats.insert('1.0', item.get('stats', '') or 'No stats available.')


    stats.tag_configure('variable_roll', foreground='#ffd166', font=('Segoe UI', 10))
    for needle in item.get('variable_stats', []):
        start = '1.0'
        while True:
            pos = stats.search(needle, start, stopindex='end')
            if not pos:
                break
            end = f"{pos}+{len(needle)}c"
            stats.tag_add('variable_roll', pos, end)
            start = end

    stats.config(state='disabled')


def open_inventory():
    win = tk.Toplevel(root)
    win.title('Rune Inventory')
    win.geometry('440x650')
    win.configure(bg='#121212')

    tk.Label(win, text='Rune Inventory', bg="#121212", fg='white', font=('Segoe UI', 20, 'bold')).pack(anchor='w', padx=20, pady=(20, 4))
    tk.Label(win, text='Enter how many of each rune you own.', bg='#121212', fg='#aaaaaa', font=('Segoe UI', 10)).pack(anchor='w', padx=20, pady=(0, 12))

    outer = tk.Frame(win, bg='#121212')
    outer.pack(fill='both', expand=True, padx=20, pady=(0, 20))
    canvas_inv = tk.Canvas(outer, bg='#121212', highlightthickness=0)
    scrollbar_inv = ttk.Scrollbar(outer, orient='vertical', command=canvas_inv.yview,
                                  style='Dark.Vertical.TScrollbar')
    canvas_inv.configure(yscrollcommand=scrollbar_inv.set)
    scrollbar_inv.pack(side='right', fill='y')
    canvas_inv.pack(side='left', fill='both', expand=True)

    frame = tk.Frame(canvas_inv, bg='#121212')
    inv_window_id = canvas_inv.create_window((0, 0), window=frame, anchor='nw')
    canvas_inv.bind('<Configure>', lambda e: canvas_inv.itemconfigure(inv_window_id, width=e.width))
    frame.bind('<Configure>', lambda e: canvas_inv.configure(scrollregion=canvas_inv.bbox('all')))

    def commit(rune, var):
        try:
            value = max(0, int(var.get()))
        except ValueError:
            value = 0
        var.set(str(value))
        user_data['inventory'][rune] = value
        save_all()
        refresh_list()

    for rune in RUNE_ORDER:
        row = tk.Frame(frame, bg='#1e1e1e', padx=10, pady=7)
        row.pack(fill='x', pady=2)
        tk.Label(row, text=rune, bg='#1e1e1e', fg='white', font=('Segoe UI', 11, 'bold'), width=10, anchor='w').pack(side='left')

        var = tk.StringVar(value=str(user_data['inventory'].get(rune, 0)))
        spin = tk.Spinbox(row, from_=0, to=999, textvariable=var, width=8, bg='#292929', fg='white', insertbackground='white', buttonbackground='#333333', relief='flat', font=('Segoe UI', 10), command=lambda r=rune, v=var: commit(r, v))
        spin.pack(side='right')
        spin.bind('<FocusOut>', lambda e, r=rune, v=var: commit(r, v))
        spin.bind('<Return>', lambda e, r=rune, v=var: commit(r, v))


def refresh_list(*_):
    if missing_runes_window is not None and missing_runes_window.winfo_exists():
        missing_runes_window.refresh_totals()
    for widget in inner_frame.winfo_children():
        widget.destroy()

    items = get_filtered_items()
    all_items = data.get('items', [])
    total = len(all_items)
    completed = sum(get_runeword_state(i['name'])['completed'] for i in all_items)
    remaining = max(0, total - completed)
    percent = round((completed / total) * 100) if total else 0
    craftable_total = sum(can_craft(i) for i in all_items)

    progress_label.config(
        text=f'{percent}% Completed   •   {remaining} Remaining   •   {craftable_total} Craftable'
    )
    progress_var.set(percent)

    if not items:
        tk.Label(inner_frame, text='No runewords to show.', bg='#121212', fg='#888888', font=('Segoe UI', 11)).pack(pady=30)
        return

    for item in items:
        state = get_runeword_state(item['name'])
        completed = state['completed']
        favorite = state['favorite']
        missing = get_missing_runes(item)
        copies = craft_count(item)

        row = tk.Frame(inner_frame, bg='#1e1e1e', padx=7, pady=4)
        row.pack(fill='x', pady=2)

        favorite_btn = make_smooth_button(
            row,
            text='★' if favorite else '☆',
            command=lambda n=item['name']: toggle_favorite(n),
            bg='#1e1e1e',
            fg='#ffd166' if favorite else '#8a8a8a',
            hover_bg='#2a2a2a',
            press_bg='#343434',
            active_fg='#ffd166',
            font=('Segoe UI', 12),
            width=2,
            padx=2,
            pady=2
        )
        favorite_btn.pack(side='left', padx=(0, 8))

        left = tk.Frame(row, bg='#1e1e1e')
        left.pack(side='left', fill='x', expand=True)

        title = item['name'] + (f"  •  Req lvl {item['level']}" if item.get('level') is not None else '')
        tk.Label(left, text=title, bg='#1e1e1e', fg='#777777' if completed else '#ffffff', font=('Segoe UI', 10, 'bold'), anchor='w').pack(fill='x')

        details = ' → '.join(item.get('runes', []))
        if item.get('sockets'):
            details += f"   |   {item['sockets']} sockets"
        bases = item.get('bases', [])
        base_text = ', '.join(bases)

        details_row = tk.Frame(left, bg='#1e1e1e')
        details_row.pack(fill='x', pady=(3, 0))

        tk.Label(
            details_row,
            text=details,
            bg='#1e1e1e',
            fg='#777777' if completed else '#c9a85c',
            font=('Segoe UI', 8),
            anchor='w',
            justify='left'
        ).pack(side='left')

        if bases:
            tk.Label(
                details_row,
                text='   |   ',
                bg='#1e1e1e',
                fg='#777777' if completed else '#c9a85c',
                font=('Segoe UI', 8)
            ).pack(side='left')

            tk.Label(
                details_row,
                text=get_base_icon(bases),
                bg='#1e1e1e',
                fg='white',
                font=('Segoe UI Symbol', 14, 'bold')
            ).pack(side='left', padx=(0, 4))

            tk.Label(
                details_row,
                text=base_text,
                bg='#1e1e1e',
                fg='#777777' if completed else '#c9a85c',
                font=('Segoe UI', 8),
                anchor='w'
            ).pack(side='left')

        status = format_missing(missing)
        if not missing:
            status += f'   •   Can craft {copies}'
        tk.Label(left, text=status, bg='#1e1e1e', fg='#777777' if completed else ('#00dd88' if not missing else '#e6a15c'), font=('Segoe UI', 8), anchor='w').pack(fill='x', pady=(1, 0))

        details_btn = make_smooth_button(
            row,
            text='…',
            command=lambda current=item: open_details(current),
            bg='#303030',
            hover_bg='#454545',
            press_bg='#555555',
            font=('Segoe UI', 10, 'bold'),
            width=2,
            padx=2,
            pady=1,
            anchor="center",
        )
        details_btn.pack(side='right', padx=(4, 0))

        complete_bg = '#2f3432' if completed else '#303030'
        complete_hover = '#3d4a43' if completed else "#3BA06C"
        complete_press = '#4a5a51' if completed else "#12f167"

        completed_btn = tk.Button(
            row,
            text='↩' if completed else '✔',
            command=lambda n=item['name']: toggle_completed(n),
            bg=complete_bg,
            fg='#d8e8df' if completed else 'white',
            activebackground=complete_press,
            activeforeground='white',
            relief='flat',
            bd=1,
            font=('Segoe UI', 11, 'bold'),
            cursor='hand2',
            width=3,
            height=1,
            padx=7,
            pady=1,
            highlightthickness=0,
        )

        def complete_enter(_, btn=completed_btn, start=complete_bg, end=complete_hover):
            animate_button_bg(btn, btn.cget('bg'), end, steps=6, delay=33)

        def complete_leave(_, btn=completed_btn, end=complete_bg):
            animate_button_bg(btn, btn.cget('bg'), end, steps=6, delay=33)

        def complete_press(_, btn=completed_btn, end=complete_press):
            btn._anim_token = getattr(btn, '_anim_token', 0) + 1
            btn.configure(bg=end, relief='sunken')

        def complete_release(_, btn=completed_btn, end=complete_hover):
            btn.configure(relief='flat')
            animate_button_bg(btn, btn.cget('bg'), end, steps=4, delay=33)

        completed_btn.bind('<Enter>', complete_enter)
        completed_btn.bind('<Leave>', complete_leave)
        completed_btn.bind('<ButtonPress-1>', complete_press)
        completed_btn.bind('<ButtonRelease-1>', complete_release)

        completed_btn.pack(side='right', padx=(5, 0))

        def open_item_details(_event=None, current=item):
            open_details(current)

        for widget in (row, left, details_row):
            widget.bind('<Double-Button-1>', open_item_details)

        for child in left.winfo_children():
            if not isinstance(child, tk.Button):
                child.bind('<Double-Button-1>', open_item_details)
                for grandchild in child.winfo_children():
                    if not isinstance(grandchild, tk.Button):
                        grandchild.bind('<Double-Button-1>', open_item_details)


def on_mousewheel(event):
    if event.widget.winfo_toplevel() == root:
        canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')


DONATE_URL = 'https://www.paypal.com/ncp/payment/KUM5TR7ETF4QJ'


def open_donate():
    webbrowser.open(DONATE_URL)


data = load_runewords()
user_data = load_user_data()

root = tk.Tk()
root.title('Diablo 2 Runeword Tracker')
root.geometry('820x640')
root.minsize(680, 500)
root.configure(bg='#121212')

# Clam allows dark colors on Windows, including otherwise-native ttk fields.
scroll_style = ttk.Style(root)
scroll_style.theme_use('clam')
scroll_style.configure('.', background='#222222', foreground='#dddddd',
                       bordercolor='#333333', lightcolor='#333333',
                       darkcolor='#333333', troughcolor='#121212',
                       selectbackground='#454035', selectforeground='white')
scroll_style.configure('TCombobox', fieldbackground='#222222',
                       background='#333333', foreground='#dddddd',
                       arrowcolor='#aaaaaa', bordercolor='#333333', padding=4)
scroll_style.map('TCombobox',
                 fieldbackground=[('readonly', '#222222'), ('disabled', '#1a1a1a')],
                 foreground=[('disabled', '#666666'), ('readonly', '#dddddd')],
                 selectbackground=[('readonly', '#222222')],
                 selectforeground=[('readonly', '#dddddd')],
                 background=[('active', '#454545'), ('pressed', '#505050')])
# The expanded combobox is a Tk listbox, so it needs separate colors.
root.option_add('*TCombobox*Listbox.background', '#222222')
root.option_add('*TCombobox*Listbox.foreground', '#dddddd')
root.option_add('*TCombobox*Listbox.selectBackground', '#454035')
root.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')
root.option_add('*TCombobox*Listbox.highlightThickness', 0)
root.option_add('*TCombobox*Listbox.borderWidth', 0)
scroll_style.configure('Treeview', background='#1e1e1e',
                       fieldbackground='#1e1e1e', foreground='#dddddd',
                       borderwidth=0, relief='flat')
scroll_style.configure('Treeview.Heading', background='#292929',
                       foreground='#c9a85c', relief='flat', borderwidth=0,
                       font=('Segoe UI', 10, 'bold'), padding=(8, 7))
scroll_style.map('Treeview.Heading', background=[('active', '#383838'),
                                               ('pressed', '#454035')])
# Remove the native border; the unused area below the rows stays dark.
scroll_style.layout('RuneTotals.Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
scroll_style.configure('Horizontal.TProgressbar', background='#c9a85c',
                       troughcolor='#222222', bordercolor='#222222',
                       lightcolor='#c9a85c', darkcolor='#c9a85c')
root.option_add('*Spinbox.highlightThickness', 0)
root.option_add('*Spinbox.selectBackground', '#454035')
root.option_add('*Spinbox.selectForeground', '#ffffff')

for part in ('trough', 'thumb', 'uparrow', 'downarrow'):
    scroll_style.element_create(
        f'Dark.Vertical.Scrollbar.{part}', 'from', 'clam',
        f'Vertical.Scrollbar.{part}')
scroll_style.layout('Dark.Vertical.TScrollbar', [
    ('Dark.Vertical.Scrollbar.trough', {'sticky': 'ns', 'children': [
        ('Dark.Vertical.Scrollbar.uparrow', {'side': 'top', 'sticky': ''}),
        ('Dark.Vertical.Scrollbar.downarrow', {'side': 'bottom', 'sticky': ''}),
        ('Dark.Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'}),
    ]}),
])
scroll_style.configure(
    'Dark.Vertical.TScrollbar',
    troughcolor='#121212', background='#353535',
    bordercolor='#121212', lightcolor='#353535', darkcolor='#353535',
    arrowcolor='#aaaaaa', arrowsize=14, borderwidth=0,
)
scroll_style.map(
    'Dark.Vertical.TScrollbar',
    background=[('pressed', '#666666'), ('active', '#505050')],
    lightcolor=[('pressed', '#666666'), ('active', '#505050')],
    darkcolor=[('pressed', '#666666'), ('active', '#505050')],
    arrowcolor=[('disabled', '#454545'), ('active', '#dddddd')],
)

# Use bundled Zod image as the window/taskbar icon when available.
_app_icon = None
_icon_path = get_resource_path('zod.png')
if _icon_path.exists():
    try:
        _app_icon = tk.PhotoImage(file=str(_icon_path))
        root.iconphoto(True, _app_icon)
    except tk.TclError:
        pass

header = tk.Frame(root, bg='#121212')
header.pack(fill='x', padx=12, pady=(10, 4))
tk.Label(header, text='D2 Runeword Tracker', bg='#121212', fg='white', font=('Segoe UI', 16, 'bold')).pack(side='left', pady=(0, 5))

donate_button = make_smooth_button(
    header,
    text='Donate',
    command=open_donate,
    bg="#252525",
    fg='#dddddd',
    hover_bg='#3a3a3a',
    press_bg='#4a4a4a',
    font=('Segoe UI', 13, 'bold'),
    padx=100,
    pady=2,
    justify="right",
    anchor="center"
)
donate_button.pack(side='left', padx=(15, 0), pady=(0, 5))

progress_label = tk.Label(header, text='', bg='#121212', fg='#c9a85c', font=('Segoe UI', 9, 'bold'))
progress_label.pack(side='right')

progress_var = tk.DoubleVar(value=0)
progress_bar = ttk.Progressbar(
    root,
    variable=progress_var,
    maximum=100,
    mode='determinate',
)
progress_bar.pack(fill='x', padx=12, pady=(0, 4))

controls = tk.Frame(root, bg='#121212')
controls.pack(fill='x', padx=12, pady=4)

search_var = tk.StringVar()
search_var.trace_add('write', refresh_list)
search_entry = tk.Entry(
    controls,
    textvariable=search_var,
    bg='#222222',
    fg='white',
    insertbackground='white',
    relief='flat',
    font=('Segoe UI', 9),
    highlightthickness=1,
    highlightbackground='#2f2f2f',
    highlightcolor='#5a5a5a'
)
search_entry.pack(side='left', fill='x', expand=True, ipady=4)

filter_var = tk.StringVar(value='All')
filter_var.trace_add('write', refresh_list)
ttk.Combobox(controls, textvariable=filter_var, values=['All','Missing','Completed','Can craft','Missing 1 rune','Favorites'], state='readonly', width=12).pack(side='left', padx=5)

sort_var = tk.StringVar(value='Default')
sort_var.trace_add('write', refresh_list)
ttk.Combobox(controls, textvariable=sort_var, values=['Default','Name','Level','Craftable first'], state='readonly', width=12).pack(side='left', padx=(0, 5))

def open_main_menu():
    menu = tk.Menu(root, tearoff=0, bg='#222222', fg='#dddddd',
                   activebackground='#454035', activeforeground='white',
                   disabledforeground='#666666', relief='flat', bd=0,
                   activeborderwidth=0)
    menu.add_command(label='Rune Inventory', command=open_inventory)
    menu.add_command(label='Runes for Missing Runewords', command=open_missing_runes)
    menu.add_separator()
    menu.add_command(label='Reset completed', command=reset_completed)

    try:
        x = menu_button.winfo_rootx()
        y = menu_button.winfo_rooty() + menu_button.winfo_height()
        menu.tk_popup(x, y)
    finally:
        menu.grab_release()


menu_button = make_smooth_button(
    controls,
    text='☰',
    command=open_main_menu,
    bg='#333333',
    fg='white',
    hover_bg='#484848',
    press_bg='#5a5a5a',
    font=('Segoe UI', 11, 'bold'),
    width=3,
    padx=4,
    pady=3
)
menu_button.pack(side='left')

make_smooth_button(controls, text='Rune totals', command=open_missing_runes,
                   fg='#c9a85c', font=('Segoe UI', 9)).pack(side='left', padx=(5, 0))

status_label = tk.Label(root, text='', bg='#121212', fg='white', font=('Segoe UI', 8))
status_label.pack(fill='x', padx=12, pady=(0, 2))

list_container = tk.Frame(root, bg='#121212')
list_container.pack(fill='both', expand=True, padx=12, pady=(2, 10))
canvas = tk.Canvas(list_container, bg='#121212', highlightthickness=0)
scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=canvas.yview,
                          style='Dark.Vertical.TScrollbar')
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side='right', fill='y')
canvas.pack(side='left', fill='both', expand=True)
inner_frame = tk.Frame(canvas, bg='#121212')
window_id = canvas.create_window((0, 0), window=inner_frame, anchor='nw')
inner_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window_id, width=e.width))
canvas.bind_all('<MouseWheel>', on_mousewheel)

refresh_list()
if not data.get('items'):
    status_label.config(text='No runewords found in runewords.json.', fg='#aaaaaa')

root.mainloop()
