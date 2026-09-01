import json
import os
import re
from datetime import datetime

from kivy.config import Config
from kivy.metrics import dp
from kivy.uix.popup import Popup

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDButton, MDButtonText, MDFabButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

Config.set("graphics", "width", "360")
Config.set("graphics", "height", "640")

DATA_DIR = "notes_data"
os.makedirs(DATA_DIR, exist_ok=True)

BG = (0.055, 0.055, 0.065, 1)
CARD = (0.10, 0.10, 0.12, 1)
CARD_2 = (0.14, 0.14, 0.16, 1)
TEXT = (0.95, 0.95, 0.97, 1)
MUTED = (0.60, 0.60, 0.64, 1)


def safe_float(value):
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return 0.0


def money(value):
    return f"{value:,.2f} TMT".replace(",", " ")


def parse_day(date_string):
    try:
        return int(str(date_string).strip().split(".")[0])
    except (ValueError, IndexError):
        return 999


class ConfirmPopup(Popup):
    def __init__(self, message, on_confirm, **kwargs):
        super().__init__(
            title="Удалить заметку?",
            size_hint=(0.86, None),
            height=dp(190),
            separator_height=0,
            auto_dismiss=True,
            **kwargs,
        )
        box = MDBoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        box.add_widget(MDLabel(
            text=message,
            theme_text_color="Custom",
            text_color=TEXT,
            halign="center",
        ))
        buttons = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        buttons.add_widget(MDButton(
            MDButtonText(text="Отмена"),
            on_release=lambda *_: self.dismiss(),
        ))
        buttons.add_widget(MDButton(
            MDButtonText(text="Удалить"),
            on_release=lambda *_: self.confirm(on_confirm),
        ))
        box.add_widget(buttons)
        self.content = box

    def confirm(self, callback):
        self.dismiss()
        callback()


class MainNotesScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "main_screen"
        self.search_text = ""

        root = MDRelativeLayout()
        main = MDBoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(10),
        )

        header = MDBoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        header.add_widget(MDLabel(
            text="Расходы",
            font_style="Headline",
            role="small",
            theme_text_color="Custom",
            text_color=TEXT,
        ))
        header.add_widget(MDIconButton(
            icon="chart-box-outline",
            on_release=lambda *_: self.app.open_stats(),
        ))
        main.add_widget(header)

        self.search_input = MDTextField(
            MDTextFieldHintText(text="Поиск по заметкам и расходам"),
            size_hint_y=None,
            height=dp(48),
        )
        self.search_input.bind(text=self.on_search)
        main.add_widget(self.search_input)

        summary = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(92),
            padding=dp(14),
            spacing=dp(2),
            radius=[dp(18)] * 4,
            md_bg_color=CARD_2,
        )
        summary.add_widget(MDLabel(
            text="Всего расходов",
            theme_text_color="Custom",
            text_color=MUTED,
            font_style="Body",
            role="small",
        ))
        self.total_label = MDLabel(
            text="0.00 TMT",
            theme_text_color="Custom",
            text_color=TEXT,
            font_style="Headline",
            role="small",
            bold=True,
        )
        summary.add_widget(self.total_label)
        main.add_widget(summary)

        scroll = MDScrollView()
        self.grid = MDGridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        scroll.add_widget(self.grid)
        main.add_widget(scroll)
        root.add_widget(main)

        root.add_widget(MDFabButton(
            icon="plus",
            pos_hint={"right": 0.93, "bottom": 0.07},
            on_release=lambda *_: self.app.open_note_editor(None),
        ))
        self.add_widget(root)

    @property
    def app(self):
        return MDApp.get_running_app()

    def on_pre_enter(self, *args):
        self.refresh_list()

    def on_search(self, instance, value):
        self.search_text = value.strip().lower()
        self.refresh_list()

    def get_files(self):
        try:
            return [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".json")]
        except OSError:
            return []

    def read_note(self, filename):
        try:
            with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def note_matches(self, data):
        if not self.search_text:
            return True
        values = [str(data.get("title", "")), str(data.get("note", ""))]
        for row in data.get("rows", []):
            values.extend([
                str(row.get("category", "")),
                str(row.get("date", "")),
                str(row.get("amount", "")),
            ])
        return any(self.search_text in value.lower() for value in values)

    def refresh_list(self):
        self.grid.clear_widgets()
        grand_total = 0.0
        visible_count = 0

        for filename in sorted(self.get_files(), reverse=True):
            data = self.read_note(filename)
            if not data:
                continue

            rows = data.get("rows", [])
            note_total = sum(safe_float(r.get("amount", 0)) for r in rows)
            grand_total += note_total

            if not self.note_matches(data):
                continue
            visible_count += 1

            card = MDCard(
                orientation="vertical",
                padding=dp(12),
                spacing=dp(4),
                size_hint_y=None,
                height=dp(124),
                radius=[dp(18)] * 4,
                md_bg_color=CARD,
                on_release=lambda _, fn=filename: self.app.open_note_editor(fn),
            )

            head = MDBoxLayout(size_hint_y=None, height=dp(34), spacing=dp(4))
            head.add_widget(MDLabel(
                text=data.get("title", "Без названия"),
                theme_text_color="Custom",
                text_color=TEXT,
                font_style="Title",
                role="small",
                bold=True,
                shorten=True,
                shorten_from="right",
            ))
            head.add_widget(MDIconButton(
                icon="delete-outline",
                size_hint=(None, None),
                size=(dp(38), dp(38)),
                on_release=lambda _, fn=filename: self.ask_delete(fn),
            ))
            card.add_widget(head)
            card.add_widget(MDLabel(
                text=f"Записей: {len(rows)}",
                theme_text_color="Custom",
                text_color=MUTED,
                role="small",
            ))
            card.add_widget(MDLabel(
                text=money(note_total),
                theme_text_color="Custom",
                text_color=TEXT,
                font_style="Title",
                role="small",
                bold=True,
            ))
            self.grid.add_widget(card)

        self.total_label.text = money(grand_total)
        if visible_count == 0:
            self.grid.add_widget(MDLabel(
                text=("Ничего не найдено" if self.search_text
                      else "Пока нет записей\nНажми +, чтобы добавить расход"),
                halign="center",
                theme_text_color="Custom",
                text_color=MUTED,
                size_hint_y=None,
                height=dp(100),
            ))

    def ask_delete(self, filename):
        ConfirmPopup(
            "Запись будет удалена без возможности восстановления.",
            lambda: self.delete_note(filename),
        ).open()

    def delete_note(self, filename):
        try:
            path = os.path.join(DATA_DIR, filename)
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
        self.refresh_list()


class NoteEditorScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "editor_screen"
        self.current_filename = None
        self.row_inputs = []

        self.main_layout = MDBoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(8),
        )

        top = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(6))
        top.add_widget(MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=(dp(42), dp(42)),
            on_release=self.save_and_close,
        ))
        self.title_input = MDTextField(
            MDTextFieldHintText(text="Название заметки"),
            size_hint_y=None,
            height=dp(48),
        )
        top.add_widget(self.title_input)
        self.main_layout.add_widget(top)

        self.main_layout.add_widget(MDLabel(
            text="Дата • Категория / описание • Сумма",
            theme_text_color="Custom",
            text_color=MUTED,
            role="small",
            size_hint_y=None,
            height=dp(28),
        ))

        scroll = MDScrollView()
        self.table_box = MDBoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=[0, dp(8), 0, dp(8)],
        )
        self.table_box.bind(minimum_height=self.table_box.setter("height"))
        scroll.add_widget(self.table_box)
        self.main_layout.add_widget(scroll)

        bottom = MDBoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        bottom.add_widget(MDButton(
            MDButtonText(text="+ Расход"),
            on_release=lambda *_: self.add_row(),
        ))
        self.total_label = MDLabel(
            text="Итого: 0.00 TMT",
            theme_text_color="Custom",
            text_color=TEXT,
            font_style="Title",
            role="small",
            halign="right",
            bold=True,
        )
        bottom.add_widget(self.total_label)
        self.main_layout.add_widget(bottom)

        self.note_input = MDTextField(
            MDTextFieldHintText(text="Заметка / комментарии"),
            size_hint_y=None,
            height=dp(62),
        )
        self.main_layout.add_widget(self.note_input)
        self.add_widget(self.main_layout)

    @property
    def app(self):
        return MDApp.get_running_app()

    def load_note(self, filename=None):
        self.table_box.clear_widgets()
        self.row_inputs = []
        self.current_filename = filename

        if filename:
            try:
                with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                data = {}
            self.title_input.text = data.get("title", "")
            self.note_input.text = data.get("note", "")
            for row in data.get("rows", []):
                self.add_row(
                    row.get("date", ""),
                    row.get("category", ""),
                    str(row.get("amount", "")),
                )
        else:
            self.title_input.text = f"Расходы - {datetime.now():%d.%m.%Y}"
            self.note_input.text = ""
            self.add_row()
        self.recalc_total()

    def add_row(self, date="", category="", amount=""):
        row = MDBoxLayout(size_hint_y=None, height=dp(58), spacing=dp(4))
        if not date:
            if self.row_inputs and self.row_inputs[-1][0].text.strip():
                date = self.row_inputs[-1][0].text.strip()
            else:
                date = datetime.now().strftime("%d.%m")

        t_date = MDTextField(
            MDTextFieldHintText(text="Дата"), text=date, size_hint_x=0.22,
        )
        t_cat = MDTextField(
            MDTextFieldHintText(text="Категория / описание"),
            text=category, size_hint_x=0.50,
        )
        t_amt = MDTextField(
            MDTextFieldHintText(text="Сумма"), text=amount, size_hint_x=0.20,
        )
        t_amt.bind(text=lambda *_: self.recalc_total())

        row_tuple = (t_date, t_cat, t_amt, row)
        row.add_widget(t_date)
        row.add_widget(t_cat)
        row.add_widget(t_amt)
        row.add_widget(MDIconButton(
            icon="close",
            size_hint=(None, None),
            size=(dp(34), dp(34)),
            pos_hint={"center_y": 0.5},
            on_release=lambda *_: self.remove_row(row_tuple),
        ))
        self.table_box.add_widget(row)
        self.row_inputs.append(row_tuple)

    def remove_row(self, row_tuple):
        if row_tuple in self.row_inputs:
            self.table_box.remove_widget(row_tuple[3])
            self.row_inputs.remove(row_tuple)
            self.recalc_total()

    def recalc_total(self):
        total = sum(safe_float(amt.text) for _, _, amt, _ in self.row_inputs)
        self.total_label.text = f"Итого: {money(total)}"

    def save_and_close(self, *args):
        title = self.title_input.text.strip() or "Без названия"
        rows = []
        for t_date, t_cat, t_amt, _ in self.row_inputs:
            date_val = t_date.text.strip()
            cat_val = t_cat.text.strip()
            amt_val = t_amt.text.strip()
            if cat_val or amt_val:
                rows.append({
                    "date": date_val,
                    "category": cat_val,
                    "amount": amt_val,
                })

        rows.sort(key=lambda item: parse_day(item["date"]))
        data = {
            "title": title,
            "note": self.note_input.text.strip(),
            "rows": rows,
        }

        if not self.current_filename:
            safe_title = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE)
            safe_title = re.sub(r"\s+", "_", safe_title).strip("_") or "note"
            self.current_filename = f"{safe_title}_{int(datetime.now().timestamp())}.json"

        try:
            with open(os.path.join(DATA_DIR, self.current_filename), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            return

        self.app.main_screen.refresh_list()
        self.app.sm.current = "main_screen"


class StatsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "stats_screen"
        root = MDBoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))

        top = MDBoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        top.add_widget(MDIconButton(
            icon="arrow-left", on_release=lambda *_: self.app.go_main()
        ))
        top.add_widget(MDLabel(
            text="Статистика",
            font_style="Headline",
            role="small",
            theme_text_color="Custom",
            text_color=TEXT,
        ))
        root.add_widget(top)

        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(112),
            padding=dp(16),
            spacing=dp(4),
            radius=[dp(18)] * 4,
            md_bg_color=CARD_2,
        )
        card.add_widget(MDLabel(
            text="Общая сумма",
            theme_text_color="Custom",
            text_color=MUTED,
        ))
        self.stats_total = MDLabel(
            text="0.00 TMT",
            theme_text_color="Custom",
            text_color=TEXT,
            font_style="Headline",
            role="small",
            bold=True,
        )
        card.add_widget(self.stats_total)
        root.add_widget(card)

        scroll = MDScrollView()
        self.stats_box = MDBoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        self.stats_box.bind(minimum_height=self.stats_box.setter("height"))
        scroll.add_widget(self.stats_box)
        root.add_widget(scroll)
        self.add_widget(root)

    @property
    def app(self):
        return MDApp.get_running_app()

    def on_pre_enter(self, *args):
        self.refresh_stats()

    def refresh_stats(self):
        self.stats_box.clear_widgets()
        total = 0.0
        note_count = 0
        row_count = 0
        biggest = 0.0
        categories = {}

        for filename in self.app.main_screen.get_files():
            data = self.app.main_screen.read_note(filename)
            if not data:
                continue
            note_count += 1
            for row in data.get("rows", []):
                amount = safe_float(row.get("amount", 0))
                total += amount
                row_count += 1
                biggest = max(biggest, amount)
                category = str(row.get("category", "") or "Без категории").strip()
                categories[category] = categories.get(category, 0.0) + amount

        self.stats_total.text = money(total)
        self.add_stat("Заметок", str(note_count))
        self.add_stat("Расходов", str(row_count))
        self.add_stat("Самый большой расход", money(biggest))

        if categories:
            self.stats_box.add_widget(MDLabel(
                text="По категориям",
                theme_text_color="Custom",
                text_color=TEXT,
                font_style="Title",
                role="small",
                bold=True,
                size_hint_y=None,
                height=dp(38),
            ))
            for category, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                self.add_stat(category, money(amount))

    def add_stat(self, title, value):
        card = MDCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(68),
            padding=dp(12),
            radius=[dp(16)] * 4,
            md_bg_color=CARD,
        )
        card.add_widget(MDLabel(
            text=title, theme_text_color="Custom", text_color=MUTED,
        ))
        card.add_widget(MDLabel(
            text=value, theme_text_color="Custom", text_color=TEXT,
            halign="right", bold=True,
        ))
        self.stats_box.add_widget(card)


class ExpenseNotesApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"

        self.sm = MDScreenManager()
        self.main_screen = MainNotesScreen()
        self.editor_screen = NoteEditorScreen()
        self.stats_screen = StatsScreen()

        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.editor_screen)
        self.sm.add_widget(self.stats_screen)
        self.main_screen.refresh_list()
        return self.sm

    def open_note_editor(self, filename=None):
        self.editor_screen.load_note(filename)
        self.sm.current = "editor_screen"

    def open_stats(self):
        self.sm.current = "stats_screen"

    def go_main(self):
        self.main_screen.refresh_list()
        self.sm.current = "main_screen"


if __name__ == "__main__":
    ExpenseNotesApp().run()
