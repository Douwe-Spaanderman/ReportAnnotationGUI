import re
from pypdf import PdfReader
import csv
from pathlib import Path

def extract_reports(pdf_path, first_page_marker="Aard materiaal", subsequent_page_marker="geboortedatum: anoniem", extact_id = None):
    """Extract reports with metadata from PDF."""
    reader = PdfReader(pdf_path)
    reports = []
    current_report = []
    total_pages_for_report = 1
    current_page_in_report = 0
    pa_nummer = None
    datum = None

    if extact_id:
        match = re.search(r'deel\s+(\d+)', extact_id, re.IGNORECASE)
        if match:
            match = f"Deel {match.group(1)}"
    
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        
        # Check for page indicator
        page_indicator = re.search(r'Pagina:\s*(\d+)\s*van\s*(\d+)', text)
        
        if page_indicator:
            current_page_in_report = int(page_indicator.group(1))
            total_pages_for_report = int(page_indicator.group(2))
            
            if current_page_in_report == 1:
                if current_report:  # Save previous report
                    reports.append({
                        'patient': "Annoniem",
                        'ID': match if extact_id else None,
                        'pa_nummer': pa_nummer,
                        'datum': datum,
                        'content': ' '.join(current_report).replace('\n', ' ').strip()
                    })
                    current_report = []
                
                # Process first page
                content, pa_nummer, datum = extract_first_page_content(text, first_page_marker)
                if content:
                    current_report.append(content)
                else:
                    raise ValueError(f"First page marker '{first_page_marker}' not found on page {page_num}")
            else:
                # Process subsequent page
                content = extract_subsequent_page_content(text, subsequent_page_marker)
                if content:
                    current_report.append(content)
                else:
                    raise ValueError(f"Subsequent page marker '{subsequent_page_marker}' not found on page {page_num}")
            
            # Save if last page of report
            if current_page_in_report == total_pages_for_report and current_report:
                reports.append({
                    'patient': "Annoniem",
                    'ID': match if extact_id else None,
                    'pa_nummer': pa_nummer,
                    'datum': datum,
                    'content': ' '.join(current_report).replace('\n', ' ').strip()
                })
                current_report = []
        else:
            # Page without indicator - assume continuation
            if current_report:
                content = extract_subsequent_page_content(text, subsequent_page_marker) or text
                current_report.append(content)
    
    # Add any remaining report
    if current_report:
        reports.append({
            'patient': "Annoniem",
            'ID': match if extact_id else None,
            'pa_nummer': pa_nummer,
            'datum': datum,
            'content': ' '.join(current_report).replace('\n', ' ').strip()
        })
    
    return reports

def extract_first_page_content(text, first_page_marker):
    """Extract content and metadata from first page."""
    # Extract PA-nummer (format: W00-40587)
    pa_match = re.search(r'(?<=\n)[A-Za-z]\d{2}-\d{5}(?=\n)', text)
    pa_nummer = pa_match.group(0) if pa_match else None
    
    # Extract Datum (format: DD-MM-YYYY)
    date_match = re.search(r'Datum ontvangst (\d{2}-\d{2}-\d{4})', text)
    datum = date_match.group(1) if date_match else None
    
    # Extract content
    marker_index = text.find(first_page_marker)
    if marker_index == -1:
        return None, None, None
    
    content = text[marker_index + len(first_page_marker):]
    footer_index = content.find('Pagina:')
    if footer_index != -1:
        content = content[:footer_index]
    
    return content.strip(), pa_nummer, datum

def extract_subsequent_page_content(text, subsequent_page_marker):
    """Extract content from subsequent pages."""
    marker_index = text.find(subsequent_page_marker)
    if marker_index == -1:
        return None
    
    content = text[marker_index + len(subsequent_page_marker):]
    footer_index = content.find('Pagina:')
    if footer_index != -1:
        content = content[:footer_index]
    
    return content.strip()

def save_reports_to_csv(reports, output_file='pathology_reports.csv'):
    """Save all reports to a single CSV file with one report per row."""
    if output_file.exists():
        header = False
    else:
        header = True

    with open(output_file, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        if header:
            writer.writerow(['Patient', 'ID', 'PA-nummer', 'Datum', 'Content'])
        
        # Write each report as a single row
        for report in reports:
            writer.writerow([
                report['patient'] or 'Annoniem',
                report['ID'] or 'N/A',
                report['pa_nummer'] or 'N/A',
                report['datum'] or 'N/A',
                report['content']
            ])
    
    print(f"Saved {len(reports)} reports to {output_file}")

if __name__ == "__main__":
    import argparse
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Extracting text from pdf. Note, now ')
    parser.add_argument('--pdf', help='Path to directory with PDFs')
    parser.add_argument('--output', required=False, default="Extracted.csv", help='Define output file')
    args = parser.parse_args()

    output_file = Path(args.output).with_suffix(".csv")

    pdf_paths = list(Path(args.pdf).glob("*.pdf"))
    for pdf_path in pdf_paths:
        print(pdf_path.name)
        try:
            reports = extract_reports(
                pdf_path,
                first_page_marker="Aard materiaal:",
                subsequent_page_marker="Geboortedatum: Anoniem",
                extact_id=pdf_path.name
            )
            save_reports_to_csv(reports, output_file)
        except ValueError as e:
            print(f"Error processing PDF: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")