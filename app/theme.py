"""浅色办公风全局样式。"""

LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #F5F6F8;
    color: #1F2329;
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 13px;
}

QFrame#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #E5E6EB;
}

QLabel#appTitle {
    font-size: 15px;
    font-weight: 600;
    color: #1F2329;
    padding: 16px 16px 8px 16px;
}

QLabel#sidebarSection {
    font-size: 11px;
    color: #86909C;
    padding: 8px 16px 4px 16px;
}

QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
    padding: 4px 8px;
}

QListWidget::item {
    border-radius: 6px;
    padding: 10px 12px;
    margin: 2px 0;
    color: #4E5969;
}

QListWidget::item:selected {
    background-color: #E8F3FF;
    color: #1677FF;
    font-weight: 500;
}

QListWidget::item:hover:!selected {
    background-color: #F2F3F5;
}

QListWidget#resultList {
    background-color: #FFFFFF;
    border: 1px solid #E5E6EB;
    border-radius: 8px;
    padding: 8px;
}

QListWidget#resultList::item {
    border: 1px solid #F2F3F5;
    border-radius: 8px;
    padding: 12px 14px;
    margin: 4px 0;
    color: #1F2329;
}

QLabel#toolTitle {
    font-size: 18px;
    font-weight: 600;
    color: #1F2329;
    padding-bottom: 4px;
}

QPlainTextEdit#jsonEditor {
    background-color: #FFFFFF;
    border: 1px solid #E5E6EB;
    border-radius: 8px;
    padding: 12px;
    font-family: Consolas, "Cascadia Mono", "Courier New", monospace;
    font-size: 14px;
    color: #1F2329;
    selection-background-color: #BAE0FF;
}

QPlainTextEdit#jsonEditor:focus {
    border-color: #1677FF;
}

QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #E5E6EB;
    border-radius: 6px;
    padding: 8px 16px;
    color: #1F2329;
    min-height: 20px;
}

QPushButton:hover {
    border-color: #1677FF;
    color: #1677FF;
}

QPushButton:pressed {
    background-color: #E8F3FF;
}

QPushButton#primaryButton {
    background-color: #1677FF;
    border-color: #1677FF;
    color: #FFFFFF;
    font-weight: 500;
}

QPushButton#primaryButton:hover {
    background-color: #4096FF;
    border-color: #4096FF;
    color: #FFFFFF;
}

QPushButton#primaryButton:pressed {
    background-color: #0958D9;
    border-color: #0958D9;
}

QLabel#statusOk {
    color: #00B42A;
    padding: 4px 0;
}

QLabel#statusError {
    color: #F53F3F;
    padding: 4px 0;
}

QLabel#statusInfo {
    color: #86909C;
    padding: 4px 0;
}

QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #E5E6EB;
    color: #86909C;
}

QLineEdit#urlInput {
    background-color: #FFFFFF;
    border: 1px solid #E5E6EB;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 20px;
}

QLineEdit#urlInput:focus {
    border-color: #1677FF;
}

QComboBox#methodCombo {
    background-color: #FFFFFF;
    border: 1px solid #E5E6EB;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 20px;
}

QComboBox#methodCombo:focus {
    border-color: #1677FF;
}

QComboBox#methodCombo::drop-down {
    border: none;
    width: 24px;
}

QComboBox#methodCombo QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E5E6EB;
    selection-background-color: #E8F3FF;
    selection-color: #1677FF;
}

QComboBox#endpointCombo,
QComboBox#fieldCombo {
    background-color: #FFFFFF;
    border: 1px solid #E5E6EB;
    border-radius: 8px;
    padding: 8px 12px;
    padding-right: 36px;
    min-height: 22px;
    color: #1F2329;
}

QComboBox#endpointCombo:hover,
QComboBox#fieldCombo:hover {
    border-color: #4096FF;
}

QComboBox#endpointCombo:focus,
QComboBox#fieldCombo:focus {
    border-color: #1677FF;
}

QComboBox#endpointCombo::drop-down,
QComboBox#fieldCombo::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 32px;
    border-left: 1px solid #E5E6EB;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    background-color: #F7F8FA;
}

QComboBox#endpointCombo::drop-down:hover,
QComboBox#fieldCombo::drop-down:hover {
    background-color: #E8F3FF;
}

QComboBox#endpointCombo::down-arrow,
QComboBox#fieldCombo::down-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #4E5969;
    margin-right: 10px;
}

QComboBox#endpointCombo QAbstractItemView,
QComboBox#fieldCombo QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E5E6EB;
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: #E8F3FF;
    selection-color: #1677FF;
}

QComboBox#endpointCombo QAbstractItemView::item,
QComboBox#fieldCombo QAbstractItemView::item {
    min-height: 32px;
    padding: 6px 12px;
    border-radius: 6px;
    color: #1F2329;
}

QComboBox#endpointCombo QAbstractItemView::item:hover,
QComboBox#fieldCombo QAbstractItemView::item:hover {
    background-color: #F2F3F5;
}

QComboBox#endpointCombo QAbstractItemView::item:selected,
QComboBox#fieldCombo QAbstractItemView::item:selected {
    background-color: #E8F3FF;
    color: #1677FF;
}

QTextBrowser#markdownView {
    background-color: #FFFFFF;
    border: none;
    padding: 16px 20px;
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 14px;
    color: #1F2329;
    selection-background-color: #BAE0FF;
}

QTextBrowser#markdownView a {
    color: #1677FF;
    text-decoration: none;
}

QDialog {
    background-color: #F5F6F8;
}

QTabWidget#httpTabs::pane {
    border: 1px solid #E5E6EB;
    border-top: 1px solid #E5E6EB;
    border-radius: 0 0 8px 8px;
    background-color: #FFFFFF;
    top: 0;
    margin-top: 0;
    padding: 0;
}

QTabWidget#httpTabs QTabBar {
    qproperty-drawBase: 0;
}

QTabWidget#httpTabs QTabBar::tab {
    background-color: #F2F3F5;
    border: 1px solid #E5E6EB;
    border-bottom: 1px solid #E5E6EB;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 20px;
    margin-right: 2px;
    min-width: 80px;
    min-height: 14px;
    color: #4E5969;
}

QTabWidget#httpTabs QTabBar::tab:selected {
    background-color: #FFFFFF;
    border-bottom-color: #FFFFFF;
    color: #1677FF;
    font-weight: 500;
}

QTabWidget#httpTabs QTabBar::tab:!selected {
    margin-top: 2px;
}

QTabWidget#httpTabs QTabBar::tab:!selected:hover {
    background-color: #E8F3FF;
}

QPlainTextEdit#httpEditor {
    background-color: #FFFFFF;
    border: none;
    border-radius: 0;
    padding: 12px;
    font-family: Consolas, "Cascadia Mono", "Courier New", monospace;
    font-size: 14px;
    color: #1F2329;
    selection-background-color: #BAE0FF;
}

QPlainTextEdit#httpEditor:disabled {
    background-color: #F7F8FA;
    color: #86909C;
}

QLabel#sectionLabel {
    font-size: 14px;
    font-weight: 600;
    color: #1F2329;
}

QCheckBox {
    spacing: 6px;
    color: #4E5969;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #E5E6EB;
    border-radius: 4px;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #1677FF;
    border-color: #1677FF;
}

QSpinBox#timeoutSpin {
    background-color: #FFFFFF;
    border: 1px solid #E5E6EB;
    border-radius: 6px;
    padding: 4px 6px;
    min-height: 20px;
}

QSpinBox#timeoutSpin:focus {
    border-color: #1677FF;
}

QPushButton#stepButton {
    padding: 0;
    min-height: 0;
    font-size: 16px;
    font-weight: 600;
    color: #4E5969;
}

QPushButton#stepButton:hover {
    background-color: #E8F3FF;
    border-color: #1677FF;
    color: #1677FF;
}

QGroupBox#paramsBox {
    background-color: #FFFFFF;
    border: 1px solid #E5E6EB;
    border-radius: 8px;
    margin-top: 8px;
    padding-top: 12px;
    font-weight: 600;
}

QGroupBox#paramsBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #1F2329;
}

QSplitter#httpSplitter::handle {
    background-color: #E5E6EB;
    height: 4px;
    margin: 4px 0;
}
"""
