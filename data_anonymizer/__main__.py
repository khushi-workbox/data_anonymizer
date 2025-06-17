import argparse
from .anonymizer_core import anonymize_file

def main():
    parser = argparse.ArgumentParser(
        description="🔒 PII Data Anonymizer using Presidio. Supports CSV, Excel, and PDF input."
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help="📂 Path to input file (.csv, .xlsx, .xls, .pdf)"
    )
    parser.add_argument(
        '--output', '-o',
        required=False,
        help="💾 Path to save anonymized output (CSV, Excel or TXT for PDF)"
    )

    args = parser.parse_args()

    anonymize_file(args.input, args.output)

if __name__ == "__main__":
    main()
