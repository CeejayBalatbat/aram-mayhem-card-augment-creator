# ARAM Mayhem Augment Creator.
# Desktop editor that loads scraped augment data, lets you edit the
# name, tags and description, and renders a card PNG like the in-game one.

import json
import os
import sys
import glob
import re
import html

# Use FreeType on Windows so the League fonts render with the same
# spacing as in-game instead of Windows' DirectWrite hinting.
if sys.platform == "win32":
    os.environ.setdefault(
        "QT_QPA_PLATFORM",
        "windows:fontengine=freetype"
    )

from PySide6.QtCore import Qt, QRectF, QUrl
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QImage,
    QPainter,
    QPixmap,
    QTextCharFormat,
    QTextDocument,
    QTextImageFormat,
    QFontMetrics,
    QLinearGradient,
    QPainterPath,
    QPen,
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
    QComboBox,
    QCompleter,
)


# File and folder locations, all relative to this script.
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

STAT_ICONS_DIR = os.path.join(
    ASSETS_DIR,
    "stat_icons"
)

BACKGROUNDS_DIR = os.path.join(
    ASSETS_DIR,
    "backgrounds"
)

FONTS_DIR = os.path.join(
    ASSETS_DIR,
    "fonts"
)

EDITS_FILE = os.path.join(
    BASE_DIR,
    "augment_edits.json"
)

CHAMPION_ABILITIES_FILE = os.path.join(
    BASE_DIR,
    "champion_abilities.json"
)

ABILITY_ICONS_DIR = os.path.join(
    ASSETS_DIR,
    "ability_icons"
)

CHAMPION_ICONS_DIR = os.path.join(
    ASSETS_DIR,
    "champion_icons"
)

ABILITY_FRAMES_DIR = os.path.join(
    ASSETS_DIR,
    "ability_frames"
)


# Stat icons offered in the "Stat Icons" menu: menu label -> file in assets/stat_icons.
STAT_ICONS = {
    "Attack Damage": "attack_damage.png",
    "Ability Power": "ability_power.png",
    "Attack Speed": "attack_speed.png",
    "Ability Haste": "ability_haste.png",
    "Armor": "armor.png",
    "Magic Resist": "magic_resist.png",
    "Health": "health.png",
    "Movement Speed": "movement_speed.png",
    "Tenacity": "tenacity.png",
    "Adaptive Force": "adaptive_force.png",
    "Critical Strike": "critical_strike.png",
    "On-Hit": "on_hit.png",
    "Cooldown": "cooldown.png",
}


# Size of the rendered card in pixels.
CARD_WIDTH = 380
CARD_HEIGHT = 580


# Set True to draw colored outlines around each layout area on the card.
DEBUG_BOUNDS = False


# Augment icon box: size and top-left position on the card.
ICON_SIZE = 165

ICON_X = 107
ICON_Y = 48


# Title (augment name) box position, size, font size and alignment.
TITLE_X = 30
TITLE_Y = 260

TITLE_WIDTH = 320
TITLE_HEIGHT = 40

TITLE_FONT_SIZE = 18

TITLE_ALIGNMENT = Qt.AlignCenter


# Tag row: area on the card where the tag pills are centered.
TAG_AREA_X = 30
TAG_AREA_Y = 303

TAG_AREA_WIDTH = 320
TAG_AREA_HEIGHT = 23

# Spacing and padding around each tag pill.
TAG_GAP = 6

TAG_PADDING_X = 4
TAG_PADDING_Y = 1

# Width limits for a single tag pill.
TAG_MAX_WIDTH = 180
TAG_MIN_WIDTH = 0

TAG_BOX_RADIUS = 2

TAG_FONT_SIZE = 12

TAG_TEXT_ALIGNMENT = Qt.AlignCenter

# Normal tag pill colors: gradient edge, gradient center, text.
TAG_BOX_COLOR_EDGE = "#89877a"
TAG_BOX_COLOR_CENTER = "#9b9d94"
TAG_TEXT_COLOR = "#1A1A1A"

# "Quest" tag pill colors (gold).
TAG_QUEST_BOX_COLOR_EDGE = "#f0c200"
TAG_QUEST_BOX_COLOR_CENTER = "#e9c117"
TAG_QUEST_TEXT_COLOR = "#111111"

# Optional outline around each tag pill (0 = no outline).
TAG_BORDER_WIDTH = 0
TAG_BORDER_COLOR = "#000000"

# Drop shadow drawn behind each tag pill.
TAG_SHADOW_OFFSET_X = 1
TAG_SHADOW_OFFSET_Y = 1
TAG_SHADOW_COLOR = "#80000000"


# Description text box position, size, font and alignment.
DESCRIPTION_X = 42
DESCRIPTION_Y = 350

DESCRIPTION_WIDTH = 300
DESCRIPTION_HEIGHT = 200

DESCRIPTION_FONT_SIZE = 15

DESCRIPTION_LETTER_SPACING = .75

DESCRIPTION_ALIGNMENT = Qt.AlignCenter

# Default height of inline stat icons, with per-icon overrides below.
STAT_ICON_SIZE = 12

STAT_ICON_CUSTOM_SIZES = {
    "critical_strike.png": 16,
    "on_hit.png": 14,
    "cooldown.png": 14,
    
}


# Gold "?" in scraped descriptions marks an augment that targets one of your
# abilities; its presence switches on the champion/ability picker.
ABILITY_PLACEHOLDER = "<font color='#F0C200'>?</font>"

ABILITY_GOLD = "#F0C200"

# Ability slots, in the order they appear in the skill dropdown.
ABILITY_KEYS = ["Q", "W", "E", "R"]

# Augments locked to one ability slot (augment id -> key), so the
# skill dropdown only offers that slot.
FIXED_ABILITY_KEYS = {
    "1103": "Q",
    "1150": "W",
    "1151": "E",
}

# Augments that draw a special frame instead of their normal icon when
# an ability is picked (augment id -> file in assets/ability_frames).
ABILITY_FRAMES = {
    "2064": "quickstep_frame.png",
}

ABILITY_FRAME_SIZE = 178

# Ability icon drawn in the middle of the augment icon, plus its border.
ABILITY_ICON_SIZE = 64
ABILITY_ICON_BORDER_WIDTH = 2
ABILITY_ICON_BORDER_COLOR = "#c9b489"

# "[Q]" key label drawn under the ability icon.
ABILITY_KEY_Y = 170
ABILITY_KEY_HEIGHT = 22
ABILITY_KEY_FONT_SIZE = 14

# Round champion portrait in the card's top-left corner.
PORTRAIT_X = 10
PORTRAIT_Y = 10
PORTRAIT_SIZE = 56
PORTRAIT_RING_WIDTH = 4
PORTRAIT_RING_COLOR = "#d9c7a0"


# Editor window colors (not used on the card itself).
BG = "#101216"
PANEL = "#181b21"
PANEL_2 = "#20242c"
BORDER = "#303640"

TEXT = "#eeeeee"
SUBTEXT = "#9da3ad"
ACCENT = "#c8a96b"

# Card text colors: title text and League keyword highlight.
CARD_TEXT = "#eae7da"

LEAGUE_HIGHLIGHT = "#C8AA6E"


# League fonts bundled in assets/fonts: display name -> file.
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


# Registers the bundled fonts with Qt and returns
# {display name: Qt family name} for the ones that loaded.
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


# Converts Riot's description markup (<scaleAD>, <status>, <br>, ...) into
# HTML the QTextEdit understands. Highlight tags become gold <font> spans,
# explicit <font color> tags keep their color, and any other tag is dropped.
def convert_league_markup(text):

    if not text:
        return ""

    replacements = {}

    # Swaps a highlight tag for a placeholder so html.escape() below
    # doesn't mangle it; the placeholder is turned back into HTML later.
    def protect_tag(match):

        key = f"___LEAGUE_TAG_{len(replacements)}___"

        replacements[key] = (
            LEAGUE_HIGHLIGHT,
            match.group(2)
        )

        return key

    # Same as protect_tag, but keeps the tag's own color.
    def protect_font(match):

        key = f"___LEAGUE_TAG_{len(replacements)}___"

        replacements[key] = (
            match.group(1),
            match.group(2)
        )

        return key

    # Line breaks become real newlines first so they survive escaping.
    text = re.sub(
        r"<br\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"<font color=['\"](#[0-9A-Fa-f]{6})['\"]>(.*?)</font>",
        protect_font,
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    protected = re.sub(
        r"<(scale[A-Za-z0-9_]+|attention|status|keyword[A-Za-z0-9_]*|magicDamage|physicalDamage|trueDamage)>(.*?)</\1>",
        protect_tag,
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    # Escape everything else so stray < > & show as text.
    protected = html.escape(
        protected
    )

    # Put the protected highlights back as colored <font> spans.
    for key, (
        color,
        content
    ) in replacements.items():

        content = html.escape(
            content
        )

        replacement = (
            f'<font color="{color}">'
            f'{content}'
            f'</font>'
        )

        protected = protected.replace(
            key,
            replacement
        )

    # Remove any leftover (now escaped) tags the editor wouldn't understand.
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


# Main window: augment list on the left, editor in the middle, live
# card preview on the right.
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

        # augments.json entries, and the one currently open in the editor.
        self.augments = []

        self.current_augment = None

        # Tags shown on the card for the current augment.
        self.tags = []

        # champion_abilities.json data, keyed by champion id.
        self.champions = {}

        self.is_ability_augment = False

        # Saved edits keyed by augment id, and the editor state as it was when
        # the current augment was opened (used to detect unsaved changes).
        self.edits = {}

        self.loaded_state = None

        self.load_settings()

        self.load_augments()

        self.load_champions()

        self.load_edits()

        self.build_ui()

        self.populate_augment_list()


    # Reads the scraped augment list from augments.json.
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


    # Reads champion and ability names/icons for the ability picker.
    def load_champions(self):

        if not os.path.exists(
            CHAMPION_ABILITIES_FILE
        ):

            print(
                f"Could not find {CHAMPION_ABILITIES_FILE} "
                "- run champion_ability_scraper.py"
            )

            return

        with open(
            CHAMPION_ABILITIES_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        self.champions = data.get(
            "champions",
            {}
        )

        print(
            f"Loaded {len(self.champions)} champions"
        )


    # Reads saved edits from augment_edits.json, starting empty if it's
    # missing or unreadable.
    def load_edits(self):

        if not os.path.exists(
            EDITS_FILE
        ):
            return

        try:

            with open(
                EDITS_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                self.edits = json.load(f)

        except (OSError, json.JSONDecodeError) as e:

            print(
                f"Could not read {EDITS_FILE}: {e}"
            )

            self.edits = {}

        print(
            f"Loaded {len(self.edits)} saved edits"
        )


    # Writes all saved edits back to augment_edits.json.
    def write_edits(self):

        with open(
            EDITS_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.edits,
                f,
                indent=2,
                ensure_ascii=False
            )


    # Snapshot of everything the user can edit, as stored in augment_edits.json.
    def get_editor_state(self):

        return {
            "name": self.name_edit.text(),
            "tags": list(self.tags),
            "description_html": self.description_edit.toHtml(),
            "champion": self.champion_combo.currentData(),
            "skill": self.skill_combo.currentData(),
        }


    # Id of the augment open in the editor, as a string.
    def get_current_augment_id(self):

        if not self.current_augment:
            return None

        return str(
            self.current_augment.get(
                "id",
                ""
            )
        )


    # Stores the editor's current state as the saved edit for this augment.
    # With only_if_changed=True (autosave) it skips saving when nothing changed.
    def save_current_edit(
        self,
        only_if_changed=False
    ):

        augment_id = self.get_current_augment_id()

        if not augment_id:
            return

        state = self.get_editor_state()

        if (
            only_if_changed
            and state == self.loaded_state
        ):
            return

        self.edits[augment_id] = state

        self.write_edits()

        self.loaded_state = state

        self.refresh_list_item_styles()

        self.statusBar().showMessage(
            f"Saved {state['name']}",
            3000
        )


    # Deletes the saved edit for this augment and reloads the original data.
    def reset_current_edit(self):

        augment_id = self.get_current_augment_id()

        if not augment_id:
            return

        if augment_id in self.edits:

            del self.edits[augment_id]

            self.write_edits()

        item = self.augment_list.currentItem()

        if item:

            self.select_augment(
                item,
                autosave=False
            )

        self.refresh_list_item_styles()

        self.statusBar().showMessage(
            "Reset to original",
            3000
        )


    # Loads a saved edit into the editor fields. Signals are blocked while
    # setting values so each field doesn't trigger its own preview render.
    def apply_saved_edit(
        self,
        augment_id
    ):

        edit = self.edits.get(
            augment_id
        )

        if not edit:
            return

        self.name_edit.blockSignals(
            True
        )

        self.name_edit.setText(
            edit.get(
                "name",
                self.name_edit.text()
            )
        )

        self.name_edit.blockSignals(
            False
        )

        self.tags = list(
            edit.get(
                "tags",
                self.tags
            )
        )

        self.update_tags_display()

        if edit.get("champion"):

            index = self.champion_combo.findData(
                edit["champion"]
            )

            if index >= 0:

                self.champion_combo.blockSignals(
                    True
                )

                self.champion_combo.setCurrentIndex(
                    index
                )

                self.champion_combo.blockSignals(
                    False
                )

                self.populate_skill_combo()

        if edit.get("skill"):

            index = self.skill_combo.findData(
                edit["skill"]
            )

            if index >= 0:

                self.skill_combo.blockSignals(
                    True
                )

                self.skill_combo.setCurrentIndex(
                    index
                )

                self.skill_combo.blockSignals(
                    False
                )

        if edit.get("description_html"):

            self.description_edit.blockSignals(
                True
            )

            self.description_edit.setHtml(
                edit["description_html"]
            )

            self.description_edit.blockSignals(
                False
            )


    # Shows augments with saved edits in italic gold in the list.
    def refresh_list_item_styles(self):

        for i in range(
            self.augment_list.count()
        ):

            item = self.augment_list.item(
                i
            )

            augment = item.data(
                Qt.UserRole
            )

            augment_id = str(
                augment.get(
                    "id",
                    ""
                )
            )

            edited = augment_id in self.edits

            font = item.font()

            font.setItalic(
                edited
            )

            item.setFont(
                font
            )

            item.setForeground(
                QColor(ACCENT)
                if edited
                else QColor(TEXT)
            )

            item.setToolTip(
                "Has saved edits"
                if edited
                else ""
            )


    # Autosaves the open augment when the window closes.
    def closeEvent(
        self,
        event
    ):

        self.save_current_edit(
            only_if_changed=True
        )

        super().closeEvent(
            event
        )


    # Restores the custom colors saved in the color picker.
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


    # Saves the color picker's custom colors to settings.json.
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


    # Builds the three-panel window layout and its stylesheet.
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


        # Left panel: search box and augment list.
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


        # Center panel: editor fields.
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


        # Name field.
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


        # Tag input plus the row of removable tag buttons.
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


        # Champion and ability picker, only shown for ability augments.
        self.ability_section = QWidget()

        ability_section_layout = QVBoxLayout(
            self.ability_section
        )

        ability_section_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        ability_label = QLabel(
            "Ability"
        )

        ability_label.setObjectName(
            "label"
        )

        ability_section_layout.addWidget(
            ability_label
        )

        ability_row = QHBoxLayout()

        self.champion_combo = QComboBox()

        self.champion_combo.setEditable(
            True
        )

        self.champion_combo.setInsertPolicy(
            QComboBox.NoInsert
        )

        self.champion_combo.addItem(
            "No champion",
            None
        )

        for champion_id, champion in self.champions.items():

            self.champion_combo.addItem(
                champion["name"],
                champion_id
            )

        # Let the champion box match text anywhere in the name while typing.
        completer = self.champion_combo.completer()

        completer.setFilterMode(
            Qt.MatchContains
        )

        completer.setCompletionMode(
            QCompleter.PopupCompletion
        )

        self.champion_combo.currentIndexChanged.connect(
            self.on_champion_changed
        )

        ability_row.addWidget(
            self.champion_combo,
            3
        )

        self.skill_combo = QComboBox()

        self.skill_combo.currentIndexChanged.connect(
            self.update_preview
        )

        ability_row.addWidget(
            self.skill_combo,
            4
        )

        ability_section_layout.addLayout(
            ability_row
        )

        center_layout.addWidget(
            self.ability_section
        )

        self.ability_section.setVisible(
            False
        )

        self.populate_skill_combo()


        # Description formatting toolbar.
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


        color_button = QPushButton(
            "Text Color"
        )

        color_button.clicked.connect(
            self.change_text_color
        )

        toolbar.addWidget(
            color_button
        )


        stat_icon_button = QPushButton(
            "Stat Icons"
        )

        stat_icon_menu = self.build_stat_icon_menu(
            stat_icon_button
        )

        stat_icon_button.setMenu(
            stat_icon_menu
        )

        toolbar.addWidget(
            stat_icon_button
        )


        toolbar.addStretch()

        center_layout.addLayout(
            toolbar
        )


        # Rich-text description editor, using the card's description font.
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


        # Save and reset buttons.
        save_row = QHBoxLayout()

        save_button = QPushButton(
            "Save Changes  (Ctrl+S)"
        )

        save_button.setShortcut(
            "Ctrl+S"
        )

        save_button.clicked.connect(
            lambda: self.save_current_edit()
        )

        save_row.addWidget(
            save_button
        )

        reset_button = QPushButton(
            "Reset to Original"
        )

        reset_button.clicked.connect(
            self.reset_current_edit
        )

        save_row.addWidget(
            reset_button
        )

        save_row.addStretch()

        center_layout.addLayout(
            save_row
        )


        # Right panel: card preview and export button.
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


        # Panel width ratio 1:2:2.
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


        # Dark theme for the editor window.
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
            QListWidget,
            QComboBox {{
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


    # Fills the left list with every augment; each item keeps its augment
    # dict in Qt.UserRole.
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

        self.refresh_list_item_styles()


    # Hides list items whose name doesn't contain the search text.
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


    # Opens an augment in the editor: autosaves the previous one, fills every
    # field from the scraped data, then applies any saved edit on top.
    def select_augment(
        self,
        item,
        autosave=True
    ):

        if autosave:

            self.save_current_edit(
                only_if_changed=True
            )

        augment = item.data(
            Qt.UserRole
        )

        self.current_augment = augment


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


        self.tags = list(
            augment.get(
                "tags",
                []
            )
        )

        self.update_tags_display()


        # Ability augments are detected by the gold "?" placeholder.
        self.is_ability_augment = (
            ABILITY_PLACEHOLDER
            in augment.get(
                "description",
                ""
            )
        )

        self.ability_section.setVisible(
            self.is_ability_augment
        )

        self.populate_skill_combo()


        # Description is converted from Riot markup to editor HTML.
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


        # Reset the bold/italic toggles for the new text.
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


        # Saved edits override the scraped values.
        self.apply_saved_edit(
            self.get_current_augment_id()
        )

        self.loaded_state = self.get_editor_state()


        self.update_preview()


    # Picking a new champion refreshes its ability list and the preview.
    def on_champion_changed(self):

        self.populate_skill_combo()

        self.update_preview()


    # Refills the skill dropdown with the chosen champion's abilities, keeping
    # the same slot selected when possible. Locked augments only list their
    # fixed slot and disable the dropdown.
    def populate_skill_combo(self):

        previous_key = self.skill_combo.currentData()

        self.skill_combo.blockSignals(
            True
        )

        self.skill_combo.clear()

        champion = self.get_selected_champion()

        fixed_key = None

        if self.current_augment:

            fixed_key = FIXED_ABILITY_KEYS.get(
                str(
                    self.current_augment.get(
                        "id",
                        ""
                    )
                )
            )

        if champion:

            abilities = champion.get(
                "abilities",
                {}
            )

            for key in ABILITY_KEYS:

                if fixed_key and key != fixed_key:
                    continue

                ability = abilities.get(key)

                if not ability:
                    continue

                self.skill_combo.addItem(
                    f"{key} - {ability['name']}",
                    key
                )

            index = self.skill_combo.findData(
                previous_key
            )

            if index >= 0:

                self.skill_combo.setCurrentIndex(
                    index
                )

        self.skill_combo.setEnabled(
            champion is not None
            and fixed_key is None
        )

        self.skill_combo.blockSignals(
            False
        )


    # Champion dict for the champion dropdown's selection, or None.
    def get_selected_champion(self):

        champion_id = self.champion_combo.currentData()

        if not champion_id:
            return None

        return self.champions.get(
            champion_id
        )


    # Returns (key, ability) for the chosen skill, or None when this isn't
    # an ability augment or nothing is chosen.
    def get_selected_ability(self):

        if not self.is_ability_augment:
            return None

        champion = self.get_selected_champion()

        key = self.skill_combo.currentData()

        if not champion or not key:
            return None

        ability = champion.get(
            "abilities",
            {}
        ).get(
            key
        )

        if not ability:
            return None

        return key, ability


    # Path of this augment's special ability frame, if it has one.
    def find_ability_frame(self):

        if not self.current_augment:
            return None

        filename = ABILITY_FRAMES.get(
            str(
                self.current_augment.get(
                    "id",
                    ""
                )
            )
        )

        if not filename:
            return None

        path = os.path.join(
            ABILITY_FRAMES_DIR,
            filename
        )

        if os.path.exists(
            path
        ):

            return path

        return None


    # Replaces the gold "?" in the description HTML with the chosen ability's
    # name for the rendered card. The editor keeps the "?" so the champion
    # can be changed at any time.
    def fill_ability_name(
        self,
        description_html
    ):

        selected = self.get_selected_ability()

        if not selected:
            return description_html

        key, ability = selected

        ability_name = html.escape(
            ability["name"]
        )

        return re.sub(
            r'(<span style="[^"]*color:\s*#f0c200;?[^"]*">)\?(</span>)',
            lambda match: (
                match.group(1)
                + ability_name
                + match.group(2)
            ),
            description_html,
            flags=re.IGNORECASE
        )


    # Draws the ability augment extras: champion portrait in the corner,
    # ability icon over the augment icon, and the "[Q]" key label.
    def draw_ability_overlay(
        self,
        painter
    ):

        if not self.is_ability_augment:
            return

        center_x = ICON_X + ICON_SIZE / 2
        center_y = ICON_Y + ICON_SIZE / 2


        # Round champion portrait with a colored ring.
        champion = self.get_selected_champion()

        if champion:

            portrait_path = os.path.join(
                CHAMPION_ICONS_DIR,
                champion.get(
                    "icon",
                    ""
                )
            )

            if os.path.exists(
                portrait_path
            ):

                portrait = QPixmap(
                    portrait_path
                ).scaled(
                    PORTRAIT_SIZE,
                    PORTRAIT_SIZE,
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )

                portrait_rect = QRectF(
                    PORTRAIT_X,
                    PORTRAIT_Y,
                    PORTRAIT_SIZE,
                    PORTRAIT_SIZE
                )

                clip = QPainterPath()

                clip.addEllipse(
                    portrait_rect
                )

                painter.save()

                painter.setClipPath(
                    clip
                )

                painter.drawPixmap(
                    PORTRAIT_X,
                    PORTRAIT_Y,
                    portrait
                )

                painter.restore()

                painter.save()

                painter.setPen(
                    QPen(
                        QColor(
                            PORTRAIT_RING_COLOR
                        ),
                        PORTRAIT_RING_WIDTH
                    )
                )

                painter.setBrush(
                    Qt.NoBrush
                )

                ring_inset = PORTRAIT_RING_WIDTH / 2

                painter.drawEllipse(
                    portrait_rect.adjusted(
                        ring_inset,
                        ring_inset,
                        -ring_inset,
                        -ring_inset
                    )
                )

                painter.restore()


        # Everything below needs an ability picked.
        selected = self.get_selected_ability()

        if not selected:
            return

        key, ability = selected


        # Ability icon centered on the augment icon, with a square border.
        ability_icon_path = os.path.join(
            ABILITY_ICONS_DIR,
            ability["icon"]
        )

        if os.path.exists(
            ability_icon_path
        ):

            ability_icon = QPixmap(
                ability_icon_path
            ).scaled(
                ABILITY_ICON_SIZE,
                ABILITY_ICON_SIZE,
                Qt.IgnoreAspectRatio,
                Qt.SmoothTransformation
            )

            icon_rect = QRectF(
                center_x - ABILITY_ICON_SIZE / 2,
                center_y - ABILITY_ICON_SIZE / 2,
                ABILITY_ICON_SIZE,
                ABILITY_ICON_SIZE
            )

            painter.drawPixmap(
                icon_rect.toRect(),
                ability_icon
            )

            painter.save()

            painter.setPen(
                QPen(
                    QColor(
                        ABILITY_ICON_BORDER_COLOR
                    ),
                    ABILITY_ICON_BORDER_WIDTH
                )
            )

            painter.setBrush(
                Qt.NoBrush
            )

            painter.drawRect(
                icon_rect
            )

            painter.restore()


        # "[Q]"-style key label under the icon.
        key_font = QFont(
            self.fonts.get(
                "Beaufort Bold",
                "Arial"
            ),
            ABILITY_KEY_FONT_SIZE
        )

        key_font.setHintingPreference(
            QFont.HintingPreference.PreferNoHinting
        )

        key_font.setWeight(
            QFont.Weight.Bold
        )

        painter.save()

        painter.setFont(
            key_font
        )

        painter.setPen(
            QColor(
                ABILITY_GOLD
            )
        )

        painter.drawText(
            QRectF(
                TITLE_X,
                ABILITY_KEY_Y,
                TITLE_WIDTH,
                ABILITY_KEY_HEIGHT
            ),
            Qt.AlignCenter,
            f"[{key}]"
        )

        painter.restore()


    # Adds the typed tag (skipping duplicates) and refreshes the display.
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


    # Rebuilds the row of tag buttons; clicking one removes that tag.
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


    # Removes the tag at the given position.
    def remove_tag(self, index):

        if index < 0:
            return

        if index >= len(self.tags):
            return

        self.tags.pop(index)

        self.update_tags_display()

        self.update_preview()


    # Toggles bold on the selected description text.
    def toggle_bold(self):

        cursor = self.description_edit.textCursor()

        if not cursor.hasSelection():
            return

        format = QTextCharFormat()

        current_weight = (
            cursor.charFormat()
            .fontWeight()
        )

        if current_weight == QFont.Bold:

            format.setFontWeight(
                QFont.Normal
            )

        else:

            format.setFontWeight(
                QFont.Bold
            )

        cursor.mergeCharFormat(
            format
        )

        self.description_edit.setTextCursor(
            cursor
        )

        self.update_preview()


    # Sets italic on the selected text to match the italic button.
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


    # Colors the selected text with a color picked from a dialog, then saves
    # the dialog's custom colors so they persist between runs.
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

        self.save_settings()

        self.update_preview()


    # Builds the "Stat Icons" dropdown menu, one entry per STAT_ICONS item.
    def build_stat_icon_menu(
        self,
        button
    ):

        from PySide6.QtWidgets import QMenu

        menu = QMenu(
            button
        )

        for label, filename in STAT_ICONS.items():

            icon_path = os.path.join(
                STAT_ICONS_DIR,
                filename
            )

            action = menu.addAction(
                label
            )

            action.triggered.connect(
                lambda checked=False,
                path=icon_path:
                self.insert_stat_icon(path)
            )

        return menu


    # Inserts a stat icon as an inline image at the cursor, sized to the
    # icon's configured height while keeping its aspect ratio.
    def insert_stat_icon(
        self,
        icon_path
    ):

        if not os.path.exists(
            icon_path
        ):
            print(
                f"Stat icon not found: {icon_path}"
            )
            return

        filename = os.path.basename(icon_path)
        base_size = STAT_ICON_CUSTOM_SIZES.get(filename, STAT_ICON_SIZE)

        reader = QImage(icon_path)
        if not reader.isNull() and reader.height() > 0:
            aspect_ratio = reader.width() / reader.height()
            target_height = base_size
            target_width = int(round(target_height * aspect_ratio))
        else:
            target_width = base_size
            target_height = base_size

        cursor = (
            self.description_edit
            .textCursor()
        )

        image_format = QTextImageFormat()

        image_format.setName(
            QUrl.fromLocalFile(
                icon_path
            ).toString()
        )

        image_format.setWidth(
            target_width
        )

        image_format.setHeight(
            target_height
        )

        # These icons sit better centered on the text line.
        if filename in ["critical_strike.png", "on_hit.png"]:
            image_format.setVerticalAlignment(
                QTextImageFormat.AlignMiddle
            )

        cursor.insertImage(
            image_format
        )

        self.description_edit.setTextCursor(
            cursor
        )

        self.description_edit.ensureCursorVisible()

        self.update_preview()


    # Pre-loads every local image in the HTML into the render document,
    # trimming transparent borders so icons line up with the text.
    def register_stat_icons_in_document(
        self,
        document,
        html_text
    ):

        image_urls = re.findall(
            r'<img[^>]+src="([^"]+)"',
            html_text,
            flags=re.IGNORECASE
        )

        for image_url in image_urls:

            if not image_url.startswith(
                "file:///"
            ):
                continue

            image_path = QUrl(
                image_url
            ).toLocalFile()

            if not os.path.exists(
                image_path
            ):
                continue

            image = QImage(
                image_path
            )

            if image.isNull():
                continue

            image = image.convertToFormat(QImage.Format_ARGB32)

            # Find the bounding box of pixels that aren't (nearly) transparent.
            min_x, min_y = image.width(), image.height()
            max_x, max_y = -1, -1

            for y in range(image.height()):
                for x in range(image.width()):
                    if (image.pixel(x, y) >> 24) & 0xFF > 15:
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)

            if max_x >= min_x and max_y >= min_y:
                image = image.copy(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)

            document.addResource(
                QTextDocument.ImageResource,
                QUrl(image_url),
                image
            )


    # Finds the augment's icon file. Tries, in order: the path as given, the
    # file in assets/icons, the filename anywhere under assets/icons, then
    # any icon file containing the augment's id or name.
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


    # Picks the card background from the augment's rarity
    # (2/prismatic, 1/gold, anything else silver).
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


    # Draws the tag pills centered in the tag row: shadow, horizontal
    # gradient fill, then the text. "Quest" tags use the gold colors.
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

        tags_font.setWeight(
            QFont.Weight.Bold
        )

        metrics = QFontMetrics(
            tags_font
        )

        # Measure each tag so the whole row can be centered.
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

                    is_quest = str(tag).strip().lower() == "quest"


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


                    edge_color = TAG_QUEST_BOX_COLOR_EDGE if is_quest else TAG_BOX_COLOR_EDGE
                    center_color = TAG_QUEST_BOX_COLOR_CENTER if is_quest else TAG_BOX_COLOR_CENTER

                    gradient = QLinearGradient(
                        rect.left(),
                        rect.top(),
                        rect.right(),
                        rect.top()
                    )

                    gradient.setColorAt(
                        0.0,
                        QColor(edge_color)
                    )

                    gradient.setColorAt(
                        0.5,
                        QColor(center_color)
                    )

                    gradient.setColorAt(
                        1.0,
                        QColor(edge_color)
                    )

                    if TAG_BORDER_WIDTH > 0:

                        painter.setPen(
                            QColor(TAG_BORDER_COLOR)
                        )

                    else:

                        painter.setPen(
                            Qt.NoPen
                        )

                    painter.setBrush(
                        gradient
                    )

                    painter.drawRoundedRect(
                        rect,
                        TAG_BOX_RADIUS,
                        TAG_BOX_RADIUS
                    )


                    painter.setFont(
                        tags_font
                    )

                    text_color = TAG_QUEST_TEXT_COLOR if is_quest else TAG_TEXT_COLOR
                    painter.setPen(
                        QColor(
                            text_color
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


    # Outlines the icon, title, tag and description areas when DEBUG_BOUNDS is on.
    def draw_debug_bounds(
        self,
        painter
    ):

        if not DEBUG_BOUNDS:
            return

        painter.save()

        pen = painter.pen()

        pen.setWidth(
            2
        )


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


    # Renders the full card as a QImage: background, icon, ability overlay,
    # title, tags and description, in that order.
    def render_card(self):

        if not self.current_augment:
            return None


        # Background for the augment's rarity, or plain dark if it's missing.
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


        # Augment icon, or the special ability frame when one applies,
        # centered in the icon box.
        icon_path = self.find_icon()

        icon_size = ICON_SIZE

        frame_path = self.find_ability_frame()

        if (
            frame_path
            and self.get_selected_ability()
        ):

            icon_path = frame_path

            icon_size = ABILITY_FRAME_SIZE

        if icon_path:

            icon = QPixmap(
                icon_path
            )

            icon = icon.scaled(
                icon_size,
                icon_size,
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


        self.draw_ability_overlay(
            painter
        )


        # Title.
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

        title_font.setHintingPreference(
            QFont.HintingPreference.PreferNoHinting
        )

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


        self.draw_tag_boxes(
            painter
        )


        # Description: the editor's HTML with the ability name filled in,
        # drawn through a QTextDocument so formatting and icons are kept.
        description_html = (
            self.description_edit
            .toHtml()
        )

        description_html = self.fill_ability_name(
            description_html
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


        # Force the configured alignment by adding text-align to <body>.
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


        # Strip font-family from the editor HTML so the card font is always used.
        aligned_html = re.sub(
            r'font-family\s*:[^;"]+;?',
            '',
            aligned_html,
            flags=re.IGNORECASE
        )


        # Lay the description out at the card's text width.
        document = QTextDocument()

        document.setDocumentMargin(
            0
        )

        document.setDefaultFont(
            default_font
        )

        self.register_stat_icons_in_document(
            document,
            aligned_html
        )

        document.setHtml(
            aligned_html
        )

        document.setTextWidth(
            DESCRIPTION_WIDTH
        )


        # Draw it inside the description box.
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


        self.draw_debug_bounds(
            painter
        )


        painter.end()

        return base


    # Re-renders the card and scales it to fit the preview panel.
    def update_preview(self):

        if not self.current_augment:
            return

        image = self.render_card()

        if image is None:
            return

        pixmap = QPixmap.fromImage(
            image
        )


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


    # Renders the card and saves it as a PNG through a Save As dialog, defaulting
    # to "Augment Cards/<name>.png" with unsafe filename characters removed.
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

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Augment Card",
            default_path,
            "PNG Images (*.png)"
        )

        if not file_path:
            return

        image.save(
            file_path,
            "PNG"
        )

        print(
            f"Exported: {file_path}"
        )


# Starts the Qt app and shows the main window.
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