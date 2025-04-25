import sys
import csv
import json
import argparse
import yaml
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QProgressBar, QGroupBox,
    QSlider, QRadioButton, QCheckBox, QButtonGroup, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

class AnnotationApp(QMainWindow):
    def __init__(self, csv_path, yaml_path, output_path):
        super().__init__()
        self.setWindowTitle("Patient Report Annotator")
        self.current_index = 0
        self.data = []
        self.annotations = {}
        self.button_groups = {}
        self.output_path = output_path
        self.suppress_save_warnings = False  # Default to showing warnings
        
        # Load task with error handling
        try:
            self.task_config = self.load_task_config(yaml_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            sys.exit(1)

        # Load or create annotations file
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r') as f:
                    self.annotations = json.load(f)
            except:
                QMessageBox.warning(self, "Warning", "Could not load existing annotations file. Starting fresh.")

        # Setup UI
        self.init_ui()
        self.apply_styles()
        self.load_settings()  # Load user preferences

        # Load data with error handling
        try:
            self.load_data(csv_path)
            self.update_progress()
            self.find_first_unannotated()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            sys.exit(1)
    
    def init_ui(self):
        """Initialize all UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Left panel: Text display (monospace font)
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Courier New", 10))  # Monospace for \n, \t
        layout.addWidget(self.text_display, stretch=7)
        
        # Right panel: Controls
        right_panel = QVBoxLayout()
        layout.addLayout(right_panel, stretch=3)
        
        # Task instructions (from YAML)
        self.instructions = QTextEdit()
        self.instructions.setReadOnly(True)
        self.instructions.setPlainText(self.task_config.get("instructions", "No instructions provided."))
        right_panel.addWidget(QLabel("<b>Task Instructions<b>"))
        right_panel.addWidget(self.instructions)
        
        # Navigation buttons
        nav_group = QGroupBox("Navigation")
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton("⏮ Previous")
        self.next_button = QPushButton("Next ⏭")
        self.save_button = QPushButton("💾 Save")
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addWidget(self.save_button)
        nav_group.setLayout(nav_layout)
        right_panel.addWidget(nav_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        right_panel.addWidget(self.progress_bar)
        
        # Annotation controls
        self.annotation_group = QGroupBox(self.task_config.get("name", "Annotations"))
        self.annotation_layout = QVBoxLayout()
        self.annotation_group.setLayout(self.annotation_layout)
        right_panel.addWidget(self.annotation_group)
        
        # Signals
        self.prev_button.clicked.connect(self.prev_entry)
        self.next_button.clicked.connect(self.next_entry)
        self.save_button.clicked.connect(self.save_and_next)
        
        # Build UI
        self.build_annotation_ui()
        self.update_ui()

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
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                if not {"Patient-ID", "Report-ID", "Text"}.issubset(reader.fieldnames):
                    raise ValueError("CSV must include columns: Patient-ID, Report-ID, Text")
                self.data = list(reader)
        except Exception as e:
            raise ValueError(f"Invalid CSV: {str(e)}")
    
    def build_annotation_ui(self):
        """Recursively build UI from YAML groups with control tracking."""
        self.controls = {}  # Dictionary to track all controls by label
        self.button_groups = {}  # For radio button groups
        self.required_controls = []  # List of required controls

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
        return data

    def clear_controls(self):
        """Reset all input controls to default values"""
        for control in self.controls.values():
            if isinstance(control, QSlider):
                control.setValue(control.minimum())
            elif isinstance(control, QButtonGroup):
                control.setExclusive(False)
                for button in control.buttons():
                    button.setChecked(False)
                control.setExclusive(True)
            elif isinstance(control, QCheckBox):
                control.setChecked(False)

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
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to CSV file")
    parser.add_argument("--yaml", required=True, help="Path to YAML task file")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    window = AnnotationApp(args.csv, args.yaml, args.output)
    window.show()
    sys.exit(app.exec_())