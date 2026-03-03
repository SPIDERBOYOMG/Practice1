import re
import json

def parse_receipt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Extract date and time: Время: DD.MM.YYYY HH:MM:SS
    date_match = re.search(r'Время:\s*(\d{2}\.\d{2}\.\d{4}\s+\d{2}:\d{2}:\d{2})', text)
    date_time = date_match.group(1) if date_match else None
    
    # Extract all prices: numbers followed by ',00' or with spaces like '1 200,00'
    prices = re.findall(r'\b(\d+\s*,\d{2})\b', text)
    prices = [p.strip().replace(' ', '') for p in prices]
    
    # Calculate total (should match ИТОГО)
    total_match = re.search(r'ИТОГО:\s*(\d+\s*,\d{2})', text)
    total = float(total_match.group(1).replace(' ', '').replace(',', '.')) if total_match else sum(float(p.replace(',', '.')) for p in prices)
    
    # Extract product names: after number. until quantity line
    products = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.match(r'^\d+\.', line):
            # Next non-empty line is product name
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                product = lines[i].strip()
                products.append(product)
        i += 1
    
    # Payment method
    payment = re.search(r'(Банковская карта):?\s*\d', text)
    payment_method = payment.group(1) if payment else 'Unknown'
    
    result = {
        'date_time': date_time,
        'payment_method': payment_method,
        'prices': prices,
        'total': total,
        'products': products
    }
    return result

if __name__ == '__main__':
    data = parse_receipt('raw.txt')
    print(json.dumps(data, ensure_ascii=False, indent=2))
