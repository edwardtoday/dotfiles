import argparse
import sys
import os

def parse_page_ranges(pages_str):
    """
    Parses a string like "1-3, 5, 8-10" into a list of 0-based indices.
    """
    indices = []
    parts = pages_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = part.split('-')
                start = int(start)
                end = int(end)
                if start > end:
                    start, end = end, start
                indices.extend(range(start - 1, end))
            except ValueError:
                print(f"Warning: Invalid range format '{part}'. Ignoring.")
        else:
            try:
                page = int(part)
                indices.append(page - 1)
            except ValueError:
                print(f"Warning: Invalid page number '{part}'. Ignoring.")
    return sorted(list(set(indices)))

def main():
    parser = argparse.ArgumentParser(description="Extract pages from a PDF file.")
    parser.add_argument("input_file", help="Path to the source PDF file.")
    parser.add_argument("pages", help="Pages to extract (e.g., '1-5, 8, 10-12').")
    parser.add_argument("output_file", help="Path to the destination PDF file.")
    
    args = parser.parse_args()

    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        print("Error: pypdf not installed in the virtual environment.")
        sys.exit(1)

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)

    try:
        reader = PdfReader(args.input_file)
        writer = PdfWriter()
        
        target_indices = parse_page_ranges(args.pages)
        total_pages = len(reader.pages)
        
        extracted_count = 0
        
        for idx in target_indices:
            if 0 <= idx < total_pages:
                writer.add_page(reader.pages[idx])
                extracted_count += 1
            else:
                print(f"Warning: Page {idx + 1} is out of range (PDF has {total_pages} pages). Skipped.")

        if extracted_count == 0:
            print("Error: No valid pages selected to extract.")
            sys.exit(1)

        output_dir = os.path.dirname(os.path.abspath(args.output_file))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(args.output_file, "wb") as f:
            writer.write(f)
            
        print(f"Success: Extracted {extracted_count} pages to '{args.output_file}'")

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
