import json
import os
import sys
import glob
import re
import html

# Qt on Windows defaults to the DirectWrite text-rendering backend, which
# has a known issue rendering certain CFF-flavored .otf fonts (like the
# extracted Beaufort/Spiegel files here) when they're loaded at runtime
# via QFontDatabase.addApplicationFont() rather than being installed
# system fonts: compound curves in glyphs like "A" and "G" come out
# self-intersecting/corrupted, while simple straight-stroke glyphs look
# fine. Forcing the FreeType backend instead avoids the bug entirely.
# This must be set before QApplication is constructed, and only applies
# on Windows (the platform string is meaningless elsewhere).
if sys.platform == "win32":
    os.environ.setdefault(
        "QT_QPA_PLATFORM",
        "windows:fontengine=freetype"
    )

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QImage,
    QPainter,
    QPixmap,
    QTextCharFormat,
    QTextDocument,
    QFontMetrics,
    QLinearGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QColorDialog,
    QFrame,
    QFileDialog,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AUGMENTS_FILE = os.path.join(
    BASE_DIR,
    "augments.json"
)

SETTINGS_FILE = os.path.join(
    BASE_DIR,
    "settings.json"
)

ASSETS_DIR = os.path.join(
    BASE_DIR,
    "assets"
)

ICONS_DIR = os.path.join(
    ASSETS_DIR,
    "icons"
)

BACKGROUNDS_DIR = os.path.join(
    ASSETS_DIR,
    "backgrounds"
)

FONTS_DIR = os.path.join(
    ASSETS_DIR,
    "fonts"
)


# ============================================================
# CARD SIZE
# ============================================================

CARD_WIDTH = 380
CARD_HEIGHT = 580

# ============================================================
# DEBUG
# ============================================================

DEBUG_BOUNDS = False

# ============================================================
# CARD VISUAL TUNING
# ============================================================


# ============================================================
# ICON
# ============================================================

ICON_SIZE = 165

ICON_X = 107
ICON_Y = 48


# ============================================================
# TITLE
# ============================================================

TITLE_X = 30
TITLE_Y = 260

TITLE_WIDTH = 320
TITLE_HEIGHT = 40

TITLE_FONT_SIZE = 18

TITLE_ALIGNMENT = Qt.AlignCenter


# ============================================================
# TAG BOXES
# ============================================================

TAG_AREA_X = 30
TAG_AREA_Y = 303

TAG_AREA_WIDTH = 320
TAG_AREA_HEIGHT = 23

TAG_GAP = 6

TAG_PADDING_X = 4
TAG_PADDING_Y = 1

TAG_MAX_WIDTH = 180
TAG_MIN_WIDTH = 0

TAG_BOX_RADIUS = 2

TAG_FONT_SIZE = 12

TAG_TEXT_ALIGNMENT = Qt.AlignCenter

TAG_BOX_COLOR_EDGE = "#89877a"
TAG_BOX_COLOR_CENTER = "#9b9d94"
TAG_TEXT_COLOR = "#1A1A1A"

TAG_BORDER_WIDTH = 0
TAG_BORDER_COLOR = "#000000"

TAG_SHADOW_OFFSET_X = 1
TAG_SHADOW_OFFSET_Y = 1
TAG_SHADOW_COLOR = "#80000000"


# ============================================================
# DESCRIPTION
# ============================================================

DESCRIPTION_X = 42
DESCRIPTION_Y = 350

DESCRIPTION_WIDTH = 300
DESCRIPTION_HEIGHT = 200

DESCRIPTION_FONT_SIZE = 15

DESCRIPTION_LETTER_SPACING = .75

DESCRIPTION_ALIGNMENT = Qt.AlignCenter


# ============================================================
# COLORS
# ============================================================

BG = "#101216"
PANEL = "#181b21"
PANEL_2 = "#20242c"
BORDER = "#303640"

TEXT = "#eeeeee"
SUBTEXT = "#9da3ad"
ACCENT = "#c8a96b"

CARD_TEXT = "#eae7da"

LEAGUE_HIGHLIGHT = "#C8AA6E"


# ============================================================
# FONT FILES
# ============================================================

FONT_FILES = {
    "Beaufort Bold": os.path.join(
        FONTS_DIR,
        "beaufortforlol-bold.otf"
    ),

    "Beaufort Regular": os.path.join(
        FONTS_DIR,
        "beaufortforlol-regular.otf"
    ),

    "Spiegel Bold": os.path.join(
        FONTS_DIR,
        "spiegel-bold.otf"
    ),

    "Spiegel Regular": os.path.join(
        FONTS_DIR,
        "spiegel-regular.otf"
    ),
}


# ============================================================
# FONT LOADING
# ============================================================

def load_fonts():

    loaded = {}

    for name, path in FONT_FILES.items():

        if not os.path.exists(path):

            print(
                f"Font not found: {path}"
            )

            continue

        font_id = QFontDatabase.addApplicationFont(
            path
        )

        if font_id == -1:

            print(
                f"Could not load font: {path}"
            )

            continue

        families = (
            QFontDatabase
            .applicationFontFamilies(
                font_id
            )
        )

        if families:

            loaded[name] = families[0]

    print(
        "Loaded fonts:",
        loaded
    )

    return loaded


# ============================================================
# LEAGUE MARKUP -> QT HTML
# ============================================================

def convert_league_markup(text):

    if not text:
        return ""

    replacements = {}

    def protect_tag(match):

        key = f"___LEAGUE_TAG_{len(replacements)}___"

        replacements[key] = (
            match.group(1),
            match.group(2)
        )

        return key

    protected = re.sub(
        r"<(scale[A-Za-z0-9_]+|attention|status|keyword[A-Za-z0-9_]*|magicDamage|physicalDamage|trueDamage)>(.*?)</\1>",
        protect_tag,
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    protected = html.escape(
        protected
    )

    for key, (
        tag,
        content
    ) in replacements.items():

        content = html.escape(
            content
        )

        replacement = (
            f'<font color="{LEAGUE_HIGHLIGHT}">'
            f'{content}'
            f'</font>'
        )

        protected = protected.replace(
            key,
            replacement
        )

    protected = re.sub(
        r"&lt;/?[A-Za-z][^&]*?&gt;",
        "",
        protected
    )

    protected = protected.replace(
        "\n",
        "<br>"
    )

    return protected


# ============================================================
# MAIN WINDOW
# ============================================================

class AugmentCreator(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "ARAM Mayhem Augment Creator"
        )

        self.resize(
            1400,
            850
        )

        self.fonts = load_fonts()

        self.augments = []

        self.current_augment = None

        self.tags = []

        self.load_settings()

        self.load_augments()

        self.build_ui()

        self.populate_augment_list()


    # ========================================================
    # DATA
    # ========================================================

    def load_augments(self):

        if not os.path.exists(
            AUGMENTS_FILE
        ):

            print(
                f"ERROR: Could not find {AUGMENTS_FILE}"
            )

            return

        with open(
            AUGMENTS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        self.augments = data.get(
            "augments",
            []
        )

        print(
            f"Loaded {len(self.augments)} augments"
        )


    # ========================================================
    # SETTINGS (SAVE CUSTOM COLORS)
    # ========================================================

    def load_settings(self):

        if not os.path.exists(
            SETTINGS_FILE
        ):
            return

        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        colors = data.get(
            "custom_colors",
            []
        )

        for index, color_hex in enumerate(colors):

            if index < QColorDialog.customCount():

                QColorDialog.setCustomColor(
                    index,
                    QColor(color_hex)
                )

    def save_settings(self):

        colors = []

        for i in range(
            QColorDialog.customCount()
        ):

            color = QColorDialog.customColor(i)

            colors.append(
                color.name()
            )

        data = {
            "custom_colors": colors
        }

        with open(
            SETTINGS_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QHBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        main_layout.setSpacing(
            12
        )


        # ====================================================
        # LEFT PANEL
        # ====================================================

        left_panel = QFrame()

        left_panel.setObjectName(
            "panel"
        )

        left_layout = QVBoxLayout(
            left_panel
        )

        title = QLabel(
            "AUGMENTS"
        )

        title.setObjectName(
            "panelTitle"
        )

        left_layout.addWidget(
            title
        )

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Search augment..."
        )

        self.search.textChanged.connect(
            self.filter_augments
        )

        left_layout.addWidget(
            self.search
        )

        self.augment_list = QListWidget()

        self.augment_list.itemClicked.connect(
            self.select_augment
        )

        left_layout.addWidget(
            self.augment_list
        )


        # ====================================================
        # CENTER PANEL
        # ====================================================

        center_panel = QFrame()

        center_panel.setObjectName(
            "panel"
        )

        center_layout = QVBoxLayout(
            center_panel
        )

        editor_title = QLabel(
            "EDITOR"
        )

        editor_title.setObjectName(
            "panelTitle"
        )

        center_layout.addWidget(
            editor_title
        )


        # ====================================================
        # NAME
        # ====================================================

        name_label = QLabel(
            "Name"
        )

        name_label.setObjectName(
            "label"
        )

        center_layout.addWidget(
            name_label
        )

        self.name_edit = QLineEdit()

        self.name_edit.textChanged.connect(
            self.update_preview
        )

        center_layout.addWidget(
            self.name_edit
        )


        # ====================================================
        # TAGS
        # ====================================================

        tags_label = QLabel(
            "Tags"
        )

        tags_label.setObjectName(
            "label"
        )

        center_layout.addWidget(
            tags_label
        )

        tag_row = QHBoxLayout()

        self.tag_input = QLineEdit()

        self.tag_input.setPlaceholderText(
            "Type a tag and press Enter"
        )

        self.tag_input.returnPressed.connect(
            self.add_tag
        )

        tag_row.addWidget(
            self.tag_input
        )

        add_tag_button = QPushButton(
            "Add"
        )

        add_tag_button.clicked.connect(
            self.add_tag
        )

        tag_row.addWidget(
            add_tag_button
        )

        center_layout.addLayout(
            tag_row
        )

        self.tags_container = QWidget()

        self.tags_layout = QHBoxLayout(
            self.tags_container
        )

        self.tags_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.tags_layout.setSpacing(
            6
        )

        self.tags_layout.setAlignment(
            Qt.AlignLeft
        )

        center_layout.addWidget(
            self.tags_container
        )


        # ====================================================
        # DESCRIPTION
        # ====================================================

        description_label = QLabel(
            "Description"
        )

        description_label.setObjectName(
            "label"
        )

        center_layout.addWidget(
            description_label
        )

        toolbar = QHBoxLayout()


        # ----------------------------------------------------
        # BOLD
        # ----------------------------------------------------

        self.bold_button = QPushButton(
            "B"
        )

        self.bold_button.setCheckable(
            True
        )

        self.bold_button.clicked.connect(
            self.toggle_bold
        )

        toolbar.addWidget(
            self.bold_button
        )


        # ----------------------------------------------------
        # ITALIC
        # ----------------------------------------------------

        self.italic_button = QPushButton(
            "I"
        )

        self.italic_button.setCheckable(
            True
        )

        self.italic_button.clicked.connect(
            self.toggle_italic
        )

        toolbar.addWidget(
            self.italic_button
        )


        # ----------------------------------------------------
        # COLOR
        # ----------------------------------------------------

        color_button = QPushButton(
            "Text Color"
        )

        color_button.clicked.connect(
            self.change_text_color
        )

        toolbar.addWidget(
            color_button
        )

        toolbar.addStretch()

        center_layout.addLayout(
            toolbar
        )


        # ----------------------------------------------------
        # TEXT EDITOR
        # ----------------------------------------------------

        self.description_edit = QTextEdit()

        description_font_family = self.fonts.get(
            "Beaufort Regular",
            "Arial"
        )

        description_font = QFont(
            description_font_family,
            DESCRIPTION_FONT_SIZE
        )

        description_font.setWeight(
            QFont.Normal
        )

        self.description_edit.setFont(
            description_font
        )

        self.description_edit.setPlaceholderText(
            "Write the augment description here..."
        )

        self.description_edit.textChanged.connect(
            self.update_preview
        )

        center_layout.addWidget(
            self.description_edit
        )


        # ====================================================
        # RIGHT PANEL
        # ====================================================

        right_panel = QFrame()

        right_panel.setObjectName(
            "panel"
        )

        right_layout = QVBoxLayout(
            right_panel
        )

        preview_title = QLabel(
            "PREVIEW"
        )

        preview_title.setObjectName(
            "panelTitle"
        )

        right_layout.addWidget(
            preview_title
        )

        self.preview = QLabel()

        self.preview.setAlignment(
            Qt.AlignCenter
        )

        self.preview.setMinimumSize(
            CARD_WIDTH,
            CARD_HEIGHT
        )

        right_layout.addWidget(
            self.preview,
            1
        )


        # ====================================================
        # EXPORT
        # ====================================================

        export_button = QPushButton(
            "EXPORT PNG"
        )

        export_button.setObjectName(
            "exportButton"
        )

        export_button.clicked.connect(
            self.export_card
        )

        right_layout.addWidget(
            export_button
        )


        # ====================================================
        # ADD PANELS
        # ====================================================

        main_layout.addWidget(
            left_panel,
            1
        )

        main_layout.addWidget(
            center_panel,
            2
        )

        main_layout.addWidget(
            right_panel,
            2
        )


        # ====================================================
        # STYLE
        # ====================================================

        self.setStyleSheet(
            f"""

            QMainWindow {{
                background: {BG};
            }}

            QWidget {{
                color: {TEXT};
                font-family: Arial;
                font-size: 14px;
            }}

            QFrame#panel {{
                background: {PANEL};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}

            QLabel#panelTitle {{
                font-size: 18px;
                font-weight: bold;
                color: {ACCENT};
                padding: 4px;
            }}

            QLabel#label {{
                color: {SUBTEXT};
                font-weight: bold;
                margin-top: 8px;
            }}

            QLineEdit,
            QTextEdit,
            QListWidget {{
                background: {PANEL_2};
                border: 1px solid {BORDER};
                border-radius: 5px;
                padding: 7px;
                color: {TEXT};
            }}

            QTextEdit {{
                font-family: "{description_font_family}";
                font-size: {DESCRIPTION_FONT_SIZE}px;
            }}

            QLineEdit:focus,
            QTextEdit:focus {{
                border: 1px solid {ACCENT};
            }}

            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {BORDER};
            }}

            QListWidget::item:selected {{
                background: {ACCENT};
                color: #111111;
            }}

            QPushButton {{
                background: {PANEL_2};
                border: 1px solid {BORDER};
                border-radius: 5px;
                padding: 7px 12px;
            }}

            QPushButton:hover {{
                border: 1px solid {ACCENT};
            }}

            QPushButton:checked {{
                background: {ACCENT};
                color: #111111;
            }}

            QPushButton#exportButton {{
                background: {ACCENT};
                color: #111111;
                font-weight: bold;
                padding: 12px;
            }}

            """
        )


    # ========================================================
    # AUGMENT LIST
    # ========================================================

    def populate_augment_list(self):

        self.augment_list.clear()

        for augment in self.augments:

            name = augment.get(
                "name",
                "Unknown Augment"
            )

            item = QListWidgetItem(
                name
            )

            item.setData(
                Qt.UserRole,
                augment
            )

            self.augment_list.addItem(
                item
            )


    def filter_augments(
        self,
        text
    ):

        text = text.lower().strip()

        for i in range(
            self.augment_list.count()
        ):

            item = self.augment_list.item(
                i
            )

            augment = item.data(
                Qt.UserRole
            )

            name = augment.get(
                "name",
                ""
            ).lower()

            item.setHidden(
                text not in name
            )


    # ========================================================
    # SELECT AUGMENT
    # ========================================================

    def select_augment(
        self,
        item
    ):

        augment = item.data(
            Qt.UserRole
        )

        self.current_augment = augment


        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        name = augment.get(
            "name",
            "Unknown"
        )

        self.name_edit.blockSignals(
            True
        )

        self.name_edit.setText(
            name
        )

        self.name_edit.blockSignals(
            False
        )


        # ----------------------------------------------------
        # TAGS
        # ----------------------------------------------------

        self.tags = list(
            augment.get(
                "tags",
                []
            )
        )

        self.update_tags_display()


        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        description = augment.get(
            "description",
            ""
        )

        description_html = (
            convert_league_markup(
                description
            )
        )

        self.description_edit.blockSignals(
            True
        )

        self.description_edit.setHtml(
            description_html
        )

        self.description_edit.blockSignals(
            False
        )


        # ----------------------------------------------------
        # Reset toolbar state
        # ----------------------------------------------------

        self.bold_button.blockSignals(
            True
        )

        self.bold_button.setChecked(
            False
        )

        self.bold_button.blockSignals(
            False
        )

        self.italic_button.blockSignals(
            True
        )

        self.italic_button.setChecked(
            False
        )

        self.italic_button.blockSignals(
            False
        )


        self.update_preview()


    # ========================================================
    # TAGS
    # ========================================================

    def add_tag(self):

        tag = self.tag_input.text().strip()

        if not tag:
            return

        if tag not in self.tags:

            self.tags.append(
                tag
            )

        self.tag_input.clear()

        self.update_tags_display()

        self.update_preview()


    def update_tags_display(self):

        while self.tags_layout.count():

            item = self.tags_layout.takeAt(0)

            widget = item.widget()

            if widget:

                widget.deleteLater()

        if not self.tags:

            no_tags = QLabel(
                "No tags"
            )

            no_tags.setStyleSheet(
                f"color: {SUBTEXT};"
            )

            self.tags_layout.addWidget(
                no_tags
            )

            return

        for index, tag in enumerate(
            self.tags
        ):

            tag_button = QPushButton(
                f"{tag}  ×"
            )

            tag_button.setProperty(
                "tag_index",
                index
            )

            tag_button.clicked.connect(
                lambda checked=False, i=index:
                self.remove_tag(i)
            )

            self.tags_layout.addWidget(
                tag_button
            )


    def remove_tag(self, index):

        if index < 0:
            return

        if index >= len(self.tags):
            return

        self.tags.pop(index)

        self.update_tags_display()

        self.update_preview()


    # ========================================================
    # RICH TEXT
    # ========================================================

    def toggle_bold(self):
        cursor = self.description_edit.textCursor()

        if not cursor.hasSelection():
            return

        format = QTextCharFormat()

        current_weight = cursor.charFormat().fontWeight()

        if current_weight == QFont.Bold:
            format.setFontWeight(QFont.Normal)
        else:
            format.setFontWeight(QFont.Bold)

        cursor.mergeCharFormat(format)

        self.description_edit.setTextCursor(cursor)

        self.update_preview()


    def toggle_italic(self):

        cursor = (
            self.description_edit
            .textCursor()
        )

        if not cursor.hasSelection():
            return

        fmt = QTextCharFormat()

        fmt.setFontItalic(
            self.italic_button.isChecked()
        )

        cursor.mergeCharFormat(
            fmt
        )

        self.description_edit.setTextCursor(
            cursor
        )

        self.update_preview()


    def change_text_color(self):

        cursor = (
            self.description_edit
            .textCursor()
        )

        if not cursor.hasSelection():
            return

        color = QColorDialog.getColor(
            QColor("#FFFFFF"),
            self,
            "Choose Text Color"
        )

        self.save_settings()

        if not color.isValid():
            return

        fmt = QTextCharFormat()

        fmt.setForeground(
            color
        )

        cursor.mergeCharFormat(
            fmt
        )

        self.description_edit.setTextCursor(
            cursor
        )

        self.update_preview()


    # ========================================================
    # FIND ICON
    # ========================================================

    def find_icon(self):

        if not self.current_augment:
            return None

        icon = self.current_augment.get(
            "icon",
            ""
        )

        if not icon:
            return None


        if os.path.exists(icon):
            return icon


        possible = os.path.join(
            ICONS_DIR,
            icon
        )

        if os.path.exists(
            possible
        ):

            return possible


        filename = os.path.basename(
            icon
        )

        matches = glob.glob(
            os.path.join(
                ICONS_DIR,
                "**",
                filename
            ),
            recursive=True
        )

        if matches:
            return matches[0]


        augment_id = str(
            self.current_augment.get(
                "id",
                ""
            )
        )

        if augment_id:

            matches = glob.glob(
                os.path.join(
                    ICONS_DIR,
                    f"*{augment_id}*"
                )
            )

            if matches:
                return matches[0]


        name = self.current_augment.get(
            "name",
            ""
        )

        clean_name = (
            name
            .replace(
                " ",
                "_"
            )
            .replace(
                "'",
                ""
            )
            .replace(
                "-",
                "_"
            )
        )

        matches = glob.glob(
            os.path.join(
                ICONS_DIR,
                f"*{clean_name}*"
            )
        )

        if matches:
            return matches[0]

        return None


    # ========================================================
    # FIND BACKGROUND
    # ========================================================

    def find_background(self):

        rarity = self.current_augment.get(
            "rarity",
            0
        )

        rarity_text = str(
            rarity
        ).lower()

        if (
            rarity_text == "2"
            or rarity_text == "prismatic"
        ):

            filename = (
                "bg_prismatic.png"
            )

        elif (
            rarity_text == "1"
            or rarity_text == "gold"
        ):

            filename = (
                "bg_gold.png"
            )

        else:

            filename = (
                "bg_silver.png"
            )

        path = os.path.join(
            BACKGROUNDS_DIR,
            filename
        )

        if os.path.exists(
            path
        ):

            return path

        return None


    # ========================================================
    # DRAW TAG BOXES
    # ========================================================

    def draw_tag_boxes(
        self,
        painter
    ):

        if not self.tags:
            return

        tags_font_family = (
            self.fonts.get(
                "Beaufort Bold",
                "Arial"
            )
        )

        tags_font = QFont(
            tags_font_family,
            TAG_FONT_SIZE
        )

        tags_font.setHintingPreference(
            QFont.HintingPreference.PreferNoHinting
        )

        # Spiegel-Bold.otf and Spiegel-Regular.otf also share one family
        # name ("Spiegel"), same situation as Beaufort - explicit weight
        # is required to actually get the bold face instead of Qt's
        # default-to-Regular behavior.
        tags_font.setWeight(
            QFont.Weight.Bold
        )

        metrics = QFontMetrics(
            tags_font
        )

        tag_widths = []

        for tag in self.tags:

            text_width = metrics.horizontalAdvance(
                str(tag)
            )

            width = (
                text_width
                + TAG_PADDING_X * 2
            )

            width = max(
                width,
                TAG_MIN_WIDTH
            )

            width = min(
                width,
                TAG_MAX_WIDTH
            )

            tag_widths.append(
                width
            )


        total_width = (
            sum(tag_widths)
            + TAG_GAP * max(
                0,
                len(tag_widths) - 1
            )
        )

        start_x = (
            TAG_AREA_X
            + (
                TAG_AREA_WIDTH
                - total_width
            ) / 2
        )

        box_height = TAG_AREA_HEIGHT

        start_y = (
            TAG_AREA_Y
            + (
                TAG_AREA_HEIGHT
                - box_height
            ) / 2
        )

        current_x = start_x

        for index, tag in enumerate(
            self.tags
        ):

            box_width = tag_widths[index]

            rect = QRectF(
                current_x,
                start_y,
                box_width,
                box_height
            )


            # ------------------------------------------------
            # Shadow
            # ------------------------------------------------

            if (
                TAG_SHADOW_OFFSET_X != 0
                or TAG_SHADOW_OFFSET_Y != 0
            ):

                shadow_rect = QRectF(
                    rect.left()
                    + TAG_SHADOW_OFFSET_X,

                    rect.top()
                    + TAG_SHADOW_OFFSET_Y,

                    rect.width(),
                    rect.height()
                )

                painter.setPen(
                    Qt.NoPen
                )

                painter.setBrush(
                    QColor(
                        TAG_SHADOW_COLOR
                    )
                )

                painter.drawRoundedRect(
                    shadow_rect,
                    TAG_BOX_RADIUS,
                    TAG_BOX_RADIUS
                )


            # ------------------------------------------------
            # Box
            # ------------------------------------------------

            gradient = QLinearGradient(
                rect.left(),
                rect.top(),
                rect.right(),
                rect.top()
            )
            
            gradient.setColorAt(0.0, QColor(TAG_BOX_COLOR_EDGE))
            gradient.setColorAt(0.5, QColor(TAG_BOX_COLOR_CENTER))
            gradient.setColorAt(1.0, QColor(TAG_BOX_COLOR_EDGE))

            if TAG_BORDER_WIDTH > 0:
                painter.setPen(QColor(TAG_BORDER_COLOR))
            else:
                painter.setPen(Qt.NoPen)

            painter.setBrush(gradient)

            painter.drawRoundedRect(
                rect,
                TAG_BOX_RADIUS,
                TAG_BOX_RADIUS
            )


            # ------------------------------------------------
            # Text
            # ------------------------------------------------

            painter.setFont(
                tags_font
            )

            painter.setPen(
                QColor(
                    TAG_TEXT_COLOR
                )
            )

            text_rect = rect.adjusted(
                TAG_PADDING_X,
                TAG_PADDING_Y,
                -TAG_PADDING_X,
                -TAG_PADDING_Y
            )

            painter.drawText(
                text_rect,
                TAG_TEXT_ALIGNMENT,
                str(tag)
            )

            current_x += (
                box_width
                + TAG_GAP
            )

    # ========================================================
    # DEBUG BOUNDS
    # ========================================================

    def draw_debug_bounds(self, painter):

        if not DEBUG_BOUNDS:
            return

        painter.save()

        pen = painter.pen()
        pen.setWidth(2)

        # ----------------------------------------------------
        # ICON
        # ----------------------------------------------------

        pen.setColor(
            QColor("#00FFFF")
        )

        painter.setPen(
            pen
        )

        painter.setBrush(
            Qt.NoBrush
        )

        painter.drawRect(
            ICON_X,
            ICON_Y,
            ICON_SIZE,
            ICON_SIZE
        )


        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        pen.setColor(
            QColor("#00FF00")
        )

        painter.setPen(
            pen
        )

        painter.drawRect(
            TITLE_X,
            TITLE_Y,
            TITLE_WIDTH,
            TITLE_HEIGHT
        )


        # ----------------------------------------------------
        # TAG AREA
        # ----------------------------------------------------

        pen.setColor(
            QColor("#FFFF00")
        )

        painter.setPen(
            pen
        )

        painter.drawRect(
            TAG_AREA_X,
            TAG_AREA_Y,
            TAG_AREA_WIDTH,
            TAG_AREA_HEIGHT
        )


        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        pen.setColor(
            QColor("#FF0000")
        )

        painter.setPen(
            pen
        )

        painter.drawRect(
            DESCRIPTION_X,
            DESCRIPTION_Y,
            DESCRIPTION_WIDTH,
            DESCRIPTION_HEIGHT
        )


        painter.restore()
    # ========================================================
    # DRAW CARD
    # ========================================================

    def render_card(self):

        if not self.current_augment:
            return None


        # ----------------------------------------------------
        # BASE IMAGE
        # ----------------------------------------------------

        background_path = (
            self.find_background()
        )

        if background_path:

            base = (
                QImage(
                    background_path
                )
                .convertToFormat(
                    QImage.Format_ARGB32
                )
            )

            base = base.scaled(
                CARD_WIDTH,
                CARD_HEIGHT,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )

        else:

            base = QImage(
                CARD_WIDTH,
                CARD_HEIGHT,
                QImage.Format_ARGB32
            )

            base.fill(
                QColor("#111111")
            )


        painter = QPainter(
            base
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.setRenderHint(
            QPainter.SmoothPixmapTransform
        )


        # ====================================================
        # ICON
        # ====================================================

        icon_path = self.find_icon()

        if icon_path:

            icon = QPixmap(
                icon_path
            )

            icon = icon.scaled(
                ICON_SIZE,
                ICON_SIZE,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            icon_x = (
                ICON_X
                + (
                    ICON_SIZE
                    - icon.width()
                ) / 2
            )

            icon_y = (
                ICON_Y
                + (
                    ICON_SIZE
                    - icon.height()
                ) / 2
            )

            painter.drawPixmap(
                int(icon_x),
                int(icon_y),
                icon
            )


        # ====================================================
        # NAME
        # ====================================================

        name = self.name_edit.text()

        title_font_family = (
            self.fonts.get(
                "Beaufort Bold",
                "Arial"
            )
        )

        title_font = QFont(
            title_font_family,
            TITLE_FONT_SIZE
        )

        # Disable Qt's hint-fitting for this font. Beaufort's outlines
        # are PostScript/CFF curves (not TrueType), and Qt's hinter can
        # snap control points to the pixel grid in a way that corrupts
        # compound curves (the counter in "A", the spur in "G") at
        # small point sizes, while simple straight strokes are
        # unaffected. PreferNoHinting draws the outline as designed.
        title_font.setHintingPreference(
            QFont.HintingPreference.PreferNoHinting
        )

        # IMPORTANT: BeaufortForLOL-Bold.otf and BeaufortForLOL-Regular.otf
        # both register under the exact same internal family name
        # ("Beaufort for LOL") - Bold and Regular are two weights of one
        # family, not two separate families. That means QFont(family)
        # alone is ambiguous: without an explicit weight, Qt defaults to
        # picking the Regular (400) face. We have to ask for Bold (700)
        # explicitly to get the actual bold file. (Earlier we removed
        # setBold(True) here thinking it was the cause of the glyph
        # corruption bug - it wasn't, the hinting was. This weight
        # request is safe to have back now that hinting is disabled.)
        title_font.setWeight(
            QFont.Weight.Bold
        )

        painter.setFont(
            title_font
        )

        painter.setPen(
            QColor(
                CARD_TEXT
            )
        )

        title_rect = QRectF(
            TITLE_X,
            TITLE_Y,
            TITLE_WIDTH,
            TITLE_HEIGHT
        )

        painter.drawText(
            title_rect,
            TITLE_ALIGNMENT,
            name
        )


        # ====================================================
        # TAG BOXES
        # ====================================================

        self.draw_tag_boxes(
            painter
        )


        # ====================================================
        # DESCRIPTION
        # ====================================================

        description_html = (
            self.description_edit
            .toHtml()
        )

        description_font_family = (
            self.fonts.get(
                "Beaufort Regular",
                "Arial"
            )
        )

        default_font = QFont(
            description_font_family,
            DESCRIPTION_FONT_SIZE
        )

        default_font.setWeight(
            QFont.Normal
        )

        default_font.setHintingPreference(
            QFont.HintingPreference.PreferNoHinting
        )

        default_font.setLetterSpacing(
            QFont.AbsoluteSpacing,
            DESCRIPTION_LETTER_SPACING
        )

        document = QTextDocument()

        document.setDocumentMargin(
            0
        )

        document.setDefaultFont(
            default_font
        )

        document.setHtml(
            description_html
        )

        document.setTextWidth(
            DESCRIPTION_WIDTH
        )


        # ====================================================
        # DESCRIPTION ALIGNMENT
        # ====================================================

        alignment_css = "center"

        if DESCRIPTION_ALIGNMENT == Qt.AlignLeft:

            alignment_css = "left"

        elif DESCRIPTION_ALIGNMENT == Qt.AlignRight:

            alignment_css = "right"

        elif DESCRIPTION_ALIGNMENT == Qt.AlignJustify:

            alignment_css = "justify"


        aligned_html = (
            description_html
        )

        body_match = re.search(
            r"<body([^>]*)>",
            aligned_html,
            flags=re.IGNORECASE
        )

        if body_match:

            body_attributes = (
                body_match.group(1)
            )

            if (
                "style=" in body_attributes.lower()
            ):

                aligned_html = re.sub(
                    r'(<body[^>]*style=")([^"]*)(")',
                    rf'\1\2 text-align: {alignment_css};\3',
                    aligned_html,
                    count=1,
                    flags=re.IGNORECASE
                )

            else:

                replacement = (
                    f'<body{body_attributes} '
                    f'style="text-align: {alignment_css};">'
                )

                aligned_html = (
                    aligned_html[:body_match.start()]
                    + replacement
                    + aligned_html[body_match.end():]
                )

        else:

            aligned_html = (
                f'<div style="text-align: {alignment_css};">'
                f'{aligned_html}'
                f'</div>'
            )

        aligned_html = re.sub(
            r'font-family\s*:[^;"]+;?',
            '',
            aligned_html,
            flags=re.IGNORECASE
        )

        # ====================================================
        # FINAL DESCRIPTION DOCUMENT
        # ====================================================

        document = QTextDocument()

        document.setDocumentMargin(
            0
        )

        document.setDefaultFont(
            default_font
        )

        document.setHtml(
            aligned_html
        )

        document.setTextWidth(
            DESCRIPTION_WIDTH
        )

        description_rect = QRectF(
            DESCRIPTION_X,
            DESCRIPTION_Y,
            DESCRIPTION_WIDTH,
            DESCRIPTION_HEIGHT
        )

        painter.save()

        painter.translate(
            description_rect.left(),
            description_rect.top()
        )

        document.drawContents(
            painter,
            QRectF(
                0,
                0,
                DESCRIPTION_WIDTH,
                DESCRIPTION_HEIGHT
            )
        )

        painter.restore()


        # ====================================================
        # DEBUG BOUNDS
        # ====================================================

        self.draw_debug_bounds(
            painter
        )


        # ====================================================
        # FINISH
        # ====================================================

        painter.end()

        return base


    # ========================================================
    # UPDATE PREVIEW
    # ========================================================

    def update_preview(self):

        if not self.current_augment:
            return

        image = self.render_card()

        if image is None:
            return

        pixmap = QPixmap.fromImage(
            image
        )


        # ----------------------------------------------------
        # Fit card to preview panel
        # ----------------------------------------------------

        available_width = (
            self.preview.width() - 20
        )

        available_height = (
            self.preview.height() - 20
        )

        if (
            available_width <= 0
            or available_height <= 0
        ):

            return

        scaled = pixmap.scaled(
            available_width,
            available_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.preview.setPixmap(
            scaled
        )


    # ========================================================
    # EXPORT
    # ========================================================

    def export_card(self):

        if not self.current_augment:
            return

        image = self.render_card()

        if image is None:
            return

        output_dir = os.path.join(
            BASE_DIR,
            "Augment Cards"
        )

        os.makedirs(
            output_dir,
            exist_ok=True
        )

        name = (
            self.name_edit
            .text()
            .strip()
        )

        if not name:
            name = "augment"

        safe_name = "".join(
            c
            for c in name
            if c.isalnum()
            or c in " _-"
        ).strip()

        if not safe_name:
            safe_name = "augment"

        default_path = os.path.join(
            output_dir,
            f"{safe_name}.png"
        )

        # Open the Save As dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Augment Card",
            default_path,
            "PNG Images (*.png)"
        )

        # If the user clicks Cancel, file_path will be empty
        if not file_path:
            return

        image.save(
            file_path,
            "PNG"
        )

        print(
            f"Exported: {file_path}"
        )

# ============================================================
# START
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    window = AugmentCreator()

    window.show()

    window.update_preview()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":

    main()