import json
import os
from datetime import datetime

from kivy.config import Config

# Размеры окна под стандартный смартфон
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')

from kivy.metrics import dp
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

DATA_DIR = "notes_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


# --- ЭКРАН 1: Список заметок и файлов ---
class MainNotesScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "main_screen"

        root_layout = MDRelativeLayout()
        main_box = MDBoxLayout(orientation="vertical", padding="12dp", spacing="8dp")

        # Заголовок
        header = MDBoxLayout(size_hint_y=None, height="40dp")
        header.add_widget(MDLabel(
            text="Расходы",
            font_style="Headline",
            role="small",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        ))
        main_box.add_widget(header)

        # Списочная часть
        scroll = MDScrollView()
        self.grid = MDGridLayout(cols=1, spacing="8dp", size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        scroll.add_widget(self.grid)
        main_box.add_widget(scroll)

        root_layout.add_widget(main_box)

        # Кнопка FAB
        fab = MDFabButton(
            icon="plus",
            pos_hint={"right": 0.92, "bottom": 0.08},
            on_release=lambda x: self.app.open_note_editor(None)
        )
        root_layout.add_widget(fab)

        self.add_widget(root_layout)

    @property
    def app(self):
        return MDApp.get_running_app()

    def refresh_list(self):
        self.grid.clear_widgets()
        files = [f for f in os.listdir(DATA_DIR) if f.endswith(".json")]

        for file_name in sorted(files, reverse=True):
            filepath = os.path.join(DATA_DIR, file_name)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            card = MDCard(
                orientation="vertical",
                padding="8dp",
                spacing="2dp",
                size_hint_y=None,
                height="115dp",
                style="outlined",
                md_bg_color=(1, 1, 1, 1),
                line_color=(1, 1, 1, 1),
                on_release=lambda x, fn=file_name: self.app.open_note_editor(fn)
            )

            # Шапка карточки
            card_head = MDBoxLayout(size_hint_y=None, height="28dp", spacing="4dp")
            
            title_lbl = MDLabel(
                text=data.get("title", "Без названия"),
                font_style="Title",
                role="small",
                bold=True,
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                shorten=True,
                shorten_from="right"
            )
            
            del_file_btn = MDIconButton(
                icon="delete",
                size_hint=(None, None),
                size=("28dp", "28dp"),
                icon_color=(0.7, 0.3, 0.3, 1),
                on_release=lambda x, fn=file_name: self.delete_note(fn)
            )

            card_head.add_widget(title_lbl)
            card_head.add_widget(del_file_btn)
            card.add_widget(card_head)

            # Превью итогов
            rows = data.get("rows", [])
            total = sum(float(r.get("amount", 0) or 0) for r in rows)

            preview_text = f"Записей: {len(rows)}\nИтого: {total:,.2f} TMT".replace(",", " ")
            card.add_widget(MDLabel(
                text=preview_text,
                font_style="Body",
                role="small",
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1)
            ))

            self.grid.add_widget(card)

    def delete_note(self, filename):
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            self.refresh_list()


# --- ЭКРАН 2: Редактор таблицы расходов ---
class NoteEditorScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "editor_screen"
        self.current_filename = None
        self.row_inputs = []

        self.main_layout = MDBoxLayout(orientation="vertical", padding="12dp", spacing="6dp")

        # 1. Навигация сверху
        top_bar = MDBoxLayout(size_hint_y=None, height="48dp", spacing="6dp")
        
        back_btn = MDIconButton(
            icon="arrow-left",
            size_hint=(None, None),
            size=("40dp", "40dp"),
            on_release=self.save_and_close
        )
        top_bar.add_widget(back_btn)

        self.title_input = MDTextField(
            MDTextFieldHintText(text="Название заметки"),
            size_hint_y=None,
            height="48dp",
            font_size="13sp"
        )
        top_bar.add_widget(self.title_input)
        self.main_layout.add_widget(top_bar)

        # 2. Таблица расходов
        scroll = MDScrollView()
        self.table_box = MDBoxLayout(
            orientation="vertical", 
            spacing="8dp", 
            size_hint_y=None,
            padding=[0, 16, 0, 0]
        )
        self.table_box.bind(minimum_height=self.table_box.setter("height"))
        scroll.add_widget(self.table_box)
        self.main_layout.add_widget(scroll)

        # 3. Итог и Кнопка добавления строки
        bottom_bar = MDBoxLayout(size_hint_y=None, height="40dp", spacing="8dp")
        add_row_btn = MDButton(MDButtonText(text="+ Строка"), on_release=lambda x: self.add_row())
        self.total_label = MDLabel(
            text="Итого: 0 TMT",
            font_style="Title",
            role="small",
            halign="right",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        bottom_bar.add_widget(add_row_btn)
        bottom_bar.add_widget(self.total_label)
        self.main_layout.add_widget(bottom_bar)

        # 4. Заметка / Комментарий
        self.note_input = MDTextField(
            MDTextFieldHintText(text="Заметка / Комментарии..."),
            size_hint_y=None,
            height="64dp",
            font_size="13sp"
        )
        self.main_layout.add_widget(self.note_input)

        self.add_widget(self.main_layout)

    def load_note(self, filename=None):
        self.table_box.clear_widgets()
        self.row_inputs = []
        self.current_filename = filename

        if filename:
            filepath = os.path.join(DATA_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.title_input.text = data.get("title", "")
            self.note_input.text = data.get("note", "")
            
            # Загружаем строки с сохранённой сортировкой
            for r in data.get("rows", []):
                self.add_row(r.get("date", ""), r.get("category", ""), str(r.get("amount", "")))
        else:
            today_str = datetime.now().strftime("%d.%m.%Y")
            self.title_input.text = f"Расходы - {today_str}"
            self.note_input.text = ""

        self.recalc_total()

    def add_row(self, date="", category="", amount=""):
        row = MDBoxLayout(size_hint_y=None, height="56dp", spacing="4dp")

        # Если дата не указана, берем дату из предыдущей строки или текущую дату
        if not date:
            if self.row_inputs and self.row_inputs[-1][0].text.strip():
                date = self.row_inputs[-1][0].text.strip()
            else:
                date = datetime.now().strftime("%d.%m")

        t_date = MDTextField(MDTextFieldHintText(text="Дата"), text=date, size_hint_x=0.22, font_size="12sp")
        t_cat = MDTextField(MDTextFieldHintText(text="Описание"), text=category, size_hint_x=0.46, font_size="12sp")
        t_amt = MDTextField(MDTextFieldHintText(text="Сумма"), text=amount, size_hint_x=0.22, font_size="12sp")

        t_amt.bind(text=lambda instance, value: self.recalc_total())

        row_tuple = (t_date, t_cat, t_amt, row)

        del_btn = MDIconButton(
            icon="close",
            size_hint=(None, None),
            size=("36dp", "36dp"),
            pos_hint={"center_y": 0.5},
            on_release=lambda x: self.remove_row(row_tuple)
        )

        row.add_widget(t_date)
        row.add_widget(t_cat)
        row.add_widget(t_amt)
        row.add_widget(del_btn)

        self.table_box.add_widget(row)
        self.row_inputs.append(row_tuple)

    def remove_row(self, row_tuple):
        if row_tuple in self.row_inputs:
            self.table_box.remove_widget(row_tuple[3])
            self.row_inputs.remove(row_tuple)
            self.recalc_total()

    def recalc_total(self):
        total = 0.0
        for t_date, t_cat, amt_field, _ in self.row_inputs:
            val = amt_field.text.strip().replace(",", ".")
            if val:
                try:
                    total += float(val)
                except ValueError:
                    pass
        self.total_label.text = f"Итого: {total:,.2f} TMT".replace(",", " ")

    def _parse_day(self, date_str):
        """Вспомогательная функция для парсинга дня (числа) из строки даты"""
        try:
            # Извлекаем первое число до точки (например, из "05.08" берем 5)
            clean_str = date_str.strip().split(".")[0]
            return int(clean_str)
        except (ValueError, IndexError):
            return 999  # Некорректные даты помещаются в самый конец списка

    def save_and_close(self, *args):
        title = self.title_input.text.strip() or "Без названия"
        rows_data = []

        for t_date, t_cat, t_amt, _ in self.row_inputs:
            date_val = t_date.text.strip()
            cat_val = t_cat.text.strip()
            amt_val = t_amt.text.strip()

            if cat_val or amt_val:
                rows_data.append({
                    "date": date_val,
                    "category": cat_val,
                    "amount": amt_val
                })

        # Автоматическая сортировка по дню месяца (от 1 до 31)
        rows_data.sort(key=lambda item: self._parse_day(item["date"]))

        save_data = {
            "title": title,
            "note": self.note_input.text,
            "rows": rows_data
        }

        if not self.current_filename:
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()
            self.current_filename = f"{safe_title}_{int(datetime.now().timestamp())}.json"

        filepath = os.path.join(DATA_DIR, self.current_filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        app = MDApp.get_running_app()
        app.main_screen.refresh_list()
        app.sm.current = "main_screen"


# --- ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ ---
class ExpenseNotesApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Gray"

        self.sm = MDScreenManager()

        self.main_screen = MainNotesScreen()
        self.editor_screen = NoteEditorScreen()

        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.editor_screen)

        self.main_screen.refresh_list()
        return self.sm

    def open_note_editor(self, filename=None):
        self.editor_screen.load_note(filename)
        self.sm.current = "editor_screen"


if __name__ == "__main__":
    ExpenseNotesApp().run()