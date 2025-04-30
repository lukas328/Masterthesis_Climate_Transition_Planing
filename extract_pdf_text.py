import os
from pypdf import PdfReader
import sys

# --- Configuration ---
# Directory containing your PDF files (relative to where you run the script)
pdf_input_dir = "data"
# Directory where you want to save the extracted text files
text_output_dir = "data_text_extracted"
# --- End Configuration ---

def extract_text_from_pdf(pdf_path):
    """Extracts text from a single PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n" # Add newline between pages
            else:
                print(f"Warning: Could not extract text from page {page_num + 1} of {os.path.basename(pdf_path)}")
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        # Add more specific exception handling if needed, e.g., for encrypted PDFs
        # from pypdf.errors import FileNotDecryptedError
        # except FileNotDecryptedError:
        #     print(f"Error: Could not decrypt {pdf_path}. Is it password protected?")
        return None

def main():
    """Finds PDFs in input dir and saves extracted text to output dir."""
    # Get absolute paths based on script location or current working directory
    script_dir = os.path.dirname(os.path.abspath(__file__)) # Or use os.getcwd() if running from project root
    abs_pdf_input_dir = os.path.join(script_dir, pdf_input_dir)
    abs_text_output_dir = os.path.join(script_dir, text_output_dir)

    if not os.path.isdir(abs_pdf_input_dir):
        print(f"Error: Input directory '{abs_pdf_input_dir}' not found.")
        sys.exit(1)

    # Create output directory if it doesn't exist
    os.makedirs(abs_text_output_dir, exist_ok=True)
    print(f"Output directory: '{abs_text_output_dir}'")

    print(f"Starting PDF text extraction from '{abs_pdf_input_dir}'...")
    extracted_count = 0
    skipped_count = 0

    for filename in os.listdir(abs_pdf_input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_file_path = os.path.join(abs_pdf_input_dir, filename)
            print(f"Processing '{filename}'...")

            extracted_text = extract_text_from_pdf(pdf_file_path)

            if extracted_text:
                # Create corresponding text file path
                txt_filename = os.path.splitext(filename)[0] + ".txt"
                txt_file_path = os.path.join(abs_text_output_dir, txt_filename)

                # Write extracted text to file (using UTF-8 encoding)
                try:
                    with open(txt_file_path, "w", encoding="utf-8") as txt_file:
                        txt_file.write(extracted_text)
                    print(f"  -> Saved text to '{txt_filename}'")
                    extracted_count += 1
                except Exception as e:
                    print(f"  Error writing text file for {filename}: {e}")
                    skipped_count += 1
            else:
                print(f"  -> Skipping {filename} due to extraction errors or no text found.")
                skipped_count += 1
        else:
            print(f"Skipping non-PDF file: '{filename}'")


    print("\nExtraction Complete.")
    print(f"Successfully extracted text from: {extracted_count} PDF(s)")
    print(f"Skipped/Errored: {skipped_count} PDF(s)")

if __name__ == "__main__":
    main()