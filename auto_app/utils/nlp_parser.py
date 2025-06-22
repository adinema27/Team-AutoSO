import re

def extract_order_details(prompt):
    # Match: cust1005, customer-1005, customer 1005, CUST-1005
    cust_match = re.search(r"\b(?:cust(?:omer)?)\s*[-:]?\s*(\d+)", prompt, re.IGNORECASE)

    # Match: MAT001007, MAT-001007, material 001007, MATERIAL:001007
    mat_match = re.search(r"\b(?:mat(?:erial)?)\s*[-:]?\s*(\d+)", prompt, re.IGNORECASE)

    # Match: quantity 5, qty-5, unit: 5
    qty_match = re.search(r"\b(?:quantity|qty|unit)\s*[-:]?\s*(\d+)", prompt, re.IGNORECASE)

    if not all([cust_match, mat_match, qty_match]):
        print("❌ One or more fields could not be extracted.")
        return {
            'customer_number': cust_match.group(1) if cust_match else None,
            'material_number': mat_match.group(1) if mat_match else None,
            'quantity': int(qty_match.group(1)) if qty_match else None
        }

    result = {
        'customer_number': cust_match.group(1),
        'material_number': mat_match.group(1),
        'quantity': int(qty_match.group(1))
    }

    print(f"🔍 Extracted from NLP: {result}")
    return result
