import json
import queue
import os
import re
import shutil
import sys
import time
import threading
import urllib.error
import urllib.request
import tkinter as tk
import webbrowser
from collections import Counter
from pathlib import Path
from tkinter import messagebox, ttk


APP_NAME = 'D2RunewordTracker'
APP_VERSION = '1.3.0'
UNDO_WINDOW_SECONDS = 30
UPDATE_CHECK_INTERVAL = 24 * 60 * 60
GITHUB_RELEASE_API = 'https://api.github.com/repos/sinnes7kx/D2-Runeword-Tracker/releases/latest'
GITHUB_RELEASES_URL = 'https://github.com/sinnes7kx/D2-Runeword-Tracker/releases/latest'


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



def version_numbers(version):
    """Compare stable, numeric GitHub release tags such as v1.3.1."""
    version = str(version).strip().lstrip('vV')
    if not re.fullmatch(r'\d+(?:\.\d+)*', version):
        return None
    return tuple(int(part) for part in version.split('.'))


def is_newer_version(remote, current=APP_VERSION):
    new, old = version_numbers(remote), version_numbers(current)
    if new is None or old is None:
        return False
    width = max(len(new), len(old))
    return new + (0,) * (width - len(new)) > old + (0,) * (width - len(old))


def fetch_latest_release():
    """Called only in a worker thread; never creates or modifies Tk widgets."""
    request = urllib.request.Request(
        GITHUB_RELEASE_API,
        headers={'Accept': 'application/vnd.github+json',
                 'User-Agent': 'D2RunewordTracker-UpdateCheck',
                 'X-GitHub-Api-Version': '2022-11-28'}
    )
    with urllib.request.urlopen(request, timeout=7) as response:
        release = json.load(response)
    tag = str(release.get('tag_name', ''))
    if not version_numbers(tag):
        raise ValueError('The latest release has an unsupported version tag.')
    return {
        'version': tag,
        'notes': str(release.get('body') or 'See GitHub for release details.'),
        # Use our fixed, trusted destination rather than a response-controlled URL.
        'url': GITHUB_RELEASES_URL,
    }


update_results = queue.Queue()
update_in_progress = False
update_popup = None


def show_update_popup(release):
    global update_popup
    if update_popup is not None and update_popup.winfo_exists():
        update_popup.lift()
        return
    popup = tk.Toplevel(root)
    update_popup = popup
    popup.title('D2 Runeword Tracker - Update available')
    popup.geometry('490x390')
    popup.minsize(420, 320)
    popup.configure(bg='#080808')
    popup.transient(root)

    tk.Label(popup, text='New version available!', bg='#080808',
             fg='#c9a85c', font=('Segoe UI', 17, 'bold')).pack(
                 anchor='w', padx=20, pady=(20, 7))
    tk.Label(popup, text=f"Installed: v{APP_VERSION}    Latest: {release['version']}",
             bg='#080808', fg='#dddddd', font=('Segoe UI', 10)).pack(
                 anchor='w', padx=20, pady=(0, 10))
    tk.Label(popup, text="What's new", bg='#080808', fg='#dddddd',
             font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=20)
    notes = tk.Text(popup, height=8, bg='#111111', fg='#dddddd',
                    insertbackground='#dddddd', wrap='word', relief='flat',
                    font=('Segoe UI', 9), padx=10, pady=10)
    notes.pack(fill='both', expand=True, padx=20, pady=(7, 12))
    notes.insert('1.0', release['notes'][:5000])
    notes.configure(state='disabled')
    buttons = tk.Frame(popup, bg='#080808')
    buttons.pack(fill='x', padx=20, pady=(0, 18))
    make_smooth_button(buttons, text='Remind me later', command=popup.destroy,
                       bg='#1c1c1c', hover_bg='#444444').pack(side='left')
    make_smooth_button(buttons, text='View / Download update',
                       command=lambda: (webbrowser.open(release['url']), popup.destroy()),
                       bg='#7055a5', hover_bg='#8069b5').pack(side='right')
    popup.bind('<Escape>', lambda _: popup.destroy())


def check_for_updates(manual=False):
    """Network requests run in a thread; all Tk interactions stay on main thread."""
    global update_in_progress
    if update_in_progress:
        if manual:
            messagebox.showinfo('Updates', 'An update check is already running.')
        return
    last = user_data.get('last_update_check', 0)
    if not manual and isinstance(last, (int, float)) and 0 <= time.time() - last < UPDATE_CHECK_INTERVAL:
        return
    update_in_progress = True

    def worker():
        try:
            update_results.put((manual, fetch_latest_release(), None))
        except Exception as exc:
            update_results.put((manual, None, exc))

    threading.Thread(target=worker, daemon=True).start()
    root.after(150, poll_update_results)


def poll_update_results():
    global update_in_progress
    try:
        manual, release, error = update_results.get_nowait()
    except queue.Empty:
        if root.winfo_exists():
            root.after(150, poll_update_results)
        return
    update_in_progress = False
    if error is not None:
        if manual:
            messagebox.showwarning('Update check failed',
                                   'Unable to check GitHub Releases. Check your internet connection and try again.')
        return
    user_data['last_update_check'] = time.time()
    save_all()
    if is_newer_version(release['version']):
        # Avoid showing the same release on every startup after 'Later'.
        if manual or user_data.get('dismissed_update_version') != release['version']:
            show_update_popup(release)
            if not manual:
                user_data['dismissed_update_version'] = release['version']
                save_all()
    elif manual:
        messagebox.showinfo('No updates', f'You are running the latest version (v{APP_VERSION}).')


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


def animate_button_bg(button, start, end, steps=4, delay=22):
    """Ease between dark-theme colors. Repeated mouse events retarget in flight."""
    if not button.winfo_exists():
        return
    button._anim_token = getattr(button, '_anim_token', 0) + 1
    token = button._anim_token
    if start == end:
        return

    def step(i=1):
        try:
            if (not button.winfo_exists()
                    or getattr(button, '_anim_token', None) != token):
                return
            t = i / steps
            # Cubic ease-out feels softer than a linear fade.
            eased = 1 - (1 - t) ** 3
            button.configure(bg=_blend_color(start, end, eased))
            if i < steps:
                button.after(delay, lambda: step(i + 1))
        except tk.TclError:
            # A refresh can destroy row buttons during an active transition.
            return

    step()


def make_smooth_button(parent,
                       *,
                       text,
                       command,
                       bg='#242424',
                       fg='#dddddd',
                       hover_bg='#444444',
                       press_bg='#393939',
                       active_fg='#ffffff',
                       font=('Segoe UI', 10),
                       width=None,
                       padx=8,
                       pady=4,
                       bd=0,
                       **kwargs):
    """Smooth hover and pressed-state easing with proper release-outside behavior."""
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg,
        activebackground=press_bg, activeforeground=active_fg,
        relief='flat', bd=bd, font=font, cursor='hand2',
        padx=padx, pady=pady, highlightthickness=0,
        takefocus=True, **kwargs
    )
    if width is not None:
        btn.configure(width=width)

    btn._is_pressed = False
    btn._base_bg = bg
    btn._hover_bg = hover_bg
    btn._press_bg = press_bg

    def transition(target, duration_steps=4):
        animate_button_bg(btn, btn.cget('bg'), target,
                          steps=duration_steps, delay=16)

    def on_enter(_):
        transition(btn._press_bg if btn._is_pressed else btn._hover_bg)

    def on_leave(_):
        transition(btn._base_bg)

    def on_press(_):
        btn._is_pressed = True
        transition(btn._press_bg, duration_steps=3)

    def on_release(event):
        btn._is_pressed = False
        # Buttons remain pressed while held; release fades out smoothly.
        try:
            inside = (btn.winfo_containing(event.x_root, event.y_root) == btn)
        except tk.TclError:
            return
        transition(btn._hover_bg if inside else btn._base_bg, duration_steps=4)

    btn.bind('<Enter>', on_enter, add='+')
    btn.bind('<Leave>', on_leave, add='+')
    btn.bind('<ButtonPress-1>', on_press, add='+')
    btn.bind('<ButtonRelease-1>', on_release, add='+')
    return btn


def apply_dark_row_hover(row):
    """Lightweight near-black hover; only one paint per row-state change."""
    base = '#111111'
    highlighted = '#191919'
    surfaces = []

    def gather(widget):
        if isinstance(widget, (tk.Frame, tk.Label)):
            surfaces.append(widget)
        for child in widget.winfo_children():
            if not isinstance(child, tk.Button):
                gather(child)

    gather(row)
    row._hovered = False
    row._hover_job = None

    def set_hover(value):
        if not row.winfo_exists() or value == row._hovered:
            return
        row._hovered = value
        color = highlighted if value else base
        try:
            for widget in surfaces:
                widget.configure(bg=color)
        except tk.TclError:
            pass

    def inside_row():
        try:
            x, y = row.winfo_pointerxy()
            widget = row.winfo_containing(x, y)
            while widget is not None:
                if widget == row:
                    return True
                widget = widget.master
        except tk.TclError:
            pass
        return False

    def on_enter(_):
        if row._hover_job is not None:
            row.after_cancel(row._hover_job)
            row._hover_job = None
        set_hover(True)

    def on_leave(_):
        if row._hover_job is not None:
            row.after_cancel(row._hover_job)
        def check():
            row._hover_job = None
            set_hover(inside_row())
        row._hover_job = row.after(28, check)

    # Bind only the row/labels; no repeated per-frame color repaints.
    for widget in surfaces:
        widget.bind('<Enter>', on_enter, add='+')
        widget.bind('<Leave>', on_leave, add='+')


def get_runeword_state(name):
    state = user_data['runewords'].setdefault(name, {'completed': False, 'favorite': False})
    state.setdefault('completed', False)
    state.setdefault('favorite', False)
    return state


def get_item_by_name(name):
    return next((item for item in data.get('items', []) if item.get('name') == name), None)


def get_refund_seconds_left(state, now=None):
    """A refund is possible only for an inventory deduction made by v1.3."""
    transaction = state.get('rune_transaction')
    if not state.get('completed') or not isinstance(transaction, dict):
        return 0
    spent = transaction.get('spent')
    timestamp = transaction.get('timestamp')
    if not isinstance(spent, dict) or not spent or not isinstance(timestamp, (int, float)):
        return 0
    if not all(isinstance(n, int) and not isinstance(n, bool) and n > 0 for n in spent.values()):
        return 0
    now = time.time() if now is None else now
    elapsed = now - timestamp
    if elapsed < 0 or elapsed >= UNDO_WINDOW_SECONDS:
        return 0
    return max(0, UNDO_WINDOW_SECONDS - elapsed)


def restore_runeword(name, now=None, *, notify=True, persist=True):
    """Uncheck a runeword; refund only an eligible, recorded deduction."""
    state = get_runeword_state(name)
    if not state['completed']:
        return False
    transaction = state.get('rune_transaction')
    refund = transaction['spent'] if get_refund_seconds_left(state, now) else {}
    if not refund and transaction and notify:
        if not messagebox.askyesno(
            'Undo period expired',
            'The 30-second rune refund period has expired.\n\n'
            'Restore this runeword to Not completed WITHOUT returning runes?'
        ):
            return False
    # Clear the transaction whether it was refunded or expired: never refund twice.
    for rune, amount in refund.items():
        user_data['inventory'][rune] = max(0, int(user_data['inventory'].get(rune, 0))) + amount
    state['completed'] = False
    state.pop('rune_transaction', None)
    if persist:
        save_all()
    return bool(refund)


def toggle_completed(name):
    state = get_runeword_state(name)
    if state['completed']:
        before = state['completed']
        restore_runeword(name)
        if state['completed'] != before:
            refresh_after_inventory_change()
        return

    item = get_item_by_name(name)
    if item is None:
        messagebox.showerror('Runeword not found', f'Cannot find {name} in runewords.json.')
        return
    needed = Counter(item.get('runes', []))
    missing = get_missing_runes(item)
    if missing:
        # Existing users may track runewords acquired elsewhere, not crafted
        # from runes entered in this application.
        if not messagebox.askyesno(
            'Runes not in inventory',
            f'You do not have all the runes listed for {name}.\n\n'
            f'{format_missing(missing)}\n\n'
            'Mark it Completed without deducting any runes?\n'
            '(Restoring it will not add any runes.)'
        ):
            return
        state.pop('rune_transaction', None)
    elif needed:
        # Save the exact amount actually spent, so later changes to the
        # runeword database cannot change the refund amount.
        for rune, amount in needed.items():
            user_data['inventory'][rune] = int(user_data['inventory'].get(rune, 0)) - amount
        state['rune_transaction'] = {
            'spent': dict(needed),
            'timestamp': time.time(),
        }
    else:
        state.pop('rune_transaction', None)

    state['completed'] = True
    save_all()
    refresh_after_inventory_change()


def toggle_favorite(name):
    state = get_runeword_state(name)
    state['favorite'] = not state['favorite']
    save_all()
    refresh_after_inventory_change()


def reset_completed():
    eligible = sum(bool(get_refund_seconds_left(state))
                   for state in user_data['runewords'].values())
    text = ('Uncheck every completed runeword?\n\n'
            f'{eligible} recently crafted runeword(s) will have their runes refunded.\n'
            'Older deductions cannot be refunded.')
    if not messagebox.askyesno('Reset checklist', text):
        return
    for name in list(user_data['runewords']):
        restore_runeword(name, notify=False, persist=False)
    save_all()
    refresh_after_inventory_change()


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
    win.configure(bg='#080808')
    tk.Label(win, text='Runes for Missing Runewords', bg='#080808',
             fg='white', font=('Segoe UI', 18, 'bold')).pack(
                 anchor='w', padx=20, pady=(20, 8))
    tk.Label(win, text='One copy of every uncompleted runeword, regardless of search or filter.\n'
             'Inventory is deducted once from the combined requirements.\n'
             'Direct rune requirements only; cube upgrades are not included.',
             bg='#080808', fg='#aaaaaa', font=('Segoe UI', 9),
             justify='left', anchor='w').pack(fill='x', padx=20)

    summary = tk.Label(win, bg='#080808', fg='#c9a85c',
                       font=('Segoe UI', 10, 'bold'), justify='left', anchor='w')
    summary.pack(fill='x', padx=20, pady=14)

    style = ttk.Style(win)
    style.configure('RuneTotals.Treeview', background='#111111',
                    fieldbackground='#111111', foreground='#dddddd',
                    rowheight=28, font=('Segoe UI', 10))
    style.map('RuneTotals.Treeview', background=[('selected', '#454035')],
              foreground=[('selected', 'white')])
    table_frame = tk.Frame(win, bg='#080808')
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
    table.tag_configure('needed', foreground='#c9a85c')
    table.tag_configure('covered', foreground='#9bcfa9')

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
    buttons = tk.Frame(win, bg='#080808')
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
    win.configure(bg='#080808')
    win.resizable(False, False)

    tk.Label(win, text=item['name'], bg='#080808', fg='white', font=('Segoe UI', 20, 'bold')).pack(anchor='w', padx=20, pady=(20, 8))

    details = [
        f"Runes: {' → '.join(item.get('runes', []))}",
        f"Sockets: {item.get('sockets') or '-'}",
        f"Required level: {item.get('level') or '-'}",
        f"Craftable copies: {craft_count(item)}",
        f"Status: {'Completed' if state['completed'] else 'Not completed'}",
        format_missing(missing),
    ]

    for text in details[:2]:
        tk.Label(win, text=text, bg='#080808', fg='#c9a85c' if text.startswith('Runes:') else '#dddddd', font=('Segoe UI', 10, 'bold'), anchor='w', justify='left', wraplength=560).pack(fill='x', padx=20, pady=3)

    bases = item.get('bases', [])
    base_row = tk.Frame(win, bg='#080808')
    base_row.pack(fill='x', padx=20, pady=3)
    tk.Label(base_row, text='Bases:', bg='#080808', fg='#dddddd', font=('Segoe UI', 10, 'bold')).pack(side='left')
    if bases:
        tk.Label(base_row, text=get_base_icon(bases), bg='#080808', fg='white', font=('Segoe UI Symbol', 16, 'bold')).pack(side='left', padx=(6, 5))
        tk.Label(base_row, text=', '.join(bases), bg='#080808', fg='#dddddd', font=('Segoe UI', 10, 'bold')).pack(side='left')
    else:
        tk.Label(base_row, text='-', bg='#080808', fg='#dddddd', font=('Segoe UI', 10, 'bold')).pack(side='left', padx=(6, 0))

    for text in details[2:]:
        tk.Label(win, text=text, bg='#080808', fg='#dddddd', font=('Segoe UI', 10, 'bold'), anchor='w', justify='left', wraplength=560).pack(fill='x', padx=20, pady=3)

    tk.Label(win, text='Stats', bg='#080808', fg='white', font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=20, pady=(16, 5))
    stats = tk.Text(win, bg='#111111', fg='#dddddd', insertbackground='white', relief='flat', wrap='word', height=18, padx=10, pady=10)
    stats.pack(fill='both', expand=True, padx=20, pady=(0, 20))

    stats.insert('1.0', item.get('stats', '') or 'No stats available.')


    stats.tag_configure('variable_roll', foreground='#d5b978', font=('Segoe UI', 10))
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
    win.configure(bg='#080808')

    tk.Label(win, text='Rune Inventory', bg="#080808", fg='white', font=('Segoe UI', 20, 'bold')).pack(anchor='w', padx=20, pady=(20, 4))
    tk.Label(win, text='Runes are spent on completion. Restore within 30 seconds to refund.', bg='#080808', fg='#aaaaaa', font=('Segoe UI', 10)).pack(anchor='w', padx=20, pady=(0, 12))

    outer = tk.Frame(win, bg='#080808')
    outer.pack(fill='both', expand=True, padx=20, pady=(0, 20))
    canvas_inv = tk.Canvas(outer, bg='#080808', highlightthickness=0)
    scrollbar_inv = ttk.Scrollbar(outer, orient='vertical', command=canvas_inv.yview,
                                  style='Dark.Vertical.TScrollbar')
    canvas_inv.configure(yscrollcommand=scrollbar_inv.set)
    scrollbar_inv.pack(side='right', fill='y')
    canvas_inv.pack(side='left', fill='both', expand=True)

    frame = tk.Frame(canvas_inv, bg='#080808')
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
        refresh_after_inventory_change()

    for rune in RUNE_ORDER:
        row = tk.Frame(frame, bg='#111111', padx=10, pady=7)
        row.pack(fill='x', pady=2)
        tk.Label(row, text=rune, bg='#111111', fg='white', font=('Segoe UI', 11, 'bold'), width=10, anchor='w').pack(side='left')

        var = tk.StringVar(value=str(user_data['inventory'].get(rune, 0)))
        spin = tk.Spinbox(row, from_=0, to=999, textvariable=var, width=8, bg='#1c1c1c', fg='white', insertbackground='white', buttonbackground='#242424', relief='flat', font=('Segoe UI', 10), command=lambda r=rune, v=var: commit(r, v))
        spin.pack(side='right')
        spin.bind('<FocusOut>', lambda e, r=rune, v=var: commit(r, v))
        spin.bind('<Return>', lambda e, r=rune, v=var: commit(r, v))


# Only redraw after a short typing pause; avoid rebuilding hundreds of rows
# for every single keystroke in the search box.
_search_refresh_job = None
_refund_labels = []
_visible_rows = {}  # runeword name -> references to widgets for in-place updates


def schedule_search_refresh(*_):
    global _search_refresh_job
    if _search_refresh_job is not None:
        root.after_cancel(_search_refresh_job)
    _search_refresh_job = root.after(140, refresh_after_search)


def refresh_after_search():
    global _search_refresh_job
    _search_refresh_job = None
    refresh_list(reset_scroll=True)


def update_refund_countdowns():
    # Update only the text of visible refund labels, rather than rebuilding the list.
    active = []
    for label, name in _refund_labels:
        if not label.winfo_exists():
            continue
        seconds = get_refund_seconds_left(get_runeword_state(name))
        label.configure(text=(f'Completed • Undo rune deduction: {max(1, int(seconds + 0.999))}s left'
                              if seconds else 'Completed'))
        if seconds:
            active.append((label, name))
    _refund_labels[:] = active
    root.after(500 if active else 1000, update_refund_countdowns)


def update_summary():
    all_items = data.get('items', [])
    total = len(all_items)
    completed = sum(bool(get_runeword_state(i['name'])['completed']) for i in all_items)
    remaining = total - completed
    percent = round(completed / total * 100) if total else 0
    craftable_total = sum(can_craft(i) for i in all_items)
    progress_label.configure(
        text=f'{percent}% Completed   •   {remaining} Remaining   •   {craftable_total} Craftable'
    )
    progress_var.set(percent)
    if missing_runes_window is not None and missing_runes_window.winfo_exists():
        missing_runes_window.refresh_totals()


def update_row_in_place(item, refs):
    """Update visible row widgets without destroying or recreating them."""
    state = get_runeword_state(item['name'])
    completed = bool(state['completed'])
    missing = get_missing_runes(item)
    status = 'Completed'
    if completed:
        left = get_refund_seconds_left(state)
        if left:
            status = f'Completed • Undo rune deduction: {max(1, int(left + 0.999))}s left'
    else:
        status = format_missing(missing)
        if not missing:
            status += f'   •   Can craft {craft_count(item)}'
    refs['title'].configure(fg='#888888' if completed else '#ffffff')
    for widget in refs['details']:
        widget.configure(fg='#888888' if completed else '#c9a85c')
    refs['status'].configure(
        text=status,
        fg='#888888' if completed else ('#9bcfa9' if not missing else '#c9a85c')
    )
    refs['favorite'].configure(text='★' if state['favorite'] else '☆',
                                fg='#d5b978' if state['favorite'] else '#8a8a8a')
    button = refs['complete']
    button.configure(text='↩' if completed else '✔',
                     fg='#d8e8df' if completed else '#ffffff',
                     activebackground='#363636' if completed else '#477b5b')
    # Animation callbacks look these up dynamically, so retarget future hovers.
    button._base_bg = '#1b211e' if completed else '#1c1c1c'
    button._hover_bg = '#303030' if completed else '#477b5b'
    button._press_bg = '#625a49' if completed else '#477b5b'
    if not getattr(button, '_is_pressed', False):
        button._anim_token = getattr(button, '_anim_token', 0) + 1
        button.configure(bg=button._base_bg)
    if completed and get_refund_seconds_left(state):
        _refund_labels.append((refs['status'], item['name']))


def refresh_after_inventory_change():
    """Fast path: use existing widgets if the visible list/order hasn't changed."""
    desired = get_filtered_items()
    # Filters and 'Craftable first' sorting may change list membership/order.
    if list(_visible_rows) != [item['name'] for item in desired]:
        refresh_list()
        return
    _refund_labels.clear()
    for item in desired:
        update_row_in_place(item, _visible_rows[item['name']])
    update_summary()


def refresh_list(*_, reset_scroll=False):
    if missing_runes_window is not None and missing_runes_window.winfo_exists():
        missing_runes_window.refresh_totals()
    scroll_position = 0.0 if reset_scroll else canvas.yview()[0]
    _refund_labels.clear()
    _visible_rows.clear()
    for widget in inner_frame.winfo_children():
        widget.destroy()

    items = get_filtered_items()
    update_summary()

    if not items:
        tk.Label(inner_frame, text='No runewords to show.', bg='#080808', fg='#999999', font=('Segoe UI', 11)).pack(pady=30)
        return

    for item in items:
        state = get_runeword_state(item['name'])
        completed = state['completed']
        favorite = state['favorite']
        missing = get_missing_runes(item)
        copies = craft_count(item)

        row = tk.Frame(inner_frame, bg='#111111', padx=7, pady=4)
        row.pack(fill='x', pady=2)

        favorite_btn = make_smooth_button(
            row,
            text='★' if favorite else '☆',
            command=lambda n=item['name']: toggle_favorite(n),
            bg='#111111',
            fg='#d5b978' if favorite else '#8a8a8a',
            hover_bg='#242424',
            press_bg='#3c3c3c',
            active_fg='#d5b978',
            font=('Segoe UI', 12),
            width=2,
            padx=2,
            pady=2
        )
        favorite_btn.pack(side='left', padx=(0, 8))

        left = tk.Frame(row, bg='#111111')
        left.pack(side='left', fill='x', expand=True)

        title = item['name'] + (f"  •  Req lvl {item['level']}" if item.get('level') is not None else '')
        title_label = tk.Label(left, text=title, bg='#111111', fg='#888888' if completed else '#ffffff', font=('Segoe UI', 10, 'bold'), anchor='w')
        title_label.pack(fill='x')

        details = ' → '.join(item.get('runes', []))
        if item.get('sockets'):
            details += f"   |   {item['sockets']} sockets"
        bases = item.get('bases', [])
        base_text = ', '.join(bases)

        details_row = tk.Frame(left, bg='#111111')
        details_row.pack(fill='x', pady=(3, 0))

        tk.Label(
            details_row,
            text=details,
            bg='#111111',
            fg='#888888' if completed else '#c9a85c',
            font=('Segoe UI', 8),
            anchor='w',
            justify='left'
        ).pack(side='left')

        if bases:
            tk.Label(
                details_row,
                text='   |   ',
                bg='#111111',
                fg='#888888' if completed else '#c9a85c',
                font=('Segoe UI', 8)
            ).pack(side='left')

            tk.Label(
                details_row,
                text=get_base_icon(bases),
                bg='#111111',
                fg='white',
                font=('Segoe UI Symbol', 14, 'bold')
            ).pack(side='left', padx=(0, 4))

            tk.Label(
                details_row,
                text=base_text,
                bg='#111111',
                fg='#888888' if completed else '#c9a85c',
                font=('Segoe UI', 8),
                anchor='w'
            ).pack(side='left')

        status = format_missing(missing)
        if completed:
            seconds_left = get_refund_seconds_left(state)
            if seconds_left:
                status = f'Completed • Undo rune deduction: {max(1, int(seconds_left + 0.999))}s left'
            else:
                status = 'Completed'
        elif not missing:
            status += f'   •   Can craft {copies}'
        detail_widgets = [w for w in details_row.winfo_children()
                          if isinstance(w, tk.Label) and w.cget('fg') != 'white']
        status_widget = tk.Label(left, text=status, bg='#111111', fg='#888888' if completed else ('#9bcfa9' if not missing else '#c9a85c'), font=('Segoe UI', 8), anchor='w')
        status_widget.pack(fill='x', pady=(1, 0))
        if completed and get_refund_seconds_left(state):
            _refund_labels.append((status_widget, item['name']))

        details_btn = make_smooth_button(
            row,
            text='…',
            command=lambda current=item: open_details(current),
            bg='#1c1c1c',
            hover_bg='#303030',
            press_bg='#303030',
            font=('Segoe UI', 10, 'bold'),
            width=2,
            padx=2,
            pady=1,
            anchor="center",
        )
        details_btn.pack(side='right', padx=(4, 0))

        complete_bg = '#1b211e' if completed else '#1c1c1c'

        completed_btn = make_smooth_button(
            row,
            text='↩' if completed else '✔',
            command=lambda n=item['name']: toggle_completed(n),
            bg=complete_bg,
            fg='#d8e8df' if completed else '#ffffff',
            hover_bg='#303030' if completed else '#477b5b',
            press_bg='#625a49' if completed else '#477b5b',
            active_fg='#ffffff',
            font=('Segoe UI', 11, 'bold'),
            width=3,
            padx=7,
            pady=1,
            bd=1,
        )

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

        apply_dark_row_hover(row)
        _visible_rows[item['name']] = {
            'row': row, 'title': title_label, 'details': detail_widgets,
            'status': status_widget, 'favorite': favorite_btn,
            'complete': completed_btn,
        }

    # Refresh layout before restoring scroll offset; this retains user's place
    # when a favorite or completion changes.
    inner_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox('all'))
    canvas.yview_moveto(scroll_position)


def on_mousewheel(event):
    if event.widget.winfo_toplevel() == root:
        canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')


DONATE_URL = 'https://www.paypal.com/donate/?hosted_button_id=H5QKDWLF92MXN'


def open_donate():
    webbrowser.open(DONATE_URL)


data = load_runewords()
user_data = load_user_data()

root = tk.Tk()
root.title(f'Diablo 2 Runeword Tracker v{APP_VERSION}')
root.geometry('820x640')
root.minsize(680, 500)
root.configure(bg='#080808')

# Clam allows dark colors on Windows, including otherwise-native ttk fields.
scroll_style = ttk.Style(root)
scroll_style.theme_use('clam')
scroll_style.configure('.', background='#161616', foreground='#dddddd',
                       bordercolor='#242424', lightcolor='#242424',
                       darkcolor='#242424', troughcolor='#080808',
                       selectbackground='#454035', selectforeground='white')
scroll_style.configure('TCombobox', fieldbackground='#161616',
                       background='#242424', foreground='#dddddd',
                       arrowcolor='#aaaaaa', bordercolor='#242424', padding=4)
scroll_style.map('TCombobox',
                 fieldbackground=[('readonly', '#161616'), ('disabled', '#1a1a1a')],
                 foreground=[('disabled', '#777777'), ('readonly', '#dddddd')],
                 selectbackground=[('readonly', '#161616')],
                 selectforeground=[('readonly', '#dddddd')],
                 background=[('active', '#303030'), ('pressed', '#363636')])
# The expanded combobox is a Tk listbox, so it needs separate colors.
root.option_add('*TCombobox*Listbox.background', '#161616')
root.option_add('*TCombobox*Listbox.foreground', '#dddddd')
root.option_add('*TCombobox*Listbox.selectBackground', '#454035')
root.option_add('*TCombobox*Listbox.selectForeground', '#ffffff')
root.option_add('*TCombobox*Listbox.highlightThickness', 0)
root.option_add('*TCombobox*Listbox.borderWidth', 0)
scroll_style.configure('Treeview', background='#111111',
                       fieldbackground='#111111', foreground='#dddddd',
                       borderwidth=0, relief='flat')
scroll_style.configure('Treeview.Heading', background='#1c1c1c',
                       foreground='#c9a85c', relief='flat', borderwidth=0,
                       font=('Segoe UI', 10, 'bold'), padding=(8, 7))
scroll_style.map('Treeview.Heading', background=[('active', '#272727'),
                                               ('pressed', '#454035')])
# Remove the native border; the unused area below the rows stays dark.
scroll_style.layout('RuneTotals.Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
scroll_style.configure('Horizontal.TProgressbar', background='#c9a85c',
                       troughcolor='#161616', bordercolor='#161616',
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
    troughcolor='#080808', background='#252525',
    bordercolor='#080808', lightcolor='#252525', darkcolor='#252525',
    arrowcolor='#aaaaaa', arrowsize=14, borderwidth=0,
)
scroll_style.map(
    'Dark.Vertical.TScrollbar',
    background=[('pressed', '#777777'), ('active', '#363636')],
    lightcolor=[('pressed', '#777777'), ('active', '#363636')],
    darkcolor=[('pressed', '#777777'), ('active', '#363636')],
    arrowcolor=[('disabled', '#303030'), ('active', '#dddddd')],
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

header = tk.Frame(root, bg='#080808')
header.pack(fill='x', padx=12, pady=(10, 4))
tk.Label(header, text='D2 Runeword Tracker', bg='#080808', fg='white', font=('Segoe UI', 16, 'bold')).pack(side='left', pady=(0, 5))

donate_button = make_smooth_button(
    header,
    text='Donate',
    command=open_donate,
    bg="#252525",
    fg='#dddddd',
    hover_bg='#3a3a3a',
    press_bg='#4a4a4a',
    font=('Segoe UI', 13, 'bold'),
    padx=20,
    pady=2,
    justify="right",
    anchor="center"
)
donate_button.pack(side='left', padx=(15, 0), pady=(0, 5))

progress_label = tk.Label(header, text='', bg='#080808', fg='#c9a85c', font=('Segoe UI', 9, 'bold'))
progress_label.pack(side='right')

progress_var = tk.DoubleVar(value=0)
progress_bar = ttk.Progressbar(
    root,
    variable=progress_var,
    maximum=100,
    mode='determinate',
)
progress_bar.pack(fill='x', padx=12, pady=(0, 4))

controls = tk.Frame(root, bg='#080808')
controls.pack(fill='x', padx=12, pady=4)

search_var = tk.StringVar()
search_var.trace_add('write', schedule_search_refresh)
search_entry = tk.Entry(
    controls,
    textvariable=search_var,
    bg='#161616',
    fg='white',
    insertbackground='white',
    relief='flat',
    font=('Segoe UI', 9),
    highlightthickness=1,
    highlightbackground='#242424',
    highlightcolor='#393939'
)
search_entry.pack(side='left', fill='x', expand=True, ipady=4)

def unfocus_search_on_outside_click(event):
    """Click any other part of the main window to release search focus."""
    try:
        if (root.focus_get() == search_entry
                and event.widget is not search_entry
                and event.widget.winfo_toplevel() == root):
            root.focus_set()
    except tk.TclError:
        pass


def animate_search_focus(focused):
    search_entry.configure(
        highlightbackground='#444444' if focused else '#242424',
        highlightcolor='#c9a85c' if focused else '#393939',
    )
    animate_button_bg(search_entry, search_entry.cget('bg'),
                      '#202020' if focused else '#161616',
                      steps=9, delay=16)

search_entry.bind('<FocusIn>', lambda _: animate_search_focus(True), add='+')
search_entry.bind('<FocusOut>', lambda _: animate_search_focus(False), add='+')
search_entry.bind('<Escape>', lambda _: root.focus_set(), add='+')
root.bind_all('<Button-1>', unfocus_search_on_outside_click, add='+')


filter_var = tk.StringVar(value='All')
filter_var.trace_add('write', lambda *_: refresh_list(reset_scroll=True))
ttk.Combobox(controls, textvariable=filter_var, values=['All','Missing','Completed','Can craft','Missing 1 rune','Favorites'], state='readonly', width=12).pack(side='left', padx=5)

sort_var = tk.StringVar(value='Default')
sort_var.trace_add('write', lambda *_: refresh_list(reset_scroll=True))
ttk.Combobox(controls, textvariable=sort_var, values=['Default','Name','Level','Craftable first'], state='readonly', width=12).pack(side='left', padx=(0, 5))

def open_main_menu():
    menu = tk.Menu(root, tearoff=0, bg='#161616', fg='#dddddd',
                   activebackground='#454035', activeforeground='white',
                   disabledforeground='#777777', relief='flat', bd=0,
                   activeborderwidth=0)
    menu.add_command(label='Rune Inventory', command=open_inventory)
    menu.add_command(label='Runes for Missing Runewords', command=open_missing_runes)
    menu.add_separator()
    menu.add_command(label='Reset completed', command=reset_completed)
    menu.add_separator()
    menu.add_command(label='Check for updates', command=lambda: check_for_updates(manual=True))

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
    bg='#242424',
    fg='white',
    hover_bg='#303030',
    press_bg='#393939',
    font=('Segoe UI', 11, 'bold'),
    width=3,
    padx=4,
    pady=3
)
menu_button.pack(side='left')

make_smooth_button(controls, text='Rune totals', command=open_missing_runes,
                   fg='#c9a85c', font=('Segoe UI', 9)).pack(side='left', padx=(5, 0))

status_label = tk.Label(root, text='', bg='#080808', fg='white', font=('Segoe UI', 8))
status_label.pack(fill='x', padx=12, pady=(0, 2))

list_container = tk.Frame(root, bg='#080808')
list_container.pack(fill='both', expand=True, padx=12, pady=(2, 10))
canvas = tk.Canvas(list_container, bg='#080808', highlightthickness=0)
scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=canvas.yview,
                          style='Dark.Vertical.TScrollbar')
canvas.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side='right', fill='y')
canvas.pack(side='left', fill='both', expand=True)
inner_frame = tk.Frame(canvas, bg='#080808')
window_id = canvas.create_window((0, 0), window=inner_frame, anchor='nw')
inner_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
canvas.bind('<Configure>', lambda e: canvas.itemconfigure(window_id, width=e.width))
canvas.bind_all('<MouseWheel>', on_mousewheel)

refresh_list()
if not data.get('items'):
    status_label.config(text='No runewords found in runewords.json.', fg='#aaaaaa')

root.after(500, update_refund_countdowns)
root.after(2500, check_for_updates)
root.mainloop()
