
from collections import Counter
import csv
import math
import os
import re
import random

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, BooleanProperty, StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.core.window import Window

# ---------- Storage Helpers ----------

def get_store_path():
    # Use app directory per platform
    if platform == "android":
        # On Android, use app's files dir
        try:
            from android.storage import app_storage_path
            app_dir = app_storage_path()
        except Exception:
            app_dir = os.getcwd()
    else:
        app_dir = os.getcwd()
    return os.path.join(app_dir, "lotto_data.json")

def get_downloads_path():
    # Try Downloads directory for export
    if platform == "android":
        try:
            from android.storage import primary_external_storage_path
            base = primary_external_storage_path()
            dl = os.path.join(base, "Download")
            if os.path.isdir(dl):
                return dl
            return base
        except Exception:
            return os.getcwd()
    else:
        # Desktop fallback
        home = os.path.expanduser("~")
        dl = os.path.join(home, "Downloads")
        return dl if os.path.isdir(dl) else os.getcwd()

# ---------- Core Logic ----------

def valid_six(nums):
    if len(nums) != 6:
        return False
    if len(set(nums)) != 6:
        return False
    return all(1 <= n <= 45 for n in nums)

def next_round_label(rows):
    # rows: list of dicts {"round": str, "nums": [6 ints]}
    if not rows:
        return "1회"
    last = rows[-1]["round"]
    m = re.search(r"\d+", str(last))
    base = int(m.group()) if m else len(rows)
    return f"{base+1}회"

def frequency_counts(rows, recent_k=0):
    # rows: [{"round":..., "nums":[..]}]
    target = rows[-recent_k:] if (recent_k and recent_k > 0) else rows
    cnt = Counter()
    for r in target:
        for n in r["nums"]:
            if 1 <= n <= 45:
                cnt[n] += 1
    # return list of counts indexed 1..45
    return [cnt.get(i, 0) for i in range(1, 46)]

def weighted_probabilities(counts, alpha=1.0, beta=1.0):
    # counts: len 45
    weights = [((c + alpha) ** beta) for c in counts]
    total = sum(weights)
    if total <= 0:
        # uniform
        weights = [1.0] * 45
        total = 45.0
    probs = [w / total for w in weights]
    return probs

def sample_without_replacement(numbers, probs, k=6):
    # numbers: list of ints, probs aligned
    # simple weighted sampling without replacement via sequential draws
    chosen = []
    available = list(numbers)
    weights = list(probs)
    for _ in range(k):
        # normalize
        s = sum(weights)
        if s <= 0:
            # fallback uniform among remaining
            idx = random.randrange(len(available))
        else:
            r = random.random()
            acc = 0.0
            idx = 0
            for i, w in enumerate(weights):
                acc += w / s
                if r <= acc:
                    idx = i
                    break
        chosen.append(available[idx])
        # remove chosen
        available.pop(idx)
        weights.pop(idx)
    return sorted(chosen)

def combos_set(rows):
    return {tuple(sorted(r["nums"])) for r in rows}

def parse_paste(text):
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        nums = list(map(int, re.findall(r"\d+", line)))
        if len(nums) < 6:
            continue
        nums = nums[:6]
        if not valid_six(nums):
            continue
        m = re.search(r"(\d+)\s*회", line)
        rlabel = f"{m.group(1)}회" if m else ""
        out.append({"round": rlabel, "nums": sorted(nums)})
    return out

# ---------- Kivy App ----------

KV = r"""
#:import dp kivy.metrics.dp

<LabeledInput@BoxLayout>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(40)
    Label:
        text: root.label if hasattr(root, "label") else ""
        size_hint_x: 0.55
    TextInput:
        id: ti
        multiline: False
        input_filter: "float"
        size_hint_x: 0.45

<NumRow@BoxLayout>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(40)
    spacing: dp(6)
    Label:
        text: "번호 6개:"
        size_hint_x: 0.35
    # 6 number fields 1..45
    TextInput:
        id: n1; hint_text: "1"; multiline: False; input_filter: "int"
    TextInput:
        id: n2; hint_text: "2"; multiline: False; input_filter: "int"
    TextInput:
        id: n3; hint_text: "3"; multiline: False; input_filter: "int"
    TextInput:
        id: n4; hint_text: "4"; multiline: False; input_filter: "int"
    TextInput:
        id: n5; hint_text: "5"; multiline: False; input_filter: "int"
    TextInput:
        id: n6; hint_text: "6"; multiline: False; input_filter: "int"

BoxLayout:
    orientation: "vertical"
    padding: dp(12)
    spacing: dp(10)

    # Parameters
    BoxLayout:
        size_hint_y: None
        height: dp(140)
        spacing: dp(10)
        BoxLayout:
            orientation: "vertical"
            Label: text: "α (Laplace)"
            TextInput:
                id: alpha_in
                text: "1.0"
                multiline: False
                input_filter: "float"
        BoxLayout:
            orientation: "vertical"
            Label: text: "β (쏠림 강도)"
            TextInput:
                id: beta_in
                text: "1.0"
                multiline: False
                input_filter: "float"
        BoxLayout:
            orientation: "vertical"
            Label: text: "최근 K회(0=전체)"
            TextInput:
                id: recent_in
                text: "0"
                multiline: False
                input_filter: "int"
        BoxLayout:
            orientation: "vertical"
            Label: text: "동일조합 제외"
            CheckBox:
                id: exclude_cb
                active: True

    # Play button + Export
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(10)
        Button:
            text: "Play (5세트 생성)"
            on_release: app.on_play()
        Button:
            text: "CSV 내보내기"
            on_release: app.on_export()

    # Results
    GridLayout:
        id: results_grid
        cols: 5
        rows: 1
        size_hint_y: None
        height: dp(60)
        row_default_height: dp(60)
        spacing: dp(6)

    # Add new draw
    Label: text: "새 회차 추가"
    BoxLayout:
        size_hint_y: None
        height: dp(40)
        Label: text: "회차 레이블(빈칸=자동)"
        TextInput:
            id: round_in
            multiline: False

    NumRow:
        id: numrow

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        Button:
            text: "추가"
            on_release: app.on_add_new()

    # Paste/import
    Label: text: "과거 데이터 붙여넣기(옵션)"
    TextInput:
        id: paste_in
        hint_text: "예)\n1회: 1, 5, 12, 19, 28, 41\n2회  3 8 14 19 33 41"
        size_hint_y: 0.4
        multiline: True

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        Button:
            text: "붙여넣기 → 내장 데이터에 추가"
            on_release: app.on_import_paste()
"""

class LottoApp(App):
    rows = ListProperty([])          # list of {"round": str, "nums": [6 ints]}
    results = ListProperty([])       # list of 5 combos
    alpha = NumericProperty(1.0)
    beta = NumericProperty(1.0)
    recent_k = NumericProperty(0)
    exclude_exact = BooleanProperty(True)
    info = StringProperty("")

    def build(self):
        # Optional: tweak window size on desktop
        if platform != "android":
            Window.size = (900, 800)

        # Load storage
        store_path = get_store_path()
        self.store = JsonStore(store_path)
        self.rows = self.store.get("data")["rows"] if self.store.exists("data") else []

        root = Builder.load_string(KV)
        self.refresh_results_grid(root)
        return root

    def save_rows(self):
        self.store.put("data", rows=self.rows)

    def read_params(self):
        root = self.root
        try:
            self.alpha = float(root.ids.alpha_in.text or "1.0")
        except Exception:
            self.alpha = 1.0
            root.ids.alpha_in.text = "1.0"
        try:
            self.beta = float(root.ids.beta_in.text or "1.0")
        except Exception:
            self.beta = 1.0
            root.ids.beta_in.text = "1.0"
        try:
            self.recent_k = int(root.ids.recent_in.text or "0")
        except Exception:
            self.recent_k = 0
            root.ids.recent_in.text = "0"
        self.exclude_exact = bool(root.ids.exclude_cb.active)

    def refresh_results_grid(self, root):
        grid = root.ids.results_grid
        grid.clear_widgets()
        # create 5 columns of labels
        for i in range(5):
            from kivy.uix.label import Label
            txt = "—" if i >= len(self.results) else " ".join(map(str, self.results[i]))
            grid.add_widget(Label(text=txt))

    def on_play(self):
        self.read_params()
        counts = frequency_counts(self.rows, recent_k=self.recent_k)
        probs = weighted_probabilities(counts, alpha=self.alpha, beta=self.beta)
        numbers = list(range(1, 46))

        existing = combos_set(self.rows) if self.exclude_exact else set()
        self.results = []
        for _ in range(5):
            # try up to N attempts to avoid exact duplicates
            ok = None
            for __ in range(5000):
                combo = tuple(sample_without_replacement(numbers, probs, k=6))
                if not self.exclude_exact or combo not in existing:
                    ok = combo
                    break
            if ok is None:
                ok = combo
            self.results.append(list(ok))

        self.refresh_results_grid(self.root)
        self.toast("5세트 생성 완료")

    def on_add_new(self):
        root = self.root
        # parse numbers
        nums = []
        for i in range(1, 7):
            t = root.ids.numrow.ids[f"n{i}"].text.strip()
            if not t:
                self.toast("번호 6개를 모두 입력하세요.")
                return
            try:
                n = int(t)
            except Exception:
                self.toast("숫자만 입력하세요.")
                return
            nums.append(n)

        if not valid_six(nums):
            self.toast("서로 다른 6개(1~45) 번호여야 합니다.")
            return

        rlabel = root.ids.round_in.text.strip()
        if not rlabel:
            rlabel = next_round_label(self.rows)

        self.rows.append({"round": rlabel, "nums": sorted(nums)})
        self.save_rows()
        self.toast(f"{rlabel} 추가됨 (총 {len(self.rows)}건)")

    def on_import_paste(self):
        text = self.root.ids.paste_in.text or ""
        rows = parse_paste(text)
        if not rows:
            self.toast("추출 가능한 줄이 없습니다.")
            return
        start_idx = len(self.rows)
        added = 0
        for idx, r in enumerate(rows, start=1):
            nums = r["nums"]
            rlabel = r["round"] if r["round"] else f"{start_idx + idx}회"
            if valid_six(nums):
                self.rows.append({"round": rlabel, "nums": sorted(nums)})
                added += 1
        self.save_rows()
        self.toast(f"{added}건 추가 (총 {len(self.rows)}건)")

    def on_export(self):
        # Export CSV to Downloads
        path_dir = get_downloads_path()
        fname = "lotto_data.csv"
        full = os.path.join(path_dir, fname)
        try:
            with open(full, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["회차","n1","n2","n3","n4","n5","n6"])
                for r in self.rows:
                    row = [r["round"]] + r["nums"]
                    w.writerow(row)
            self.toast(f"CSV 저장됨: {full}")
        except Exception as e:
            self.toast(f"저장 실패: {e}")

    def toast(self, msg):
        # Simple toast replacement
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        p = Popup(title="알림", content=Label(text=msg), size_hint=(0.7, 0.25))
        p.open()

if __name__ == "__main__":
    LottoApp().run()
