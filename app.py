import sys
import csv
import json
import yaml
import os
import argparse
import datetime
from dateutil import parser as dateparser
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QProgressBar, QGroupBox,
    QSlider, QRadioButton, QCheckBox, QButtonGroup, QMessageBox,
    QLineEdit, QComboBox, QSplitter, QFileDialog, QDialog, 
    QAction, QDesktopWidget, QCompleter, QScrollArea,
    QSizePolicy, QFrame, QDateEdit, QGridLayout, QToolButton,
    QProgressDialog
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal, QEventLoop
from PyQt5.QtGui import QFont, QPixmap

class QHLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setStyleSheet("color: #ccc;")

class UMLSMapperLoader(QThread):
    finished = pyqtSignal(object)

    def run(self):
        import spacy
        from scispacy.linking import EntityLinker
        nlp = spacy.blank("en")
        nlp.add_pipe("scispacy_linker", config={
            "resolve_abbreviations": True,
            "linker_name": "umls"
        })
        self.finished.emit(nlp)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Annotator Name Field
        self.annotator_label = QLabel("Annotator Name (optional):")
        self.annotator_name = QLineEdit()
        self.annotator_name.setPlaceholderText("Enter your name")
        layout.addWidget(self.annotator_label)
        layout.addWidget(self.annotator_name)
        
        # Patient Reports View Option
        self.group_reports_check = QCheckBox("Show all reports for a patient at once")
        self.group_reports_check.setChecked(False)  # Default unchecked
        layout.addWidget(self.group_reports_check)
        
        # Add separator
        layout.addWidget(QLabel("File Paths:"))
        layout.addWidget(QHLine())
        
        # CSV file selection
        self.csv_label = QLabel("CSV File:")
        self.csv_path_edit = QLineEdit()
        self.csv_browse_button = QPushButton("Browse...")
        csv_layout = QHBoxLayout()
        csv_layout.addWidget(self.csv_path_edit)
        csv_layout.addWidget(self.csv_browse_button)

        ## CSV header configuration
        self.header_label = QLabel("Columns:")
        header_layout = QGridLayout()
        header_layout.setColumnStretch(1, 1)
        
        self.patient_id_label = QLabel("Patient Unique Identifiers:")
        self.patient_id_field = QLineEdit()
        self.patient_id_field.setText("Patient-ID")
        header_layout.addWidget(self.patient_id_label, 0, 0)
        header_layout.addWidget(self.patient_id_field, 0, 1)
        
        self.report_id_label = QLabel("Report Unique Identifiers:")
        self.report_id_field = QLineEdit()
        self.report_id_field.setText("Report-ID")
        header_layout.addWidget(self.report_id_label, 1, 0)
        header_layout.addWidget(self.report_id_field, 1, 1)
        
        self.report_date_label = QLabel("Report Dates:")
        self.report_date_field = QLineEdit()
        self.report_date_field.setText("Report-Date")
        header_layout.addWidget(self.report_date_label, 2, 0)
        header_layout.addWidget(self.report_date_field, 2, 1)
        
        self.text_label = QLabel("Report Free Text:")
        self.text_field = QLineEdit()
        self.text_field.setText("Text")
        header_layout.addWidget(self.text_label, 3, 0)
        header_layout.addWidget(self.text_field, 3, 1)
        
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
        layout.addWidget(self.header_label)
        layout.addLayout(header_layout)
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
    
    def get_settings(self):
        """Return all settings as a dictionary."""
        output_path = self.output_path_edit.text()
        if not output_path:
            output_path = os.path.join(os.getcwd(), "annotations.json")
            
        return {
            'annotator_name': self.annotator_name.text().strip(),
            'group_patient_reports': self.group_reports_check.isChecked(),
            'csv': self.csv_path_edit.text(),
            'yaml': self.yaml_path_edit.text(),
            'output': output_path,
            'headers': {
                'patient_id': self.patient_id_field.text().strip(),
                'report_id': self.report_id_field.text().strip(),
                'report_date': self.report_date_field.text().strip(),
                'text': self.text_field.text().strip()
            }
        }
    
    def set_settings(self, settings):
        """Set all settings from a dictionary."""
        self.annotator_name.setText(settings.get('annotator_name', ''))
        self.group_reports_check.setChecked(settings.get('group_patient_reports', False))
        self.csv_path_edit.setText(settings.get('csv', ''))
        self.yaml_path_edit.setText(settings.get('yaml', ''))
        self.output_path_edit.setText(settings.get('output', ''))
        
        # Set header fields
        headers = settings.get('headers', {})
        self.patient_id_field.setText(headers.get('patient_id', 'Patient-ID'))
        self.report_id_field.setText(headers.get('report_id', 'Report-ID'))
        self.report_date_field.setText(headers.get('report_date', 'Report-Date'))
        self.text_field.setText(headers.get('text', 'Text'))
    
    def browse_file(self, line_edit, file_filter, save=False):
        if save:
            path, _ = QFileDialog.getSaveFileName(self, "Select File", "", file_filter)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)
        if path:
            line_edit.setText(path)

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
        self.group_patient_reports = False
        self.current_annotator_name = "Unnamed"
        self.all_annotations = []  # Stores all annotations in flat list
        self.current_report_annotations = {}  # Current annotator's annotations for the report

        # Initialize settings with defaults
        self.settings = {
            'headers': {
                'patient_id': 'Patient-ID',
                'report_id': 'Report-ID',
                'report_date': 'Report-Date',
                'text': 'Text'
            },
            'suppress_save_warnings': False
        }
        
        # Initialize paths
        self.csv_path = csv_path or ""
        self.yaml_path = yaml_path or ""
        
        # Setup UI
        self.init_ui()
        self.apply_styles()
        
        # If paths were provided via command line, try to initialize directly
        if csv_path and yaml_path:
            if self.validate_paths(csv_path, yaml_path, output_path):
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

        # Add new Save to CSV action
        save_csv_action = QAction("Save to CSV", self)
        save_csv_action.triggered.connect(self.save_annotations_to_csv)
        file_menu.addAction(save_csv_action)
            
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
            dialog.set_settings({
                'annotator_name': self.current_annotator_name,
                'group_patient_reports': self.group_patient_reports,
                'csv': self.csv_path,
                'yaml': self.yaml_path,
                'output': self.output_path,
                'headers': self.settings.get('headers', {
                    'patient_id': 'Patient-ID',
                    'report_id': 'Report-ID',
                    'report_date': 'Report-Date',
                    'text': 'Text'
                })
            })
        
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()

            # Only proceed if paths are valid
            if not self.validate_paths(settings['csv'], settings['yaml'], settings['output']):
                QMessageBox.warning(self, "Warning", "Invalid file paths. Please check the files and try again.")
                return
            
            # Save current work before changing anything
            if self.current_report_annotations:
                self.save_annotations()
                
            # Update paths and settings
            self.csv_path = settings['csv']
            self.yaml_path = settings['yaml']
            self.output_path = settings['output']
            self.current_annotator_name = settings['annotator_name']
            self.group_patient_reports = settings['group_patient_reports']
            
            # Update headers in settings
            self.settings['headers'] = settings['headers']
            
            # Save the settings to disk
            self.save_settings()
            
            # Reload data with new settings
            try:
                self.initialize_application()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reload data: {str(e)}")
    
    def validate_paths(self, csv_path, yaml_path, output_path):
        """Validate all file paths."""
        return all(os.path.exists(p) for p in [csv_path, yaml_path]) and output_path
        
    def initialize_application(self):
        """Initialize the application with the selected files"""
        try:
            # Load settings first
            settings = self.load_settings()
            if settings:
                self.settings.update(settings)
            
            self.task_config = self.load_task_config(self.yaml_path)
            self.instructions.setPlainText(self.task_config.get("instructions", "No instructions provided."))
            self.annotation_title.setText(f'<b>{self.task_config.get("name", "Annotations")}<b>')
            
            # Load existing annotations
            self.load_annotations()

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
        if not self.output_path:
            return None
            
        settings_file = os.path.join(os.path.dirname(self.output_path), 'annotator_settings.json')
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load settings: {str(e)}")
                return None
        return None
    
    def save_settings(self):
        """Save user preferences to a settings file"""
        if not self.output_path:
            return
            
        settings_file = os.path.join(os.path.dirname(self.output_path), 'annotator_settings.json')
        try:
            with open(settings_file, 'w') as f:
                json.dump({
                    'suppress_save_warnings': self.suppress_save_warnings,
                    'headers': self.settings['headers']
                }, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {str(e)}")

    def find_first_unannotated(self):
        """Find the first unannotated entry for current annotator."""
        for i, entry in enumerate(self.data):
            report_id = entry["Report-ID"]
            # Check if current annotator has annotated this report
            has_annotation = any(
                a["report_id"] == report_id and 
                a["annotator"] == self.current_annotator_name
                for a in self.all_annotations
            )
            if not has_annotation:
                self.current_index = i
                self.update_ui()
                return
        self.current_index = len(self.data) - 1
        self.update_ui()
    
    def update_progress(self):
        """Update progress bar considering current mode."""
        if not self.current_annotator_name or not self.data:
            return
            
        # Get all annotations for current annotator
        annotator_annotations = {
            a["report_id"]: a for a in self.all_annotations 
            if a["annotator"] == self.current_annotator_name
        }
        
        if self.group_patient_reports:
            # Group mode - count completed patients
            patient_status = {}
            for entry in self.data:
                patient_id = entry["Patient-ID"]
                report_id = entry["Report-ID"]
                
                if patient_id not in patient_status:
                    patient_status[patient_id] = True
                
                if report_id not in annotator_annotations:
                    patient_status[patient_id] = False
            
            completed_patients = sum(1 for status in patient_status.values() if status)
            total_patients = len(patient_status)
            
            self.progress_bar.setMaximum(total_patients)
            self.progress_bar.setValue(completed_patients)
        else:
            # Single report mode
            annotated_count = len(annotator_annotations)
            total_count = len(self.data)
            
            self.progress_bar.setMaximum(total_count)
            self.progress_bar.setValue(annotated_count)
        
        # Update status bar
        mode = "All Patient Reports" if self.group_patient_reports else "Single Report"
        self.statusBar().showMessage(
            f"Annotator: {self.current_annotator_name or 'Unnamed'} | "
            f"Progress: {self.progress_bar.value()}/{self.progress_bar.maximum()} | "
            f"Mode: {mode}"
        )
    
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
        """Load and validate CSV data, parsing dates."""
        try:
            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                
                # Get header names from settings
                headers = self.settings.get('headers', {
                    'patient_id': 'Patient-ID',
                    'report_id': 'Report-ID',
                    'report_date': 'Report-Date',
                    'text': 'Text'
                })
                
                # Verify required columns exist
                required_columns = {
                    headers['patient_id'],
                    headers['report_id'],
                    headers['report_date'],
                    headers['text']
                }
                
                if not required_columns.issubset(reader.fieldnames):
                    raise ValueError(
                        f"CSV must include columns matching: {', '.join(required_columns)}. "
                        f"Found columns: {', '.join(reader.fieldnames)}"
                    )
                
                self.data = []
                for row in reader:
                    try:
                        # Store the original row data
                        processed_row = dict(row)
                        
                        # Add standard field names to the row for internal use
                        processed_row["Patient-ID"] = row[headers['patient_id']]
                        processed_row["Report-ID"] = row[headers['report_id']]
                        processed_row["Report-Date"] = row[headers['report_date']]
                        processed_row["Text"] = row[headers['text']]
                        
                        # Convert date string to datetime object for sorting
                        processed_row["_parsed_date"] = dateparser.parse(processed_row["Report-Date"])
                        
                        self.data.append(processed_row)
                    except ValueError:
                        processed_row["_parsed_date"] = datetime.datetime.min
                        self.data.append(processed_row)
                
                # Sort all data by patient then date
                self.data.sort(key=lambda x: (x["Patient-ID"], x["_parsed_date"]))
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

        self.add_controls(self.annotation_layout, self.task_config["groups"])

    def add_controls(self, parent_layout, items):
        for item in items:
            if "controls" in item:  # Group
                if item.get("collapsible", False):
                    # Create collapsible group
                    group = self.create_collapsible_group(item)
                    parent_layout.addWidget(group)
                else:
                    # Regular group
                    group = QGroupBox(item["label"])
                    sub_layout = QVBoxLayout()
                    self.add_controls(sub_layout, item["controls"])
                    group.setLayout(sub_layout)
                    parent_layout.addWidget(group)
            elif "groups" in item:  # Nested Group
                self.add_controls(parent_layout, item["groups"])
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

                elif item["type"] == "text" and item.get("mapper", False):
                    # Create mapper control layout
                    mapper_layout = QHBoxLayout()
                    
                    # Text field
                    text_field = QLineEdit()
                    text_field.setPlaceholderText(item.get("placeholder", ""))
                    if "default" in item:
                        text_field.setText(item["default"])
                    mapper_layout.addWidget(text_field, stretch=2)
                    
                    # Update button
                    update_button = QPushButton("🔍")
                    update_button.setToolTip("Search UMLS")
                    update_button.setFixedWidth(30)
                    mapper_layout.addWidget(update_button)
                    
                    # Dropdown for UMLS results
                    umls_dropdown = QComboBox()
                    umls_dropdown.setFixedWidth(250)
                    mapper_layout.addWidget(umls_dropdown, stretch=1)
                    
                    # Checkbox for match confirmation
                    match_checkbox = QCheckBox("Match?")
                    match_checkbox.setEnabled(False)
                    mapper_layout.addWidget(match_checkbox)
                    
                    # Store references
                    self.controls[label] = {
                        'text': text_field,
                        'dropdown': umls_dropdown,
                        'update': update_button,
                        'match_checkbox': match_checkbox
                    }
                    
                    # Connect signals
                    update_button.clicked.connect(
                        lambda _, t=text_field, d=umls_dropdown, c=match_checkbox: 
                        self.search_umls(t.text(), d, c))
                    
                    parent_layout.addLayout(mapper_layout)
                elif item["type"] == "text":
                    text_field = QLineEdit()
                    text_field.setPlaceholderText(item.get("placeholder", ""))
                    if "default" in item:
                        text_field.setText(item["default"])
                    parent_layout.addWidget(text_field)
                    self.controls[label] = text_field
                    if item.get("required", False):
                        self.required_controls.append(text_field)
                
                elif item["type"] == "date":
                    date_field = QDateEdit()
                    date_field.setDisplayFormat("dd-MM-yyyy")
                    date_field.setCalendarPopup(True)
                    date_field.setDate(QDate(2000, 1, 1))
                    parent_layout.addWidget(date_field)
                    self.controls[label] = date_field
                    if item.get("required", False):
                        self.required_controls.append(date_field)

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

    def search_umls(self, text, dropdown, match_checkbox):
        """Search UMLS for the given text and populate dropdown with results."""
        try:
            if not hasattr(self, 'nlp'):
                # Initialize UMLS linker
                loading_dialog = QProgressDialog("Downloading UMLS linker, this takes some time, please wait...", None, 0, 0, self)
                loading_dialog.setCancelButton(None)
                loading_dialog.setWindowModality(Qt.WindowModal)
                loading_dialog.setWindowTitle("Loading")
                loading_dialog.show()
                QApplication.processEvents()

                loop = QEventLoop()
                nlp_container = {}

                # Load the NLP model in a separate thread to avoid blocking the UI
                def on_finished(nlp):
                    nlp_container['nlp'] = nlp
                    loop.quit()

                loader = UMLSMapperLoader()
                loader.finished.connect(on_finished)
                loader.start()

                loop.exec_()

                loading_dialog.close()
                self.nlp = nlp_container['nlp']
                
            # Clear previous results
            dropdown.clear()
            match_checkbox.setEnabled(False)
            match_checkbox.setChecked(False)
            
            if not isinstance(text, str) or not text.strip():
                dropdown.addItem("No text entered")
                return
            
            QApplication.processEvents()
            
            # Create a Doc object from the full string
            doc = self.nlp(text)
            
            # Force a single-span entity over the entire string
            span = doc.char_span(0, len(text), label="ENTITY")
            if span is None:
                dropdown.addItem("No match found")
                return
            
            doc.ents = [span]
            
            # Run the linker
            linker = self.nlp.get_pipe("scispacy_linker")
            doc = linker(doc)
            
            ent = doc.ents[0]
            if not ent._.kb_ents:
                dropdown.addItem("No match found")
                return
            
            # Get top 10 matches
            for concept_id, score in ent._.kb_ents[:10]:
                concept = linker.kb.cui_to_entity[concept_id]
                display_text = f"{concept.canonical_name} (Score: {score:.2f}, CUI: {concept_id})"
                dropdown.addItem(display_text, {
                    'cui': concept_id,
                    'canonical_name': concept.canonical_name,
                    'score': score,
                    'types': concept.types
                })
            
            if dropdown.count() > 0:
                match_checkbox.setEnabled(True)
            
        except Exception as e:
            QMessageBox.warning(self, "UMLS Error", f"Failed to search UMLS: {str(e)}")

    def confirm_umls_selection(self, text_field, dropdown):
        """Handle confirmation of UMLS selection."""
        if dropdown.currentIndex() >= 0:
            concept_id, canonical_name, score = dropdown.currentData()
            text_field.setText(canonical_name)

    def create_collapsible_group(self, group_config):
        """Create a collapsible group box with toggle button on the right."""
        # Create a standard QGroupBox
        group = QGroupBox()
        
        # Main layout for the group
        main_layout = QVBoxLayout(group)
        
        # Header widget (for the title and toggle button)
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title label
        title_label = QLabel(f"<b>{group_config['label']}</b>")
        
        # Toggle button (styled like a QToolButton)
        toggle_button = QToolButton()
        toggle_button.setStyleSheet("QToolButton { border: none; }")
        toggle_button.setArrowType(Qt.DownArrow if group_config.get("initially_expanded", True) else Qt.RightArrow)
        toggle_button.setFixedSize(16, 16)
        
        # Add widgets to header
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(toggle_button)
        
        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(5, 5, 5, 5)
        self.add_controls(content_layout, group_config["controls"])
        
        # Add to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(content)
        
        # Set initial state
        content.setVisible(group_config.get("initially_expanded", True))
        
        # Connect toggle button
        def toggle_content():
            is_visible = not content.isVisible()
            content.setVisible(is_visible)
            toggle_button.setArrowType(Qt.DownArrow if is_visible else Qt.RightArrow)
        
        toggle_button.clicked.connect(toggle_content)
        
        return group
        
    def update_ui(self):
        """Update text display to show single or grouped reports."""
        if not self.data:
            return
        
        current_entry = self.data[self.current_index]
        patient_id = current_entry["Patient-ID"]

        if self.group_patient_reports:
            # Get all reports for current patient
            patient_reports = [r for r in self.data if r["Patient-ID"] == patient_id]
            report_texts = []
            
            for report in patient_reports:
                report_texts.append(
                    f"=== Report {report['Report-ID']} ({report['Report-Date']}) ===\n\n"
                    f"{report['Text']}\n\n"
                )
            
            self.text_display.setPlainText("\n".join(report_texts))
            self.current_patient_reports = patient_reports
        else:
            # Single report mode
            self.text_display.setPlainText(
                f"=== Report {current_entry['Report-ID']} ({current_entry['Report-Date']}) ===\n\n"
                f"{current_entry['Text']}"
            )
            self.current_patient_reports = [current_entry]
        
        # Load annotations for current view
        self.load_annotations_for_current_view()

    def load_annotations(self):
        """Load existing annotations for a report into the UI."""
        self.all_annotations = []
        if os.path.exists(self.output_path):
            try:
                with open(self.output_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "annotations" in data:
                        self.all_annotations = data["annotations"]
                    elif isinstance(data, list):
                        self.all_annotations = data
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Could not load annotations: {str(e)}")
        
        # Initialize current report annotations
        self.current_report_annotations = {}

    def load_annotation_values(self):
        """Load annotation values into UI controls."""
        if not self.current_patient_reports:
            return
        
        # For single report mode
        if not self.group_patient_reports:
            report_id = self.current_patient_reports[0]["Report-ID"]
            annotations = self.current_report_annotations.get(report_id, {})
            
            for label, control in self.controls.items():
                if label in annotations:
                    value = annotations[label]
                    if isinstance(control, QSlider):
                        control.setValue(value)
                    elif isinstance(control, QButtonGroup):
                        for button in control.buttons():
                            if button.text() == value:
                                button.setChecked(True)
                                break
                    elif isinstance(control, QCheckBox):
                        control.setChecked(value)
                    elif isinstance(control, dict) and 'text' in control:
                        control['text'].setText(str(value.get("text", "")))
                        # Handle UMLS dropdown
                        ulms = value.get("umls_selection", {})
                        concept_id = ulms.get("cui", "")
                        canonical_name = ulms.get("canonical_name", "")
                        score = ulms.get("score", "")
                        types = ulms.get("types", [])

                        display_text = f"{canonical_name} (Score: {score:.2f}, CUI: {concept_id})"
                        control['dropdown'].addItem(display_text, {
                            'cui': concept_id,
                            'canonical_name': canonical_name,
                            'score': score,
                            'types': types
                        })
                        control['match_checkbox'].setChecked(value.get("match_checkbox", False))
                    elif isinstance(control, QLineEdit):
                        control.setText(str(value))
                    elif isinstance(control, QDateEdit):
                        control.setDate(QDate.fromString(value, "dd-MM-yyyy") if value else QDate(2000, 1, 1))
                    elif isinstance(control, QComboBox):
                        control.setCurrentText(str(value))
        
        # For group mode
        else:
            first_report_id = self.current_patient_reports[0]["Report-ID"]
            annotations = self.current_report_annotations.get(first_report_id, {})
            
            for label, control in self.controls.items():
                if label in annotations:
                    value = annotations[label]
                    if isinstance(control, QSlider):
                        control.setValue(value)
                    elif isinstance(control, QButtonGroup):
                        for button in control.buttons():
                            if button.text() == value:
                                button.setChecked(True)
                                break
                    elif isinstance(control, QCheckBox):
                        control.setChecked(value)
                    elif isinstance(control, dict) and 'text' in control:
                        control['text'].setText(str(value.get("text", "")))
                        # Handle UMLS dropdown
                        ulms = value.get("umls_selection", {})
                        concept_id = ulms.get("cui", "")
                        canonical_name = ulms.get("canonical_name", "")
                        score = ulms.get("score", "")
                        types = ulms.get("types", [])

                        display_text = f"{canonical_name} (Score: {score:.2f}, CUI: {concept_id})"
                        control['dropdown'].addItem(display_text, {
                            'cui': concept_id,
                            'canonical_name': canonical_name,
                            'score': score,
                            'types': types
                        })
                        control['match_checkbox'].setChecked(value.get("match_checkbox", False))
                    elif isinstance(control, QLineEdit):
                        control.setText(str(value))
                    elif isinstance(control, QDateEdit):
                        control.setDate(QDate.fromString(value, "dd-MM-yyyy"))
                    elif isinstance(control, QComboBox):
                        control.setCurrentText(str(value))

    def save_and_next(self):
        """Save current annotations and move to next unannotated entry."""
        if not self.validate_annotations():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Please complete all required fields")
            msg.setWindowTitle("Incomplete Annotation")
            msg.exec_()
            return
            
        self.current_report_annotations = self.collect_annotation_data()

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
    
    def next_entry(self, skip_annotated=False):
        """Move to next report or patient group."""
        if len(self.data) == 0:
            return
            
        if self.group_patient_reports:
            # Find next unannotated patient group
            current_patient = self.data[self.current_index]["Patient-ID"]
            for i in range(self.current_index + 1, len(self.data)):
                if self.data[i]["Patient-ID"] != current_patient:
                    # Check if we should skip fully annotated patients
                    if skip_annotated:
                        patient_reports = [r for r in self.data if r["Patient-ID"] == self.data[i]["Patient-ID"]]
                        all_annotated = all(
                            any(a["report_id"] == r["Report-ID"] for a in self.all_annotations 
                                if a["annotator"] == self.current_annotator_name)
                            for r in patient_reports
                        )
                        if all_annotated:
                            continue
                    
                    self.current_index = i
                    self.clear_controls()
                    self.update_ui()
                    return
        else:
            # Original single report behavior
            start_index = self.current_index
            while True:
                if self.current_index >= len(self.data) - 1:
                    QMessageBox.information(self, "Complete", "All reports have been annotated!")
                    break
                    
                self.current_index += 1
                if not skip_annotated or not any(
                    a["report_id"] == self.data[self.current_index]["Report-ID"] 
                    for a in self.all_annotations 
                    if a["annotator"] == self.current_annotator_name
                ):
                    self.clear_controls()
                    self.update_ui()
                    break
                    
                # Prevent infinite loop
                if self.current_index == start_index:
                    break

    def prev_entry(self):
        """Move to previous report or patient group."""
        if self.current_index <= 0:
            return
            
        if self.group_patient_reports:
            # Find previous patient group
            current_patient = self.data[self.current_index]["Patient-ID"]
            for i in range(self.current_index - 1, -1, -1):
                if self.data[i]["Patient-ID"] != current_patient:
                    self.current_index = i
                    self.clear_controls()
                    self.update_ui()
                    return
        else:
            # Original single report behavior
            self.current_index -= 1
            self.clear_controls()
            self.update_ui()
    
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
            elif isinstance(control, dict) and 'text' in control:
                if not control['text'].text().strip():
                    return False
                if not control['dropdown'].currentData():
                    return False
                if not control['match_checkbox'].isChecked():
                    return False
            elif isinstance(control, QLineEdit):  # Text field validation
                if not control.text().strip():
                    return False
            elif isinstance(control, QDateEdit):  # Date field validation
                if not control.date().isValid():
                    return False
            elif isinstance(control, QComboBox):  # Dropdown validation
                if not control.currentText():
                    return False
        return True
        
    def collect_annotation_data(self):
        """Gather all control values for current reports."""
        collected_data = {}
        
        if not self.group_patient_reports:
            # Single report mode - same as before
            report_id = self.current_patient_reports[0]["Report-ID"]
            report_data = {}
            for label, control in self.controls.items():
                if isinstance(control, QSlider):
                    report_data[label] = control.value()
                elif isinstance(control, QButtonGroup):
                    checked = control.checkedButton()
                    report_data[label] = checked.text() if checked else None
                elif isinstance(control, QCheckBox):
                    report_data[label] = control.isChecked()
                elif isinstance(control, dict) and 'text' in control:
                    report_data[label] = {
                        'text': control['text'].text(),
                        'umls_selection': control['dropdown'].currentData() if control['dropdown'].currentIndex() >= 0 else None,
                        'match_checkbox': control['match_checkbox'].isChecked()
                    }
                elif isinstance(control, QLineEdit):
                    report_data[label] = control.text()
                elif isinstance(control, QDateEdit):
                    report_data[label] = control.date().toString("dd-MM-yyyy") if not control.date().toString("dd-MM-yyyy") == "01-01-2000" else None
                elif isinstance(control, QComboBox):
                    report_data[label] = control.currentText()
            collected_data[report_id] = report_data
        else:
            # Group mode - collect current control values
            current_annotations = {}
            for label, control in self.controls.items():
                if isinstance(control, QSlider):
                    current_annotations[label] = control.value()
                elif isinstance(control, QButtonGroup):
                    checked = control.checkedButton()
                    current_annotations[label] = checked.text() if checked else None
                elif isinstance(control, QCheckBox):
                    current_annotations[label] = control.isChecked()
                elif isinstance(control, dict) and 'text' in control:
                    current_annotations[label] = {
                        'text': control['text'].text(),
                        'umls_selection': control['dropdown'].currentData() if control['dropdown'].currentIndex() >= 0 else None,
                        'match_checkbox': control['match_checkbox'].isChecked()
                    }
                elif isinstance(control, QLineEdit):
                    current_annotations[label] = control.text()
                elif isinstance(control, QDateEdit):
                    current_annotations[label] = control.date().toString("dd-MM-yyyy") if not control.date().toString("dd-MM-yyyy") == "01-01-2000" else None
                elif isinstance(control, QComboBox):
                    current_annotations[label] = control.currentText()
            
            # Create combined report ID string for display
            report_ids = [r["Report-ID"] for r in self.current_patient_reports]
            combined_id = " - ".join(report_ids)
            
            # Store same annotations for all reports but mark them as grouped
            for report in self.current_patient_reports:
                collected_data[report["Report-ID"]] = {
                    **current_annotations,
                    "_grouped_reports": combined_id  # Add this special field
                }
        
        return collected_data

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
            elif isinstance(control, dict) and 'text' in control:
                # Reset to default if specified in YAML, else empty
                default = next((item.get("default", "") for item in self.find_control_config(label) if "default" in item), "")
                control['text'].setText(default)
                control['dropdown'].clear()
                control['match_checkbox'].setChecked(False)
            elif isinstance(control, QLineEdit):  # Text field
                # Reset to default if specified in YAML, else empty
                default = next((item.get("default", "") for item in self.find_control_config(label) if "default" in item), "")
                control.setText(default)
            elif isinstance(control, QDateEdit):  # Date field
                control.setDate(QDate(2000, 1, 1))# Reset to 01-01-2000
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
        """Save annotations for current view."""
        try:
            new_annotations = self.collect_annotation_data()
            report_ids = list(new_annotations.keys())
            
            # Remove existing annotations for these reports
            updated_annotations = [
                a for a in self.all_annotations
                if not (a["report_id"] in report_ids and 
                    a["annotator"] == self.current_annotator_name)
            ]
            
            # Add new annotations
            for report_id, annotation_data in new_annotations.items():
                if annotation_data:
                    report = next((r for r in self.data if r["Report-ID"] == report_id), None)
                    if report:
                        # Create the annotation object
                        annotation_obj = {
                            "annotator": self.current_annotator_name,
                            "patient_id": report["Patient-ID"],
                            "report_id": report_id,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "annotation": annotation_data
                        }
                        
                        # If in group mode, add the combined ID to the main object
                        if self.group_patient_reports:
                            annotation_obj["combined_report_ids"] = annotation_data.get("_grouped_reports", "")
                            # Remove the internal field from the annotation data
                            if "_grouped_reports" in annotation_obj["annotation"]:
                                del annotation_obj["annotation"]["_grouped_reports"]
                        
                        updated_annotations.append(annotation_obj)
            
            self.all_annotations = updated_annotations
            
            with open(self.output_path, 'w') as f:
                json.dump({
                    "annotations": self.all_annotations,
                    "timestamp": datetime.datetime.now().isoformat()
                }, f, indent=2)
            
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
    
    def save_annotations_to_csv(self):
        """Save all annotations to a CSV file."""
        if not self.all_annotations:
            QMessageBox.warning(self, "Warning", "No annotations to save")
            return

        # Get output path from user
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Annotations as CSV",
            "",
            "CSV Files (*.csv)",
            options=options
        )

        if not file_path:
            return  # User cancelled

        try:
            if not file_path.endswith('.csv'):
                file_path += '.csv'
                
            # Collect all unique field names from annotations
            fieldnames = set()
            for annotation in self.all_annotations:
                fieldnames.update(annotation["annotation"].keys())
            
            # Standard fields we always include
            standard_fields = [
                "annotator",
                "patient_id",
                "report_id",
                "timestamp",
                "combined_report_ids"
            ]
            
            # Combine and order fields
            all_fields = standard_fields + sorted(f for f in fieldnames if f not in standard_fields)

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=all_fields)
                writer.writeheader()
                
                for annotation in self.all_annotations:
                    row = {
                        "annotator": annotation["annotator"],
                        "patient_id": annotation["patient_id"],
                        "report_id": annotation["report_id"],
                        "timestamp": annotation["timestamp"],
                        "combined_report_ids": annotation.get("combined_report_ids", "")
                    }
                    # Add all annotation fields
                    row.update(annotation["annotation"])
                    writer.writerow(row)

            QMessageBox.information(self, "Success", f"Annotations saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save CSV: {str(e)}")

    def load_annotations_for_current_view(self):
        """Load annotations for all reports in current view."""
        self.current_report_annotations = {}
        
        if not self.current_annotator_name:
            return
            
        for report in self.current_patient_reports:
            report_id = report["Report-ID"]
            
            # Find most recent annotation for this report+annotator
            matching_annotations = [
                a for a in self.all_annotations 
                if a["report_id"] == report_id and 
                a["annotator"] == self.current_annotator_name
            ]
            
            if matching_annotations:
                self.current_report_annotations[report_id] = matching_annotations[-1]["annotation"]
            else:
                # Initialize empty annotation
                self.current_report_annotations[report_id] = {}
        
        # Load values into UI controls
        self.load_annotation_values()

    def load_annotations_for_report(self, report_id):
        """Load existing annotations for current report and annotator."""
        self.current_report_annotations = {}
        if not self.current_annotator_name:
            return
            
        # Find most recent annotation for this report+annotator
        matching_annotations = [a for a in self.all_annotations 
                            if a["report_id"] == report_id and 
                                a["annotator"] == self.current_annotator_name]
        
        if matching_annotations:
            self.current_report_annotations = matching_annotations[-1]["annotation"]

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
            QToolButton {
                border: none;
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