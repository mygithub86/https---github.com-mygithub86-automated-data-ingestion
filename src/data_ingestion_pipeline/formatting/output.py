import os
import logging
import re
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer # If using reportlab
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib.pagesizes import letter
# from fpdf import FPDF # If using fpdf2

def save_to_text(data_item, output_config):
    """Saves processed content to a text file. Implements FR4.1."""
    base_dir = output_config.get('text_output_dir', 'output/text')
    source = data_item.get('source', 'unknown')
    item_id = data_item.get('id', 'unknown_id')

    # Sanitize item_id for use in filename (replace common problematic chars)
    safe_filename = re.sub(r'[\\/*?:'"<>|]', '_', str(item_id))
    filename = f"{safe_filename}.txt"
    output_path = os.path.join(base_dir, source)

    try:
        os.makedirs(output_path, exist_ok=True)
        filepath = os.path.join(output_path, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            # Optional: Add metadata header
            if output_config.get('include_metadata_header', False):
                f.write(f"Source: {source}\n")
                f.write(f"ID: {item_id}\n")
                f.write(f"Type: {data_item.get('type', 'unknown')}\n")
                # Include URL from metadata if it exists
                metadata_url = data_item.get('metadata', {}).get('url')
                if metadata_url:
                     f.write(f"URL: {metadata_url}\n")
                f.write("---\n\n")
            # Write the processed content
            f.write(data_item.get('processed_content', '')) # Use processed content

        logging.debug(f"Saved text file: {filepath}")
        return filepath
    except IOError as e:
        logging.error(f"Failed to save text file {filepath}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error saving text file for item {item_id}: {e}", exc_info=True)
        return None


def save_to_pdf(data_item, output_config):
    """Saves processed content to a PDF file. Implements FR4.2."""
    base_dir = output_config.get('pdf_output_dir', 'output/pdf')
    source = data_item.get('source', 'unknown')
    item_id = data_item.get('id', 'unknown_id')

    safe_filename = re.sub(r'[\\/*?:'"<>|]', '_', str(item_id))
    filename = f"{safe_filename}.pdf"
    output_path = os.path.join(base_dir, source)

    # === PLACEHOLDER: Use reportlab or fpdf2 ===
    logging.warning("PDF generation requires a library (reportlab/fpdf2) and implementation.")
    # Example structure using reportlab:
    try:
        os.makedirs(output_path, exist_ok=True)
        filepath = os.path.join(output_path, filename)

        # --- ReportLab Implementation Placeholder ---
        # from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        # from reportlab.lib.styles import getSampleStyleSheet
        # from reportlab.lib.pagesizes import letter
        #
        # doc = SimpleDocTemplate(filepath, pagesize=letter)
        # styles = getSampleStyleSheet()
        # story = []
        #
        # # Add metadata
        # story.append(Paragraph(f"Source: {source}", styles['Normal']))
        # story.append(Paragraph(f"ID: {item_id}", styles['Normal']))
        # metadata_url = data_item.get('metadata', {}).get('url')
        # if metadata_url:
        #     story.append(Paragraph(f"URL: {metadata_url}", styles['Code'])) # Style URL differently
        # story.append(Spacer(1, 12))
        #
        # # Add content - handle long text and potential formatting issues
        # content = data_item.get('processed_content', '')
        # # Replace newlines for basic paragraph structure in PDF
        # pdf_content = content.replace('\n', '<br/>')
        # story.append(Paragraph(pdf_content, styles['Normal']))
        #
        # doc.build(story)
        # --- End ReportLab Placeholder ---

        logging.debug(f"Saved PDF file (placeholder): {filepath}")
        return filepath # Return path even if generation is placeholder

    except ImportError:
        logging.error("PDF generation library (e.g., reportlab or fpdf2) not installed.")
        return None
    except Exception as e:
        logging.error(f"Failed to save PDF file {filepath}: {e}", exc_info=True)
        return None
    # === END PLACEHOLDER === 