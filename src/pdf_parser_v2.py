#!/usr/bin/env python3
"""
PDF Parser v5 - Uses expected section titles for matching
Extracts all 13 sections from Thai E-bidding Documents
"""

import re
import json
import sys
import fitz
from typing import List, Dict, Tuple, Optional

THAI_TO_ARABIC = {
    '๐': '0', '๑': '1', '๒': '2', '๓': '3', '๔': '4',
    '๕': '5', '๖': '6', '๗': '7', '๘': '8', '๙': '9'
}

def thai_to_arabic_number(text: str) -> str:
    result = text
    for thai, arabic in THAI_TO_ARABIC.items():
        result = result.replace(thai, arabic)
    return result

def extract_text_from_pdf(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text

def normalize_text(text: str) -> str:
    """Normalize for comparison"""
    return ' '.join(text.lower().strip().split())

# Expected full titles or their core parts
EXPECTED_TITLES = {
    "1": "เอกสารแนบท้ายเอกสารประกวดราคาอิเล็กทรอนิกส์",
    "2": "คุณสมบัติของผู้ยื่นข้อเสนอ",
    "3": "หลักฐานการยื่นข้อเสนอ",
    "4": "การเสนอราคา",
    "5": "หลักประกันการเสนอราคา",
    "6": "หลักเกณฑ์และสิทธิ์ในการพิจารณา",
    "7": "การทำสัญญา",
    "8": "ค่าจ้างและการจ่ายเงิน",
    "9": "อัตราค่าปรับ",
    "10": "การรับประกันความชำรุดบกพร่อง",
    "11": "ข้อสงวนสิทธิ์ในการยื่นข้อเสนอและอื่นๆ",
    "12": "การปฏิบัติตามกฎหมายและระเบียบ",
    "13": "การประเมินผลการปฏิบัติงานของผู้ประกอบการ",
}

# Shorter core keywords for matching (must all be present)
CORE_KEYWORDS = {
    "1": ["เอกสาร", "แนบ", "ท้าย"],
    "2": ["คุณสมบัติ", "ผู้ยื่น", "ข้อเสนอ"],
    "3": ["หลักฐาน", "การยื่น", "ข้อเสนอ"],
    "4": ["การเสนอราคา"],  # Exact match needed
    "5": ["หลักประกัน", "การเสนอราคา"],
    "6": ["หลักเกณฑ์", "สิทธิ", "พิจารณา"],
    "7": ["การทำสัญญา"],  # Must be exact or with เช่า
    "8": ["ค่าจ้าง", "การจ่ายเงิน"],
    "9": ["อัตรา", "ค่าปรับ"],
    "10": ["รับประกัน", "ความชำรุด", "บกพร่อง"],
    "11": ["ข้อสงวนสิทธิ"],
    "12": ["ปฏิบัติ", "กฎหมาย", "ระเบียบ"],
    "13": ["ประเมินผล", "ปฏิบัติงาน", "ผู้ประกอบการ"],
}

def title_matches_section(title: str, section_num: str) -> bool:
    """
    Check if a title matches the expected section using strict rules
    """
    if section_num not in CORE_KEYWORDS:
        return False
    
    title_norm = normalize_text(title)
    keywords = CORE_KEYWORDS[section_num]
    
    # All keywords must be present
    all_present = all(normalize_text(kw) in title_norm for kw in keywords)
    
    if not all_present:
        return False
    
    # Additional checks for ambiguous cases
    if section_num == "4":
        # Must be "การเสนอราคา" and NOT "หลักประกันการเสนอราคา"
        return "หลักประกัน" not in title_norm and len(title_norm) < 20
    
    if section_num == "7":
        # Should be just "การทำสัญญา" possibly with "เช่า"
        return len(title_norm) < 25
    
    if section_num == "11":
        # Should contain "ข้อสงวนสิทธิ์"
        return "ข้อสงวนสิทธิ" in title_norm
    
    return True

def has_section_number_nearby(lines: List[str], title_line_idx: int, section_num: str) -> Tuple[bool, int]:
    """
    Check if the section number appears within 2 lines before OR after the title.
    Returns: (found, line_number_of_section_num)
    """
    # Check lines BEFORE the title (up to 2 lines)
    for offset in range(1, min(3, title_line_idx + 1)):
        check_idx = title_line_idx - offset
        if check_idx < 0:
            break
        
        line = lines[check_idx].strip()
        
        # Pattern: Standalone number "๕."
        if re.match(r'^[๑-๙\d]+\.$', line):
            num = thai_to_arabic_number(line.rstrip('.'))
            if num == section_num:
                return (True, check_idx)
    
    # Check lines AFTER the title (up to 2 lines) - THIS IS KEY FOR THIS DOCUMENT!
    for offset in range(1, min(3, len(lines) - title_line_idx)):
        check_idx = title_line_idx + offset
        if check_idx >= len(lines):
            break
        
        line = lines[check_idx].strip()
        
        # Pattern: Standalone number "๕."
        if re.match(r'^[๑-๙\d]+\.$', line):
            num = thai_to_arabic_number(line.rstrip('.'))
            if num == section_num:
                # Use title line as the reference point
                return (True, title_line_idx)
    
    return (False, -1)

def find_section_by_title_scan(lines: List[str]) -> List[Dict]:
    """
    Find sections by scanning for title lines that match expected titles
    AND have the corresponding section number nearby
    """
    headers = []
    found_sections = set()
    
    for section_num in range(1, 14):
        section_str = str(section_num)
        expected_title = EXPECTED_TITLES[section_str]
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            
            # Skip if already found
            if section_str in found_sections:
                continue
            
            # Pattern 1: Combined format "๕. หลักประกันการเสนอราคา"
            combined_match = re.match(r'^([๑-๙\d]+)\.\s+(.+)$', line_clean)
            if combined_match:
                num_part = thai_to_arabic_number(combined_match.group(1))
                title_part = combined_match.group(2).strip()
                
                if num_part == section_str and title_matches_section(title_part, section_str):
                    # Additional check: make sure this is not a subsection
                    # Main sections should have minimal indentation
                    indent = len(line) - len(line.lstrip())
                    if indent < 25:  # Main sections have less indentation
                        headers.append({
                            'line': i,
                            'number': section_str,
                            'title': title_part
                        })
                        found_sections.add(section_str)
                        break
            
            # Pattern 2: Title only, number on previous line
            elif len(line_clean) > 10 and title_matches_section(line_clean, section_str):
                # CRITICAL: Must have section number nearby
                has_num, num_line = has_section_number_nearby(lines, i, section_str)
                
                if has_num:
                    # Check indentation
                    indent = len(lines[num_line]) - len(lines[num_line].lstrip())
                    if indent < 25:
                        headers.append({
                            'line': num_line,
                            'number': section_str,
                            'title': line_clean
                        })
                        found_sections.add(section_str)
                        break
        
    return sorted(headers, key=lambda x: x['line'])

def parse_document(text: str) -> Dict:
    """Parse document"""
    lines = text.split('\n')
    
    # Find headers
    headers = find_section_by_title_scan(lines)
    
    # Check missing
    found = set(h['number'] for h in headers)
    expected = set(str(i) for i in range(1, 14))
    missing = expected - found
    
    # Extract content
    sections = []
    for idx, header in enumerate(headers):
        # Start after the title line
        start_line = header['line']
        
        # Find next section or EOF
        if idx + 1 < len(headers):
            end_line = headers[idx + 1]['line']
        else:
            end_line = len(lines)
        
        # Skip the header lines themselves
        content_start = start_line + 1
        # If title is on separate line from number, skip both
        if start_line + 1 < len(lines):
            next_line = lines[start_line + 1].strip()
            if next_line and normalize_text(next_line) == normalize_text(header['title']):
                content_start = start_line + 2
        
        content_lines = lines[content_start:end_line]
        content = '\n'.join(content_lines).strip()
        
        sections.append({
            'section_number': header['number'],
            'title': header['title'],
            'line_number': header['line'],
            'content': content,
            'content_length': len(content)
        })
    
    return {
        'document_title': 'เอกสารประกวดราคาเช่าด้วยวิธีประกวดราคาอิเล็กทรอนิกส์ (e-bidding)',
        'total_sections': len(sections),
        'sections': sections,
        'missing_sections': sorted(missing, key=int) if missing else []
    }