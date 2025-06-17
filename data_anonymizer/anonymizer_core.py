import pandas as pd
import logging
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
import re

# -------------------------------
# Setup Logging
# -------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------------------
# Initialize Presidio Engines
# -------------------------------
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# -------------------------------
# Custom Recognizers
# -------------------------------

# Aadhaar recognizer
aadhar_recognizer = PatternRecognizer(
    supported_entity="AADHAAR",
    patterns=[Pattern("Aadhaar Pattern", r"\b\d{4}-\d{4}-\d{4}\b", 0.99)],
    supported_language="en"
)
analyzer.registry.add_recognizer(aadhar_recognizer)

# PAN recognizer
pan_recognizer = PatternRecognizer(
    supported_entity="PAN",
    patterns=[Pattern("PAN Pattern", r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", 0.95)],
    supported_language="en"
)
analyzer.registry.add_recognizer(pan_recognizer)

# IP recognizer
ip_recognizer = PatternRecognizer(
    supported_entity="IP_ADDRESS",
    patterns=[Pattern("IP Pattern", r"\b(?:\d{1,3}\.){3}\d{1,3}\b", 0.9)],
    supported_language="en"
)
analyzer.registry.add_recognizer(ip_recognizer)

# Bank Account Number recognizer (basic)
bank_recognizer = PatternRecognizer(
    supported_entity="BANK_ACCOUNT",
    patterns=[Pattern("Bank Pattern", r"\b\d{9,18}\b", 0.8)],
    supported_language="en"
)
analyzer.registry.add_recognizer(bank_recognizer)

# Local 10-digit phone number recognizer (Indian mobile format)
local_phone_recognizer = PatternRecognizer(
    supported_entity="PHONE_NUMBER",
    patterns=[Pattern("Local 10-digit", r"\b\d{10}\b", 1.0)],
    supported_language="en"
)
analyzer.registry.add_recognizer(local_phone_recognizer)

# -------------------------------
# Anonymize a Single String
# -------------------------------

def _anonymize_text(text: str) -> str:
    try:
        text = str(text).strip()
        if not text:
            return text
    except Exception:
        return text

    results = analyzer.analyze(
        text=text,
        language='en',
        entities=[
            "EMAIL_ADDRESS", "PHONE_NUMBER", "AADHAAR", "PERSON",
            "PAN", "IP_ADDRESS", "BANK_ACCOUNT", "CREDIT_CARD",
            "LOCATION", "DATE_TIME"
        ]
    )

    if results:
        anonymized = anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
                "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "XXX-XXX-XXXX"}),
                "AADHAAR": OperatorConfig("replace", {"new_value": "XXXX-XXXX-XXXX"}),
                "PERSON": OperatorConfig("replace", {"new_value": "[NAME]"}),
                "PAN": OperatorConfig("replace", {"new_value": "XXXXX0000X"}),
                "IP_ADDRESS": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX.XXX"}),
                "BANK_ACCOUNT": OperatorConfig("replace", {"new_value": "XXXXXXXXXXXX"}),
                "CREDIT_CARD": OperatorConfig("replace", {"new_value": "****-****-****-****"}),
                "DATE_TIME": OperatorConfig("replace", {"new_value": "[DATE]"}),
                "LOCATION": OperatorConfig("replace", {"new_value": "[ADDRESS]"}),
                "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})
            }
        )
        text = anonymized.text

    # 🔁 Fallback: Replace any missed 10-digit mobile numbers
    text = re.sub(r'\b\d{10}\b', 'XXX-XXX-XXXX', text)

    # 🔍 DEBUG (optional): Show if number still slipped
    if re.search(r'\b\d{10}\b', text):
        print(f"⚠️ Still found phone number in: {text}")

    return text

# -------------------------------
# Anonymize All Object Columns in DataFrame
# -------------------------------

def anonymize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            logger.info(f"🔒 Anonymizing column: {col}")
            if "name" in col.lower():
                # Forcefully replace values with [NAME]
                df[col] = df[col].apply(lambda x: "[NAME]" if isinstance(x, str) and x.strip() else x)
            else:
                df[col] = df[col].apply(_anonymize_text)
    return df

# -------------------------------
# Anonymize File (CSV or Excel)
# -------------------------------

def anonymize_file(input_path: str, output_path: str = None) -> pd.DataFrame:
    print(f"📂 Reading from: {input_path}")
    ext = input_path.split('.')[-1].lower()

    if ext == 'csv':
        df = pd.read_csv(input_path)
    elif ext in ['xls', 'xlsx']:
        df = pd.read_excel(input_path)
    
    elif ext == 'pdf':
        import pdfplumber
        with pdfplumber.open(input_path) as pdf:
            all_text = "\n".join(page.extract_text() or '' for page in pdf.pages)
        
        print("📝 Extracted Text Preview:")
        print(all_text[:500])  # show first 500 chars

        print("🔍 Running anonymization...")
        anonymized_text = _anonymize_text(all_text)

        if output_path:
            with open(output_path.replace('.pdf', '_anonymized.txt'), 'w', encoding='utf-8') as f:
                f.write(anonymized_text)
            print(f"💾 Anonymized text saved to: {output_path.replace('.pdf', '_anonymized.txt')}")
        
        return anonymized_text


    else:
        raise ValueError("❌ Unsupported file format. Only CSV and Excel are supported.")

    print("📝 Original Data Preview:")
    print(df.head())

    # Normalize Aadhaar before anonymizing
    if 'Aadhaar' in df.columns:
        df['Aadhaar'] = df['Aadhaar'].astype(str).str.replace(r'\D', '', regex=True)
        df['Aadhaar'] = df['Aadhaar'].apply(lambda x: f"{x[:4]}-{x[4:8]}-{x[8:]}" if len(x) == 12 else x)

    print("🔍 Running anonymization...")
    result_df = anonymize_dataframe(df)

    print("✅ Anonymized Data Preview:")
    print(result_df.head())

    if output_path:
        if ext == 'csv':
            result_df.to_csv(output_path, index=False)
        else:
            result_df.to_excel(output_path, index=False)
        print(f"💾 Anonymized file saved to: {output_path}")

    return result_df

def anonymize_document(input_path: str, output_path: str = None):
    """Public interface to be imported elsewhere."""
    return anonymize_file(input_path, output_path)

