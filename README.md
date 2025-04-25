# Medical Report Annotation Tool

A PyQt5-based GUI for annotating medical reports with structured data.

## Features

- Load patient reports from CSV (Patient-ID, Report-ID, Text)
- Define annotation tasks (Task manager) via YAML configuration
- Track progress with visual indicators
- Save annotations to JSON with validation

## Quick Start

1. Install requirements:
```bash
pip install pyqt5 pyyaml
```

2. Run the annotator:
```bash
python app.py --csv reports.csv --yaml task.yaml --output annotations.json
```

### Arguments

- --csv: Path to patient reports CSV (required)
- --yaml: Path to task definition YAML (required)
- --output: Path to save annotations JSON (required)

## File Formats

### CSV Input

```
Patient-ID,Report-ID,Text
P001,R001,"Patient report text..."
```

### YAML Task

```yaml
name: "Medical Annotation"
instructions: "Mark all relevant findings..."
groups:
  - label: "Symptoms"
    controls:
      - type: slider
        label: "Severity"
        min: 1
        max: 5
        required: true
```

### JSON Output

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