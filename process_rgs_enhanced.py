#!/usr/bin/env python3
"""
Corrected RGS Data Processing Script
Implements the enhanced multi-factor mapping approach aligned with design specification

This script processes RGS data using:
1. Enhanced RGS to ERPNext mapping logic
2. Three-document integration (canonical + specs + translations)  
3. Correct field naming per design specification
4. Multi-factor root_type determination
5. Intelligent account_type derivation

Author: ERPNext RGS MKB Project
Date: August 2025
"""

import json
import csv
import os
import sys
from pathlib import Path

# Import our enhanced mapping logic
try:
    from enhanced_rgs_mapping import RGSToERPNextMapper
except ImportError:
    print("❌ ERROR: Could not import enhanced_rgs_mapping module")
    print("   Please ensure enhanced_rgs_mapping.py is in the same directory")
    sys.exit(1)

def load_rgs_canonical_data():
    """Load the canonical RGS data from rgsmkb_all4EN.json"""
    possible_paths = [
        '/opt/frappe_docker/rgs_mkb/rgsmkb_all4EN.json',
        'rgs_mkb/rgsmkb_all4EN.json',
        '../rgs_mkb/rgsmkb_all4EN.json'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"📊 Loading canonical RGS data from: {path}")
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    print("❌ ERROR: Could not find rgsmkb_all4EN.json")
    print("   Please ensure the canonical RGS data file is available")
    return None

def load_concept_mappings():
    """Load concept mappings from labels.csv (design requirement)"""
    labels_path = '20210913 RGS NL en EN labels.csv'
    
    if not os.path.exists(labels_path):
        print("⚠️  WARNING: Could not find labels.csv")
        print("   Proceeding without concept mappings")
        return {}
    
    print(f"🌍 Loading concept mappings from: {labels_path}")
    concept_map = {}
    
    with open(labels_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rgs_code = row.get('RGS code', '').strip()
            concept = row.get('Concept', '').strip()
            
            if rgs_code and concept:
                if rgs_code not in concept_map:
                    concept_map[rgs_code] = []
                concept_map[rgs_code].append(concept)
    
    print(f"   Loaded concept mappings for {len(concept_map)} RGS codes")
    return concept_map

def process_rgs_record_enhanced(record, mapper, concept_mappings):
    """
    Process single RGS record with enhanced mapping logic
    Aligned with design specification requirements
    """
    
    # Extract core RGS fields (design specification naming)
    rgs_code = record.get('rgsCode', '')  # Primary key
    rgs_reknr = str(record.get('rgsReknr', '0')).zfill(5)  # SME identifier (5 digits)
    rgs_omskort = record.get('rgsOmskort', '')  # SME description
    rgs_dc = record.get('rgsDc', '')  # Debit/Credit indicator
    rgs_omslag = record.get('rgsOmslag', '')  # Contra account reference
    rgs_nivo = record.get('rgsNivo', '')  # Hierarchy level
    
    # Get concept mappings for this RGS code
    concepts = concept_mappings.get(rgs_code, [])
    
    # Apply enhanced mapping logic
    root_type = mapper.determine_root_type(record, concepts)
    account_type = mapper.determine_account_type(record, root_type, concepts)
    report_type = mapper.determine_report_type(rgs_code)
    balance_must_be = mapper.map_balance_must_be(rgs_dc)
    
    # Determine if this is a group account (nivo < 5)
    try:
        nivo_int = int(str(rgs_nivo)) if rgs_nivo else 5
        is_group = nivo_int < 5  # Levels 1-4 are groups, level 5 are ledgers
    except (ValueError, TypeError):
        is_group = False
    
    # Find parent RGS code using hierarchy
    parent_rgs_code = find_parent_rgs_code(rgs_code) if rgs_code not in ['B', 'W'] else None
    
    # Build Frappe DocType record (design specification structure)
    frappe_record = {
        "doctype": "RGS Classification",
        "name": rgs_code,  # Primary key: official RGS classification
        
        # Core RGS fields (exact naming per design spec)
        "rgs_code": rgs_code,
        "rgs_reknr": rgs_reknr,
        "rgs_omskort": rgs_omskort,
        "rgs_dc": rgs_dc,
        "rgs_omslag": rgs_omslag,
        "rgs_nivo": rgs_nivo,
        
        # Tree structure
        "is_group": is_group,
        "parent_rgs_classification": parent_rgs_code,
        
        # Entity applicability (exact field names per design spec)
        "rgs_zzp": record.get('rgsZZP', 'N'),
        "rgs_ez": record.get('rgsEZ', 'N'),
        "rgs_bv": record.get('rgsBV', 'N'),
        "rgs_svc": record.get('rgsSVC', 'N'),
        
        # ERPNext integration fields (intelligently derived)
        "report_type": report_type,
        "root_type": root_type,
        "account_type": account_type,
        "balance_must_be": balance_must_be,
        
        # Metadata and traceability
        "rgs_status": record.get('rgsStatus', 'A'),
        "rgs_versie": record.get('rgsVersie', '3.7'),
        "concept_mappings": json.dumps(concepts) if concepts else "",
        
        # Administrative fields
        "rgs_sortering": record.get('rgsSortering', ''),
        "rgs_omslang": record.get('rgsOmslang', ''),
        "rgs_engels": record.get('rgsOmsEngels', ''),
        
        # Processing metadata
        "processed_timestamp": "2025-08-22",
        "processing_version": "enhanced_v1.0"
    }
    
    return frappe_record

def find_parent_rgs_code(rgs_code):
    """
    Find parent RGS code using hierarchical structure
    Design specification: parent references rgsCode (not rgsReknr)
    """
    if not rgs_code or rgs_code in ['B', 'W']:
        return None
    
    # RGS hierarchy: B → BIva → BIvaKou → BIvaKouOnd
    if len(rgs_code) <= 1:
        return None
    elif len(rgs_code) <= 4:
        return rgs_code[0]  # Return B or W
    else:
        # Remove last 3 characters for longer codes
        return rgs_code[:-3]

def process_all_rgs_data():
    """
    Main processing function implementing design specification requirements
    """
    print("🚀 Starting Enhanced RGS Data Processing")
    print("=" * 60)
    
    # Load all data sources
    canonical_data = load_rgs_canonical_data()
    if not canonical_data:
        return False
    
    concept_mappings = load_concept_mappings()
    
    # Initialize enhanced mapper
    mapper = RGSToERPNextMapper()
    
    # Process records in batches for memory efficiency
    batch_size = 100
    processed_records = []
    
    print(f"\n📈 Processing {len(canonical_data)} RGS records with enhanced mapping...")
    
    for i in range(0, len(canonical_data), batch_size):
        batch = canonical_data[i:i+batch_size]
        
        for record in batch:
            try:
                frappe_record = process_rgs_record_enhanced(
                    record, mapper, concept_mappings
                )
                processed_records.append(frappe_record)
                
            except Exception as e:
                rgs_code = record.get('rgsCode', 'UNKNOWN')
                print(f"⚠️  Error processing {rgs_code}: {e}")
                continue
        
        # Progress indicator
        progress = min(i + batch_size, len(canonical_data))
        print(f"  ✅ Processed {progress}/{len(canonical_data)} records")
    
    # Save corrected fixtures
    fixture_dir = Path('nl_erpnext_rgs_mkb/fixtures')
    fixture_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = fixture_dir / 'rgs_classification_corrected.json'
    
    print(f"\n💾 Saving {len(processed_records)} corrected RGS records...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_records, f, indent=2, ensure_ascii=False)
    
    # Generate processing report
    generate_processing_report(processed_records, output_file)
    
    print(f"✅ Enhanced RGS processing completed successfully!")
    print(f"   Output file: {output_file}")
    return True

def generate_processing_report(records, output_file):
    """Generate a report of the processing results"""
    
    # Count by root type
    root_type_counts = {}
    entity_counts = {'zzp': 0, 'ez': 0, 'bv': 0, 'svc': 0}
    
    for record in records:
        root_type = record.get('root_type', 'Unknown')
        root_type_counts[root_type] = root_type_counts.get(root_type, 0) + 1
        
        # Count entity applicability
        if record.get('rgs_zzp') == 'J':
            entity_counts['zzp'] += 1
        if record.get('rgs_ez') == 'J':
            entity_counts['ez'] += 1
        if record.get('rgs_bv') == 'J':
            entity_counts['bv'] += 1
        if record.get('rgs_svc') == 'J':
            entity_counts['svc'] += 1
    
    print(f"\n📊 Processing Report")
    print(f"   Total records: {len(records)}")
    print(f"   Root type distribution:")
    for root_type, count in sorted(root_type_counts.items()):
        print(f"     {root_type}: {count}")
    
    print(f"   Entity applicability:")
    for entity, count in entity_counts.items():
        print(f"     {entity.upper()}: {count}")

def main():
    """Main execution function"""
    try:
        success = process_all_rgs_data()
        if success:
            print("\n🎯 Next Steps:")
            print("   1. Review the generated fixture file")
            print("   2. Test the corrected mappings")
            print("   3. Update hooks.py to use corrected fixtures")
            print("   4. Rebuild Docker image with corrected data")
        else:
            print("\n❌ Processing failed. Please check the errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
