import sys
import csv
import json
import yaml
import os
import argparse
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QProgressBar, QGroupBox,
    QSlider, QRadioButton, QCheckBox, QButtonGroup, QMessageBox,
    QLineEdit, QComboBox, QSplitter, QFileDialog, QDialog, 
    QMenuBar, QAction, QDesktopWidget, QCompleter, QScrollArea,
    QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # CSV file selection
        self.csv_label = QLabel("CSV File:")
        self.csv_path_edit = QLineEdit()
        self.csv_browse_button = QPushButton("Browse...")
        csv_layout = QHBoxLayout()
        csv_layout.addWidget(self.csv_path_edit)
        csv_layout.addWidget(self.csv_browse_button)
        
        # YAML file selection
        self.yaml_label = QLabel("YAML Task File:")
        self.yaml_path_edit = QLineEdit()
        self.yaml_browse_button = QPushButton("Browse...")
        yaml_layout = QHBoxLayout()
        yaml_layout.addWidget(self.yaml_path_edit)
        yaml_layout.addWidget(self.yaml_browse_button)
        
        # Output file selection
        self.output_label = QLabel("Output JSON File (leave empty for default):")
        self.output_path_edit = QLineEdit()
        self.output_browse_button = QPushButton("Browse...")
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(self.output_browse_button)
        
        # Buttons
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        
        # Add widgets to main layout
        layout.addWidget(self.csv_label)
        layout.addLayout(csv_layout)
        
        layout.addWidget(self.yaml_label)
        layout.addLayout(yaml_layout)
        
        layout.addWidget(self.output_label)
        layout.addLayout(output_layout)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Connect signals
        self.csv_browse_button.clicked.connect(lambda: self.browse_file(self.csv_path_edit, "CSV Files (*.csv)"))
        self.yaml_browse_button.clicked.connect(lambda: self.browse_file(self.yaml_path_edit, "YAML Files (*.yaml *.yml)"))
        self.output_browse_button.clicked.connect(lambda: self.browse_file(self.output_path_edit, "JSON Files (*.json)", save=True))
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
    def browse_file(self, line_edit, file_filter, save=False):
        if save:
            path, _ = QFileDialog.getSaveFileName(self, "Select File", "", file_filter)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)
        if path:
            line_edit.setText(path)
    
    def get_paths(self):
        output_path = self.output_path_edit.text()
        if not output_path:
            output_path = os.path.join(os.getcwd(), "annotations.json")
        return {
            'csv': self.csv_path_edit.text(),
            'yaml': self.yaml_path_edit.text(),
            'output': output_path
        }
    
    def set_paths(self, csv_path, yaml_path, output_path):
        self.csv_path_edit.setText(csv_path)
        self.yaml_path_edit.setText(yaml_path)
        self.output_path_edit.setText(output_path)

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        # Try to load the BIGR logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "bigr.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo_label)
        
        # App info
        info_label = QLabel("""
        <h2>Patient Report Annotator</h2>
        <p>Developed by the BIGR group</p>
        <p><a href="https://bigr.nl">https://bigr.nl</a></p>
        <p>License: MIT</p>
        <p>Version: 1.0</p>
        """)
        info_label.setOpenExternalLinks(True)
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)

class AnnotationApp(QMainWindow):
    def __init__(self, csv_path=None, yaml_path=None, output_path=None):
        super().__init__()
        self.setWindowTitle("Patient Report Annotator")
        self.current_index = 0
        self.data = []
        self.annotations = {}
        self.button_groups = {}
        self.output_path = output_path or ""
        self.suppress_save_warnings = False
        
        # Initialize paths
        self.csv_path = csv_path or ""
        self.yaml_path = yaml_path or ""
        
        # Setup UI
        self.init_ui()
        self.apply_styles()
        
        # If paths were provided via command line, try to initialize directly
        if csv_path and yaml_path:
            if self.validate_paths():
                self.initialize_application()
            else:
                QMessageBox.critical(self, "Error", "Invalid file paths provided via command line")
                self.show_settings_dialog(initial=True)
        else:
            # Show settings dialog if no paths were provided
            self.show_settings_dialog(initial=True)
    
    def init_ui(self):
        """Initialize all UI components."""
        self.showMaximized()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create a splitter instead of direct layout
        layout = QSplitter(Qt.Horizontal)
        
        # Left panel: Text display (monospace font)
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Courier New", 10))
        layout.addWidget(self.text_display)
        
        # Right panel: Controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(2, 2, 2, 2)  # Reduce margins
        right_layout.setSpacing(5)  # Reduce spacing between widgets
        
        # Task instructions (from YAML)
        self.instructions = QTextEdit()
        self.instructions.setReadOnly(True)
        self.instructions.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.instructions.setMaximumHeight(150)  # Set reasonable maximum
        self.instructions.setMinimumHeight(20)   # Set minimum height
        
        instructions_label = QLabel("<b>Task Instructions</b>")
        right_layout.addWidget(instructions_label)
        right_layout.addWidget(self.instructions, stretch=0)  # No stretch for instructions
        
        # Navigation buttons
        nav_group = QGroupBox("Navigation")
        nav_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(5, 5, 5, 5)
        self.prev_button = QPushButton("⏮ Prev")
        self.next_button = QPushButton("Next ⏭")
        self.save_button = QPushButton("💾 Save")
        
        # Make buttons more compact
        for btn in [self.prev_button, self.next_button, self.save_button]:
            btn.setMinimumHeight(32)
            btn.setMaximumHeight(35)
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addWidget(self.save_button)
        nav_group.setLayout(nav_layout)
        right_layout.addWidget(nav_group, stretch=0)  # No stretch for navigation
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(20)
        right_layout.addWidget(self.progress_bar, stretch=0)
        
        # Create a container for the fixed title and scrollable content
        annotation_container = QWidget()
        annotation_layout = QVBoxLayout(annotation_container)
        annotation_layout.setContentsMargins(0, 0, 0, 0)
        annotation_layout.setSpacing(0)
        
        # Fixed title (outside scroll area)
        self.annotation_title = QLabel("<b>Annotations</b>")
        annotation_layout.addWidget(self.annotation_title, stretch=0)
        
        # Scroll area for just the annotation controls
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Annotation controls container
        self.annotation_content = QWidget()
        self.annotation_layout = QVBoxLayout(self.annotation_content)
        self.annotation_layout.setContentsMargins(5, 5, 5, 5)
        self.annotation_layout.setSpacing(5)
        self.annotation_layout.setAlignment(Qt.AlignTop)
        
        # Set up the scroll area
        scroll_area.setWidget(self.annotation_content)
        annotation_layout.addWidget(scroll_area, stretch=1)
        
        right_layout.addWidget(annotation_container, stretch=1)
        
        layout.addWidget(right_panel)
        layout.setSizes([700, 300])

        # Set the splitter as the main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(layout)

        # Signals
        self.prev_button.clicked.connect(self.prev_entry)
        self.next_button.clicked.connect(self.next_entry)
        self.save_button.clicked.connect(self.save_and_next)
        
    def create_menu_bar(self):
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(lambda: self.show_settings_dialog(initial=False))
        file_menu.addAction(settings_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def show_settings_dialog(self, initial=False):
        dialog = SettingsDialog(self)
        if not initial:
            dialog.set_paths(self.csv_path, self.yaml_path, self.output_path)
        
        if dialog.exec_() == QDialog.Accepted:
            paths = dialog.get_paths()
            self.csv_path = paths['csv']
            self.yaml_path = paths['yaml']
            self.output_path = paths['output']
            
            if self.validate_paths():
                self.initialize_application()
            else:
                if not initial:
                    QMessageBox.warning(self, "Warning", "Invalid file paths. Please check the files and try again.")
                else:
                    # If initial setup fails, close the app
                    self.close()
    
    def validate_paths(self):
        return all(os.path.exists(path) for path in [self.csv_path, self.yaml_path]) and self.output_path
    
    def initialize_application(self):
        """Initialize the application with the selected files"""
        try:
            self.task_config = self.load_task_config(self.yaml_path)
            self.instructions.setPlainText(self.task_config.get("instructions", "No instructions provided."))
            self.annotation_title.setText(f'<b>{self.task_config.get("name", "Annotations")}<b>')
            
            if os.path.exists(self.output_path):
                try:
                    with open(self.output_path, 'r') as f:
                        self.annotations = json.load(f)
                except:
                    QMessageBox.warning(self, "Warning", "Could not load existing annotations file. Starting fresh.")

            self.load_data(self.csv_path)
            self.build_annotation_ui()
            self.update_progress()
            self.find_first_unannotated()
            self.update_ui()
            
            # Enable UI elements now that we have valid files
            self.set_ui_enabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to initialize application: {str(e)}")
            self.set_ui_enabled(False)
    
    def set_ui_enabled(self, enabled):
        """Enable or disable UI elements"""
        self.text_display.setEnabled(enabled)
        self.prev_button.setEnabled(enabled)
        self.next_button.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.annotation_title.setEnabled(enabled)

    def load_settings(self):
        """Load user preferences from a settings file"""
        settings_file = os.path.join(os.path.dirname(self.output_path), 'annotator_settings.json')
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.suppress_save_warnings = settings.get('suppress_save_warnings', False)
            except:
                pass  # If loading fails, use defaults

    def save_settings(self):
        """Save user preferences to a settings file"""
        settings_file = os.path.join(os.path.dirname(self.output_path), 'annotator_settings.json')
        try:
            with open(settings_file, 'w') as f:
                json.dump({
                    'suppress_save_warnings': self.suppress_save_warnings
                }, f)
        except:
            pass  # If saving fails, continue silently

    def find_first_unannotated(self):
        """Find the first unannotated entry"""
        for i, entry in enumerate(self.data):
            if entry["Report-ID"] not in self.annotations:
                self.current_index = i
                self.update_ui()
                return
        self.current_index = len(self.data) - 1
        self.update_ui()
    
    def update_progress(self):
        """Update progress bar based on annotations"""
        annotated_count = sum(1 for entry in self.data 
                            if entry["Report-ID"] in self.annotations)
        self.progress_bar.setMaximum(len(self.data))
        self.progress_bar.setValue(annotated_count)
    
    def load_task_config(self, yaml_path):
        """Load and validate YAML task file."""
        try:
            with open(yaml_path, 'r') as f:
                config = yaml.safe_load(f)
                if "groups" not in config:
                    raise ValueError("YAML must contain 'groups' key.")
                return config
        except Exception as e:
            raise ValueError(f"Invalid YAML: {str(e)}")
    
    def load_data(self, csv_path):
        """Load and validate CSV data."""
        try:
            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if not {"Patient-ID", "Report-ID", "Text"}.issubset(reader.fieldnames):
                    raise ValueError("CSV must include columns: Patient-ID, Report-ID, Text")
                self.data = list(reader)
        except Exception as e:
            raise ValueError(f"Invalid CSV: {str(e)}")
    
    def build_annotation_ui(self):
        """Recursively build UI from YAML groups with control tracking."""
        self.controls = {}
        self.button_groups = {}
        self.required_controls = []

        # Clear existing annotation widgets
        for i in reversed(range(self.annotation_layout.count())): 
            widget = self.annotation_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        def add_controls(parent_layout, items):
            for item in items:
                if "controls" in item:  # Group
                    group = QGroupBox(item["label"])
                    sub_layout = QVBoxLayout()
                    add_controls(sub_layout, item["controls"])
                    group.setLayout(sub_layout)
                    parent_layout.addWidget(group)
                elif "groups" in item:  # Nested Group
                    add_controls(parent_layout, item["groups"])
                else:  # Control
                    label = item["label"]
                    parent_layout.addWidget(QLabel(label))
                    
                    if item["type"] == "slider":
                        slider = QSlider(Qt.Horizontal)
                        slider.setRange(item["min"], item["max"])
                        slider.setValue(item["min"])  # Set default to min
                        parent_layout.addWidget(slider)
                        self.controls[label] = slider
                        if item.get("required", False):
                            self.required_controls.append(slider)
                            
                    elif item["type"] == "radio":
                        group = QButtonGroup()
                        self.button_groups[label] = group
                        for option in item["options"]:
                            radio = QRadioButton(option)
                            parent_layout.addWidget(radio)
                            group.addButton(radio)
                        self.controls[label] = group
                        if item.get("required", False):
                            self.required_controls.append(group)
                            
                    elif item["type"] == "checkbox":
                        checkbox = QCheckBox(label)
                        parent_layout.addWidget(checkbox)
                        self.controls[label] = checkbox
                        if item.get("required", False):
                            self.required_controls.append(checkbox)
                    
                    elif item["type"] == "text":
                        text_field = QLineEdit()
                        text_field.setPlaceholderText(item.get("placeholder", ""))
                        if "default" in item:
                            text_field.setText(item["default"])
                        parent_layout.addWidget(text_field)
                        self.controls[label] = text_field
                        if item.get("required", False):
                            self.required_controls.append(text_field)
                    
                    elif item["type"] == "dropdown":
                        combo = QComboBox()
                        combo.addItems(item["options"])
                        if "default" in item and item["default"] in item["options"]:
                            combo.setCurrentText(item["default"])
                        parent_layout.addWidget(combo)
                        self.controls[label] = combo
                        if item.get("required", False):
                            self.required_controls.append(combo)

                    elif item["type"] == "autocomplete":
                        text_field = QLineEdit()
                        text_field.setPlaceholderText(item.get("placeholder", "Start typing..."))
                        
                        # Create completer with options
                        completer = QCompleter(item["options"])
                        completer.setCaseSensitivity(Qt.CaseInsensitive)
                        completer.setFilterMode(Qt.MatchContains)  # Match anywhere in string
                        completer.setCompletionMode(QCompleter.PopupCompletion)
                        text_field.setCompleter(completer)
                        
                        if "default" in item:
                            text_field.setText(item["default"])
                        
                        parent_layout.addWidget(text_field)
                        self.controls[label] = text_field
                        if item.get("required", False):
                            self.required_controls.append(text_field)

        add_controls(self.annotation_layout, self.task_config["groups"])

    def update_ui(self):
        """Update text display and progress."""
        if not self.data:
            return
        
        entry = self.data[self.current_index]
        # Preserve whitespace and formatting
        self.text_display.setPlainText(
            f"=== Report {entry['Report-ID']} for Patient {entry['Patient-ID']} ===\n\n"
            f"{entry['Text']}"
        )

        # Load existing annotations if present
        if entry["Report-ID"] in self.annotations:
            self.load_annotations(entry["Report-ID"])

    def load_annotations(self, report_id):
        """Load existing annotations for a report into the UI."""
        if report_id not in self.annotations:
            return
            
        annotations = self.annotations[report_id].get("annotations", {})
        
        for label, value in annotations.items():
            if label in self.controls:
                control = self.controls[label]
                
                if isinstance(control, QSlider):
                    control.setValue(value)
                elif isinstance(control, QButtonGroup):
                    for button in control.buttons():
                        if button.text() == value:
                            button.setChecked(True)
                            break
                elif isinstance(control, QCheckBox):
                    control.setChecked(value)

    def save_and_next(self):
        """Save current annotations and move to next unannotated entry."""
        if not self.validate_annotations():
            if not self.suppress_save_warnings:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Please complete all required fields")
                msg.setWindowTitle("Incomplete Annotation")
                
                # Add checkbox to suppress future warnings
                cb = QCheckBox("Don't show this message again")
                msg.setCheckBox(cb)
                msg.exec_()
                
                if cb.isChecked():
                    self.suppress_save_warnings = True
                    self.save_settings()
            return
            
        if self.save_annotations():
            self.next_entry(skip_annotated=True)
            if not self.suppress_save_warnings:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("Annotations saved successfully!")
                msg.setWindowTitle("Saved")
                
                # Add checkbox to suppress future warnings
                cb = QCheckBox("Don't show this message again")
                msg.setCheckBox(cb)
                msg.exec_()
                
                if cb.isChecked():
                    self.suppress_save_warnings = True
                    self.save_settings()

    
    def prev_entry(self):
        """Move to previous entry and load its annotations if they exist."""
        if self.current_index <= 0:
            return
            
        self.current_index -= 1
        self.clear_controls()
        self.update_ui()

    def next_entry(self, skip_annotated=False):
        """Move to next entry, optionally skipping annotated ones."""
        start_index = self.current_index
        while True:
            if self.current_index >= len(self.data) - 1:
                QMessageBox.information(self, "Complete", "All reports have been annotated!")
                break
                
            self.current_index += 1
            if not skip_annotated or self.data[self.current_index]["Report-ID"] not in self.annotations:
                self.clear_controls()
                self.update_ui()
                break
                
            # Prevent infinite loop if all remaining are annotated
            if self.current_index == start_index:
                break
    
    def validate_annotations(self):
        """Check if all required fields are filled"""
        for control in self.required_controls:
            if isinstance(control, QSlider):
                if control.value() == control.minimum():  # Assuming default is min
                    return False
            elif isinstance(control, QButtonGroup):
                if not control.checkedButton():
                    return False
            elif isinstance(control, QCheckBox):
                if not control.isChecked():
                    return False
            elif isinstance(control, QLineEdit):  # Text field validation
                if not control.text().strip():
                    return False
            elif isinstance(control, QComboBox):  # Dropdown validation
                if not control.currentText():
                    return False
        return True
        
    def collect_annotation_data(self):
        """Gather all control values"""
        data = {}
        for label, control in self.controls.items():
            if isinstance(control, QSlider):
                data[label] = control.value()
            elif isinstance(control, QButtonGroup):
                checked = control.checkedButton()
                data[label] = checked.text() if checked else None
            elif isinstance(control, QCheckBox):
                data[label] = control.isChecked()
            elif isinstance(control, QLineEdit):  # Text field
                data[label] = control.text()
            elif isinstance(control, QComboBox):  # Dropdown
                data[label] = control.currentText()
        return data

    def clear_controls(self):
        """Reset all input controls to default values"""
        for label, control in self.controls.items():
            if isinstance(control, QSlider):
                control.setValue(control.minimum())
            elif isinstance(control, QButtonGroup):
                control.setExclusive(False)
                for button in control.buttons():
                    button.setChecked(False)
                control.setExclusive(True)
            elif isinstance(control, QCheckBox):
                control.setChecked(False)
            elif isinstance(control, QLineEdit):  # Text field
                # Reset to default if specified in YAML, else empty
                default = next((item.get("default", "") for item in self.find_control_config(label) if "default" in item), "")
                control.setText(default)
            elif isinstance(control, QComboBox):  # Dropdown
                # Reset to default if specified in YAML, else first item
                config = next((item for item in self.find_control_config(label)), {})
                if "default" in config and config["default"] in [control.itemText(i) for i in range(control.count())]:
                    control.setCurrentText(config["default"])
                else:
                    control.setCurrentIndex(0)

    def find_control_config(self, label):
        """Helper to find control config by label"""
        def search_items(items):
            for item in items:
                if "controls" in item:
                    for control in item["controls"]:
                        if control.get("label") == label:
                            yield control
                elif "groups" in item:
                    yield from search_items(item["groups"])
        
        return list(search_items(self.task_config["groups"]))

    def save_annotations(self):
        """Save current annotations with validation."""
        entry = self.data[self.current_index]
        self.annotations[entry["Report-ID"]] = {
            "Patient-ID": entry["Patient-ID"],
            "annotations": self.collect_annotation_data()
        }
        
        try:
            with open(self.output_path, 'w') as f:
                json.dump(self.annotations, f, indent=2)
            self.update_progress()
            return True
        except Exception as e:
            if not self.suppress_save_warnings:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText(f"Failed to save: {str(e)}")
                msg.setWindowTitle("Error")
                
                cb = QCheckBox("Don't show this message again")
                msg.setCheckBox(cb)
                msg.exec_()
                
                if cb.isChecked():
                    self.suppress_save_warnings = True
                    self.save_settings()
            return False
    
    def apply_styles(self):
        """Apply QSS styling for a modern look."""
        self.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QSplitter::handle { 
                background-color: #ccc;
            }
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 3px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                padding: 5px;
                font-family: Courier New;
            }
        """)

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Patient Report Annotator')
    parser.add_argument('--csv', help='Path to CSV file')
    parser.add_argument('--yaml', help='Path to YAML task file')
    parser.add_argument('--output', help='Path to output JSON file')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    # Create application window with or without command line arguments
    window = AnnotationApp(csv_path=args.csv, yaml_path=args.yaml, output_path=args.output)
    
    # Center the window on screen
    qt_rectangle = window.frameGeometry()
    center_point = QDesktopWidget().availableGeometry().center()
    qt_rectangle.moveCenter(center_point)
    window.move(qt_rectangle.topLeft())
    
    window.show()
    sys.exit(app.exec_())