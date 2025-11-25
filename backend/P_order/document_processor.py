"""
Document processing utilities for proforma and receipt extraction/validation.
Uses OCR, PDF parsing, and AI for data extraction.
"""
import re
import json
from typing import Dict, List, Optional, Any
import pdfplumber
import PyPDF2
from io import BytesIO
import importlib
from django.core.files.uploadedfile import UploadedFile

try:
    import importlib
    pytesseract = importlib.import_module("pytesseract")
    Image = importlib.import_module("PIL.Image")
    TESSERACT_AVAILABLE = True
except Exception:
    pytesseract = None
    Image = None
    TESSERACT_AVAILABLE = False
try:
    # Import openai dynamically to avoid static import errors when the package is not installed.
    openai_mod = importlib.import_module("openai")
    OpenAI = getattr(openai_mod, "OpenAI", None)
    OPENAI_AVAILABLE = OpenAI is not None
except Exception:
    OpenAI = None
    OPENAI_AVAILABLE = False
    OPENAI_AVAILABLE = False


def extract_text_from_pdf(file: UploadedFile) -> str:
    """Extract text from PDF file using pdfplumber."""
    try:
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        
        try:
            file.seek(0)
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception:
            return ""


def extract_text_from_image(file: UploadedFile) -> str:
    """Extract text from image using OCR (pytesseract)."""
    if not TESSERACT_AVAILABLE:
        return ""
    
    try:
        file.seek(0)
        image = Image.open(file)
        text = pytesseract.image_to_string(image)
        return text
    except Exception:
        return ""


def extract_text_from_file(file: UploadedFile) -> str:
    """Extract text from file (PDF or image)."""
    content_type = file.content_type or ""
    
    if "pdf" in content_type.lower() or file.name.lower().endswith(".pdf"):
        return extract_text_from_pdf(file)
    elif "image" in content_type.lower() or any(
        file.name.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif"]
    ):
        return extract_text_from_image(file)
    else:
        
        text = extract_text_from_pdf(file)
        if not text:
            text = extract_text_from_image(file)
        return text


def extract_proforma_data(file: UploadedFile) -> Dict[str, Any]:
    """
    Extract key data from proforma invoice/quotation.
    Returns: vendor, items, prices, terms, total_amount
    """
    text = extract_text_from_file(file)
    
    if not text:
        return {
            "vendor": "",
            "items": [],
            "total_amount": 0.0,
            "terms": "",
            "raw_text": "",
        }
    
    # Use AI if available for better extraction
    if OPENAI_AVAILABLE:
        try:
            client = OpenAI()
            prompt = f"""Extract structured data from this proforma invoice/quotation:
{text[:3000]}

Return JSON with: vendor (company name), items (array of {{description, quantity, unit_price}}), total_amount (number), terms (payment terms).
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )
            result = json.loads(response.choices[0].message.content)
            result["raw_text"] = text[:500]  # Store first 500 chars
            return result
        except Exception:
            pass
    
    # Fallback: Basic regex extraction
    vendor = ""
    items = []
    total_amount = 0.0
    terms = ""
    
    # Extract vendor (look for company name patterns)
    vendor_match = re.search(r"(?:vendor|supplier|company|from):\s*([A-Z][A-Za-z\s&]+)", text, re.IGNORECASE)
    if vendor_match:
        vendor = vendor_match.group(1).strip()
    
    # Extract total amount
    total_matches = re.findall(r"(?:total|amount|sum):\s*\$?(\d+[.,]?\d*)", text, re.IGNORECASE)
    if total_matches:
        try:
            total_amount = float(total_matches[-1].replace(",", ""))
        except ValueError:
            pass
    
    # Extract items (basic pattern matching)
    # Look for quantity x description @ price patterns
    item_pattern = r"(\d+)\s*x?\s*([A-Za-z\s]+?)\s*(?:@|at)?\s*\$?(\d+[.,]?\d*)"
    item_matches = re.findall(item_pattern, text, re.IGNORECASE)
    for match in item_matches[:10]:  # Limit to 10 items
        try:
            items.append({
                "description": match[1].strip(),
                "quantity": int(match[0]),
                "unit_price": float(match[2].replace(",", "")),
            })
        except ValueError:
            continue
    
    return {
        "vendor": vendor or "Unknown Vendor",
        "items": items,
        "total_amount": total_amount,
        "terms": terms,
        "raw_text": text[:500],
    }


def extract_receipt_data(file: UploadedFile) -> Dict[str, Any]:
    """
    Extract data from receipt.
    Returns: seller, items, prices, total_amount
    """
    text = extract_text_from_file(file)
    
    if not text:
        return {
            "seller": "",
            "items": [],
            "total_amount": 0.0,
            "raw_text": "",
        }
    
    # Use AI if available
    if OPENAI_AVAILABLE:
        try:
            client = OpenAI()
            prompt = f"""Extract structured data from this receipt:
{text[:3000]}

Return JSON with: seller (store/vendor name), items (array of {{description, quantity, unit_price}}), total_amount (number).
"""
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )
            result = json.loads(response.choices[0].message.content)
            result["raw_text"] = text[:500]
            return result
        except Exception:
            pass
    
    # Fallback: Basic regex extraction
    seller = ""
    items = []
    total_amount = 0.0
    
    # Extract seller
    seller_match = re.search(r"(?:seller|store|vendor|from):\s*([A-Z][A-Za-z\s&]+)", text, re.IGNORECASE)
    if seller_match:
        seller = seller_match.group(1).strip()
    
    # Extract total
    total_matches = re.findall(r"(?:total|amount|sum):\s*\$?(\d+[.,]?\d*)", text, re.IGNORECASE)
    if total_matches:
        try:
            total_amount = float(total_matches[-1].replace(",", ""))
        except ValueError:
            pass
    
    # Extract items
    item_pattern = r"(\d+)\s*x?\s*([A-Za-z\s]+?)\s*(?:@|at)?\s*\$?(\d+[.,]?\d*)"
    item_matches = re.findall(item_pattern, text, re.IGNORECASE)
    for match in item_matches[:10]:
        try:
            items.append({
                "description": match[1].strip(),
                "quantity": int(match[0]),
                "unit_price": float(match[2].replace(",", "")),
            })
        except ValueError:
            continue
    
    return {
        "seller": seller or "Unknown Seller",
        "items": items,
        "total_amount": total_amount,
        "raw_text": text[:500],
    }


def validate_receipt_against_po(receipt_data: Dict[str, Any], po_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare receipt data against Purchase Order.
    Returns: validated (bool), discrepancies (list of issues)
    """
    discrepancies = []
    validated = True
    
    # Check seller/vendor match
    receipt_seller = receipt_data.get("seller", "").lower()
    po_vendor = po_data.get("vendor", "").lower()
    if receipt_seller and po_vendor and receipt_seller not in po_vendor and po_vendor not in receipt_seller:
        discrepancies.append({
            "type": "vendor_mismatch",
            "message": f"Receipt seller '{receipt_data.get('seller')}' does not match PO vendor '{po_data.get('vendor')}'",
        })
        validated = False
    
    # Check total amount (allow 5% tolerance)
    receipt_total = receipt_data.get("total_amount", 0.0)
    po_total = float(po_data.get("total_amount", 0.0))
    if receipt_total > 0 and po_total > 0:
        tolerance = po_total * 0.05  # 5% tolerance
        if abs(receipt_total - po_total) > tolerance:
            discrepancies.append({
                "type": "amount_mismatch",
                "message": f"Receipt total ${receipt_total:.2f} differs from PO total ${po_total:.2f} by more than 5%",
                "receipt_amount": receipt_total,
                "po_amount": po_total,
            })
            validated = False
    
    # Check items (basic comparison)
    receipt_items = receipt_data.get("items", [])
    po_items = po_data.get("item_snapshot", [])
    
    if len(receipt_items) != len(po_items):
        discrepancies.append({
            "type": "item_count_mismatch",
            "message": f"Receipt has {len(receipt_items)} items, PO has {len(po_items)} items",
        })
        validated = False
    
    # Compare individual items (simplified - just check if descriptions match)
    if receipt_items and po_items:
        receipt_descriptions = [item.get("description", "").lower() for item in receipt_items]
        po_descriptions = [item.get("description", "").lower() for item in po_items]
        
        for po_desc in po_descriptions:
            if not any(po_desc in rec_desc or rec_desc in po_desc for rec_desc in receipt_descriptions):
                discrepancies.append({
                    "type": "item_mismatch",
                    "message": f"PO item '{po_desc}' not found in receipt",
                })
                validated = False
    
    return {
        "validated": validated,
        "discrepancies": discrepancies,
    }

