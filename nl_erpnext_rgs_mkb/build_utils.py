# Build-Time Fixture Processing for RGS MKB
# These functions run during Docker image build to optimize RGS fixtures
# and translations for faster production deployment

import frappe
import json
import csv
import os
from frappe.utils.caching import redis_cache

@frappe.whitelist()
def convert_rgs_fixtures_for_build():
    """
    Convert large RGS fixtures to optimized format during Docker build
    This runs in a temporary build site and pre-processes data for production
    """
    if not os.getenv('FIXTURE_BUILD_MODE'):
        frappe.throw("This function only runs during Docker build")
    
    print("🔄 Starting RGS fixture conversion for build optimization...")
    
    # Try to find RGS source data
    possible_paths = [
        '/opt/frappe_docker/rgs_mkb/rgsmkb_all4EN.json',
        frappe.get_app_path('nl_erpnext_rgs_mkb', 'data/rgsmkb_all4EN.json'),
        os.path.join(os.getcwd(), 'apps/nl_erpnext_rgs_mkb/data/rgsmkb_all4EN.json')
    ]
    
    canonical_path = None
    for path in possible_paths:
        if os.path.exists(path):
            canonical_path = path
            break
    
    if not canonical_path:
        print("⚠️  No RGS source data found, skipping fixture optimization")
        return False
    
    print(f"📊 Loading RGS data from: {canonical_path}")
    
    try:
        with open(canonical_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading RGS data: {e}")
        return False
    
    print(f"📈 Processing {len(raw_data)} RGS records...")
    
    # Process in optimized batches for build-time
    optimized_fixtures = []
    batch_size = 100  # Smaller batches for build stability
    
    for i in range(0, len(raw_data), batch_size):
        batch = raw_data[i:i+batch_size]
        try:
            processed_batch = process_rgs_batch_for_build(batch)
            optimized_fixtures.extend(processed_batch)
            
            # Progress indicator
            progress = min(i+batch_size, len(raw_data))
            print(f"  ✅ Processed {progress}/{len(raw_data)} RGS records")
            
        except Exception as e:
            print(f"⚠️  Error processing batch {i}-{i+batch_size}: {e}")
            continue
    
    # Save optimized fixtures
    try:
        fixture_dir = frappe.get_app_path('nl_erpnext_rgs_mkb', 'fixtures')
        if not os.path.exists(fixture_dir):
            os.makedirs(fixture_dir)
            
        optimized_path = os.path.join(fixture_dir, 'rgs_classification_optimized.json')
        
        with open(optimized_path, 'w', encoding='utf-8') as f:
            json.dump(optimized_fixtures, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(optimized_fixtures)} optimized fixtures to {optimized_path}")
        
        # Also save metadata about the optimization
        metadata = {
            "build_timestamp": frappe.utils.now(),
            "source_records": len(raw_data),
            "optimized_records": len(optimized_fixtures),
            "optimization_version": "1.0"
        }
        
        metadata_path = os.path.join(fixture_dir, 'rgs_optimization_metadata.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        print("✅ RGS fixture optimization completed successfully")
        return len(optimized_fixtures)
        
    except Exception as e:
        print(f"❌ Error saving optimized fixtures: {e}")
        return False

def process_rgs_batch_for_build(batch):
    """Process RGS batch with build-time optimizations"""
    processed = []
    
    for record in batch:
        try:
            # Basic validation
            rgs_code = record.get('rgsCode', '')
            if not rgs_code:
                continue
            
            # Apply three-document integration approach
            erpnext_mappings = derive_erpnext_mappings_build_time(record)
            
            # Build optimized fixture record
            fixture = {
                "doctype": "RGS Classification",
                "name": rgs_code,  # Primary key
                # Core RGS fields
                "rgs_code": rgs_code,
                "rgs_omskort": record.get('rgsOmskort', ''),
                "rgs_reknr": str(record.get('rgsReknr', '0')).zfill(5),
                "rgs_dc": record.get('rgsDc', ''),
                "rgs_nivo": record.get('rgsNivo'),
                "rgs_omslang": record.get('rgsOmslang', ''),
                "rgs_oms_engels": record.get('rgsOmsEngels', ''),
                "rgs_sortering": record.get('rgsSortering', ''),
                "rgs_omslag": record.get('rgsOmslag', ''),
                "rgs_referentienr": record.get('rgsReferentienr', ''),
                "rgs_branche": record.get('rgsBranche'),
                "rgs_status": record.get('rgsStatus', 'A'),
                "rgs_versie": record.get('rgsVersie', '3.7'),
                # Entity applicability
                "rgs_zzp": record.get('rgsZZP', 'N'),
                "rgs_ez": record.get('rgsEZ', 'N'),
                "rgs_bv": record.get('rgsBV', 'N'),
                "rgs_svc": record.get('rgsSVC', 'N'),
                "rgs_uitg": 1 if record.get('rgsUITG') == 'J' else 0,
                "srt_export": record.get('srtExport', ''),
                # Pre-calculated ERPNext fields (build-time optimization)
                "erpnext_report_type": erpnext_mappings.get('report_type'),
                "erpnext_root_type": erpnext_mappings.get('root_type'),
                "erpnext_account_type": erpnext_mappings.get('account_type'),
                # Hierarchy
                "parent_rgs_classification": find_parent_rgs_code(rgs_code),
                "is_group": determine_if_group(record.get('rgsNivo', 5)),
                # Build optimization flag
                "build_optimized": True
            }
            
            processed.append(fixture)
            
        except Exception as e:
            print(f"⚠️  Error processing record {record.get('rgsCode', 'unknown')}: {e}")
            continue
    
    return processed

def derive_erpnext_mappings_build_time(record):
    """Derive ERPNext mappings during build time"""
    rgs_code = record.get('rgsCode', '')
    
    # Basic report type mapping
    if rgs_code.startswith('B'):
        report_type = "Balance Sheet"
    elif rgs_code.startswith('W'):
        report_type = "Profit and Loss"
    else:
        report_type = "Balance Sheet"
    
    # Root type mapping based on RGS structure
    root_type = derive_root_type_from_rgs_code(rgs_code)
    
    # Account type mapping
    account_type = derive_account_type_from_rgs_code(rgs_code, root_type)
    
    return {
        'report_type': report_type,
        'root_type': root_type,
        'account_type': account_type
    }

def derive_root_type_from_rgs_code(rgs_code):
    """Map RGS code structure to ERPNext root types"""
    if rgs_code.startswith('B'):
        # Balance sheet codes
        if any(x in rgs_code for x in ['BIva', 'BMat', 'BFin']):
            return "Asset"
        elif any(x in rgs_code for x in ['BKor', 'BLan']):
            return "Liability"
        elif any(x in rgs_code for x in ['BEig']):
            return "Equity"
        else:
            return "Asset"  # Default for balance sheet
    elif rgs_code.startswith('W'):
        # P&L codes
        if any(x in rgs_code for x in ['WOmz', 'WBat']):
            return "Income"
        else:
            return "Expense"
    else:
        return "Asset"  # Conservative default

def derive_account_type_from_rgs_code(rgs_code, root_type):
    """Map to specific ERPNext account types"""
    # Specific mappings based on RGS patterns
    if 'Bank' in rgs_code or rgs_code.endswith('Kas'):
        return "Bank"
    elif 'Deb' in rgs_code:
        return "Receivable"
    elif 'Crd' in rgs_code:
        return "Payable"
    elif root_type == "Asset" and any(x in rgs_code for x in ['BIva', 'BMat']):
        return "Fixed Asset"
    elif root_type == "Income":
        return "Income Account"
    elif root_type == "Expense":
        return "Expense Account"
    else:
        # Fallback mapping
        fallback_mapping = {
            'Asset': 'Fixed Asset',
            'Liability': 'Payable',
            'Equity': 'Equity',
            'Income': 'Income Account',
            'Expense': 'Expense Account'
        }
        return fallback_mapping.get(root_type, 'Fixed Asset')

def find_parent_rgs_code(rgs_code):
    """Find parent using RGS hierarchical structure"""
    if len(rgs_code) <= 1 or rgs_code in ['B', 'W']:
        return None  # Root level
    
    # Remove last 3-character segment for parent
    if len(rgs_code) <= 4:
        return rgs_code[0]  # Return B or W
    else:
        return rgs_code[:-3]  # Remove last group

def determine_if_group(nivo):
    """Determine if record is a group based on nivo"""
    try:
        level = int(nivo) if nivo else 5
        return 1 if level < 5 else 0
    except (ValueError, TypeError):
        return 0

@frappe.whitelist()
def setup_rgs_translations():
    """Generate translation files during build phase"""
    if not os.getenv('FIXTURE_BUILD_MODE'):
        frappe.throw("This function only runs during Docker build")
    
    print("🌍 Setting up RGS translations during build...")
    
    # Try to find translation source
    possible_paths = [
        '/opt/frappe_docker/rgs_mkb/20210913 RGS NL en EN labels.csv',
        frappe.get_app_path('nl_erpnext_rgs_mkb', '20210913 RGS NL en EN labels.csv'),
        os.path.join(os.getcwd(), 'apps/nl_erpnext_rgs_mkb/20210913 RGS NL en EN labels.csv')
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        print("⚠️  RGS translation CSV not found, skipping translation setup")
        return False
    
    print(f"📄 Loading translations from: {csv_path}")
    
    try:
        # Create translations directory
        translations_dir = frappe.get_app_path('nl_erpnext_rgs_mkb', 'translations')
        if not os.path.exists(translations_dir):
            os.makedirs(translations_dir)
        
        # Process translations
        nl_translations = {}
        en_translations = {}
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                try:
                    omschrijving = row.get('Omschrijving RGS', '').strip()
                    en_label = row.get('EN Label', '').strip()
                    nl_label = row.get('NL Label', '').strip()
                    
                    if omschrijving and en_label:
                        # Map Dutch descriptions to English
                        en_translations[omschrijving] = en_label
                    
                    if en_label and nl_label:
                        # Map English labels to Dutch
                        nl_translations[en_label] = nl_label
                    
                    count += 1
                    if count % 1000 == 0:
                        print(f"  ✅ Processed {count} translation entries")
                        
                except Exception as e:
                    print(f"⚠️  Error processing translation row: {e}")
                    continue
        
        # Save translation files
        nl_file = os.path.join(translations_dir, 'nl.csv')
        en_file = os.path.join(translations_dir, 'en.csv')
        
        # Save Dutch translations
        with open(nl_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for source, translation in nl_translations.items():
                writer.writerow([source, translation])
        
        # Save English translations  
        with open(en_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            for source, translation in en_translations.items():
                writer.writerow([source, translation])
        
        print(f"💾 Generated {len(nl_translations)} Dutch and {len(en_translations)} English translations")
        print("✅ RGS translations setup completed")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up translations: {e}")
        return False

@frappe.whitelist()
def load_optimized_rgs_fixtures():
    """Load pre-processed RGS fixtures in production site"""
    print("📊 Loading optimized RGS fixtures...")
    
    try:
        # Check if optimized fixtures exist
        fixture_path = frappe.get_app_path('nl_erpnext_rgs_mkb', 'fixtures/rgs_classification_optimized.json')
        
        if not os.path.exists(fixture_path):
            print("⚠️  Optimized fixtures not found, falling back to standard loading")
            return frappe.get_attr('nl_erpnext_rgs_mkb.utils.load_standard_rgs_fixtures')()
        
        with open(fixture_path, 'r', encoding='utf-8') as f:
            fixtures = json.load(f)
        
        # Load fixtures in batches for production stability
        batch_size = 100
        loaded_count = 0
        
        for i in range(0, len(fixtures), batch_size):
            batch = fixtures[i:i+batch_size]
            
            for fixture in batch:
                try:
                    if not frappe.db.exists("RGS Classification", fixture["name"]):
                        doc = frappe.get_doc(fixture)
                        doc.flags.ignore_permissions = True
                        doc.insert()
                        loaded_count += 1
                except Exception as e:
                    print(f"⚠️  Error loading fixture {fixture.get('name', 'unknown')}: {e}")
                    continue
            
            # Commit each batch
            frappe.db.commit()
            
            # Progress indicator
            progress = min(i+batch_size, len(fixtures))
            print(f"  ✅ Loaded {progress}/{len(fixtures)} RGS classifications")
        
        print(f"✅ Loaded {loaded_count} optimized RGS fixtures successfully")
        return loaded_count
        
    except Exception as e:
        print(f"❌ Error loading optimized fixtures: {e}")
        return False

@frappe.whitelist()
def activate_rgs_translations():
    """Activate pre-processed RGS translations"""
    print("🌍 Activating RGS translations...")
    
    try:
        translations_dir = frappe.get_app_path('nl_erpnext_rgs_mkb', 'translations')
        
        if not os.path.exists(translations_dir):
            print("⚠️  Translation files not found, skipping activation")
            return False
        
        # Check available translation files
        available_translations = []
        for lang in ['nl', 'en']:
            file_path = os.path.join(translations_dir, f'{lang}.csv')
            if os.path.exists(file_path):
                available_translations.append(lang)
        
        if available_translations:
            print(f"✅ RGS translations available for: {', '.join(available_translations)}")
            
            # Set configuration to indicate translations are available
            frappe.db.set_value("System Settings", None, "rgs_translations_available", 1)
            frappe.db.commit()
            
            return True
        else:
            print("⚠️  No translation files found")
            return False
            
    except Exception as e:
        print(f"❌ Error activating translations: {e}")
        return False

@frappe.whitelist()
def verify_rgs_installation():
    """Verify that RGS installation completed successfully"""
    print("🔍 Verifying RGS installation...")
    
    try:
        # Check if RGS Classification DocType exists
        if not frappe.db.exists("DocType", "RGS Classification"):
            print("❌ RGS Classification DocType not found")
            return False
        
        # Check if any RGS classifications were loaded
        rgs_count = frappe.db.count("RGS Classification")
        print(f"📊 Found {rgs_count} RGS classifications")
        
        if rgs_count == 0:
            print("⚠️  No RGS classifications found")
            return False
        
        # Check if translations are available
        translations_available = frappe.db.get_single_value("System Settings", "rgs_translations_available")
        if translations_available:
            print("🌍 RGS translations are available")
        else:
            print("⚠️  RGS translations not available")
        
        # Check optimization status
        optimized_count = frappe.db.count("RGS Classification", {"build_optimized": 1})
        if optimized_count > 0:
            print(f"🚀 {optimized_count} optimized RGS records detected")
        
        print("✅ RGS installation verification completed")
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False
