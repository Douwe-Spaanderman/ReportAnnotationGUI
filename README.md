# Medical Report Annotation Tool

A lightweight, PyQt5-based GUI for annotating medical reports using structured tasks defined in a YAML file.

## 🚀 Features

- Load free-text medical reports from a CSV file
- Automatically generate an annotation interface from a YAML task definition
- Save validated annotations to a structured JSON file, and export back to CSV
- Multi-user annotation support with individual tracking
- Multi-report annotation support
- Match free-text fields directly to UMLS

## ⚡ Quick Start

### 1. Install Dependencies

```bash
pip install pyqt5 pyyaml
```

When using UMLS mapper you also need to: `pip install scispacy`

### 2. Launch the App

```bash
python app.py
```

Upon launching, a file selection dialog will prompt you to select:

- The patient reports CSV file  
- The annotation task YAML file  
- The output path for the annotated JSON file  

### Optional: Provide Paths via CLI

You can skip the file dialog by passing paths directly:

```bash
python app.py --csv reports.csv --yaml task.yaml --output annotations.json
```

**Arguments:**

- `--csv`: Path to the CSV file with medical reports  
- `--yaml`: Path to the YAML file defining the annotation task  
- `--output`: Path to save the output JSON file

## 📁 File Formats

### CSV Input

The CSV file should include the following columns:

```csv
Patient-ID,Report-ID,Report-Date,Text
P001,R001,"01-01-2025","Patient report text..."
```

Each row corresponds to a report that will be annotated.

➡️ [View example CSV](assets/example.csv)

### YAML Task Definition

The YAML file defines the structure and controls used during annotation:

```yaml
name: "Medical Annotation"
instructions: "Mark all relevant findings based on the report content."
groups:
  - label: "Symptoms"
    controls:
      - type: slider
        label: "Severity"
        min: 1
        max: 5
        required: true
```

Controls can include sliders, checkboxes, dropdowns, and more.

➡️ [View example YAML](assets/example.yaml)
- [View additional YAML configs](configs/)

### JSON Output

Annotations are saved using the following structure:

```json
{
  "R001": {
    "Patient-ID": "P001",
    "annotations": {
      "Severity": 3
    }
  }
}
```

Each entry is indexed by the report ID, and includes both metadata and annotated values.

### CSV Export

In the viewer annotations can be exported to CSV under file.

## 🛠️ Coming Soon

- Undo/redo functionality
- More Hotkeys for faster annotation

## 📬 Feedback & Contributions

Feel free to open an issue or submit a pull request to improve this tool. Suggestions and bug reports are welcome!