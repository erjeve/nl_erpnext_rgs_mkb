# Dutch RGS MKB App - Design Specification

**Version:** 2.0  
**Date:** August 21, 2025  
**Purpose:** ERPNext app for Dutch RGS 3.7+ compliance and Chart of Accounts management with forward compatibility

## Table of Contents
1. [AI Development Kickstart Guide](#ai-development-kickstart-guide)
2. [Project Overview](#project-overview)
3. [Development Workflow](#development-workflow)
4. [RGS System Architecture](#rgs-system-architecture)
5. [Core Concept](#core-concept)
6. [Data Architecture](#data-architecture)
7. [User Experience](#user-experience)
8. [Technical Implementation](#technical-implementation)
9. [Modern Frappe Framework Integration](#modern-frappe-framework-integration)
10. [Business Value](#business-value)
11. [Development Phases](#development-phases)
12. [Success Criteria](#success-criteria)

---

## AI Development Kickstart Guide

### Context Setting for AI Assistant

You are an expert AI programming assistant specializing in **Dutch RGS MKB compliance** for ERPNext. Your primary mission is to develop a production-ready Frappe app that enables Dutch SMEs to achieve legal compliance with RGS (Referentiegrootboekschema) 3.7+ standards.

#### Critical Understanding Requirements

**1. Dutch Legal Context:**
- RGS is **mandatory** for Dutch financial reporting
- RGS MKB is the SME subset from ~5,000 RGS account codes
- Legal compliance is non-negotiable - accuracy is paramount
- Account classification directly impacts tax and legal reporting

**2. RGS Data Structure (MEMORIZE THIS):**
```
PRIMARY KEY: rgsCode (official classification, hierarchical)
- Examples: "B", "BIva", "BIvaKou", "WAkfAkf"
- Used for: Official classification, parent-child relationships
- When the rgsCode starts with "B" it is a balance account
- When the rgsCode starts with "W" it is a profit and loss account
- Hierarchy: indicated by 3-letter-acroniem-based groups (B→BIva→BIvaKou→BIvaKouOnd) 
- Each new level added to the hierarchical code starts with a capital

USER IDENTIFIERS: rgsReknr + rgsOmskort (SME-friendly)
- rgsReknr: "01000", "10101", "45105" (5-digit decimal, stable forever)
- rgsOmskort: "Bank lopende rekening", "Kas" (Dutch account names)
- Used for: ERPNext account_number and account_name

CRITICAL: rgsCode = primary key, rgsReknr = user interface
```

**3. ERPNext Integration Points:**
- Account DocType: Enhanced with RGS custom fields
- Chart of Accounts: RGS-compliant templates (ZZP, BV, EZ, SVC)
- Fixtures: Large dataset (~5,000 records) requiring Redis optimization
- Hierarchical Structure: Tree-based using rgsCode relationships

### Required Files for Clean Start

#### Essential Repository Files
```bash
# Core app structure
/nl_erpnext_rgs_mkb/
├── __init__.py
├── hooks.py                    # Frappe app configuration
├── modules.txt                 # Module definition
├── setup.py                   # Package setup
├── requirements.txt            # Python dependencies
├── package.json               # Node dependencies
├── pyproject.toml             # Modern Python packaging
├── RGS_MKB_DESIGN_SPECIFICATION.md  # THIS DOCUMENT (critical!)
└── nl_erpnext_rgs_mkb/
    ├── __init__.py
    ├── account_validation.py   # RGS compliance validation
    ├── utils.py                # Helper functions
    ├── config/
    │   └── desktop.py          # Dashboard integration
    ├── fixtures/
    │   ├── custom_field.json   # ERPNext Account enhancements
    │   └── rgs_classification.json  # RGS master data (large!)
    ├── doctype/
    │   ├── rgs_classification/
    │   │   ├── rgs_classification.json
    │   │   ├── rgs_classification.py
    │   │   └── rgs_classification.js
    │   └── rgs_template/
    │       ├── rgs_template.json
    │       ├── rgs_template.py
    │       └── rgs_template.js
    └── public/
        ├── css/app.css
        └── js/index.js
```

#### Critical Data Files
```bash
# RGS master data (external, required for processing)
/rgs_data/
├── rgsmkb_all4EN.json        # Canonical RGS MKB 3.7 dataset (~33,560 lines)
├── attributes.csv            # Official field explanation and mapping proposal
├── 20210913 RGS NL en EN labels.csv  # Official translation/concept mappings
├── rgs-definitions.json      # rgs accounts (derived from rgsmkb_all4EN.json)
├── export_zzp_standard.json  # ZZP template (derived from rgsmkb_all4EN.json)
├── export_bv_standard.json   # BV template  (derived from rgsmkb_all4EN.json) 
├── export_ez_standard.json   # EZ template  (derived from rgsmkb_all4EN.json) 
└── export_svc_standard.json  # SVC template (derived from rgsmkb_all4EN.json) 
```

### AI Task Specialization

#### Primary Competencies Required
1. **Frappe Framework Expertise** (Version 15+)
   - DocType creation and relationships
   - Custom field integration
   - Fixture loading and optimization
   - Tree DocType hierarchies
   - Modern framework patterns

2. **Dutch Accounting Knowledge**
   - RGS classification system understanding
   - correct mapping of RGS accounts to ERPNEXT's root_type, account_type
   - SME legal requirements (ZZP, BV, EZ, SVC)
   - Dutch GAAP compliance
   - Multi-member entity accounting (cooperatives, VOF)

3. **ERPNext Integration**
   - Chart of Accounts customization
   - Account DocType enhancement
   - Template creation and management
   - Financial reporting compliance

4. **Performance Optimization**
   - Large dataset handling (5,000+ records)
   - Redis cache optimization
   - Docker deployment efficiency
   - Database performance tuning

### Development Environment Setup

#### Quick Start Commands
```bash
# 1. Repository setup
git clone https://github.com/erjeve/nl_erpnext_rgs_mkb.git
cd nl_erpnext_rgs_mkb

# 2. Read the design specification FIRST
cat RGS_MKB_DESIGN_SPECIFICATION.md  # CRITICAL - contains all context

# 3. Understand the data structure
head -50 /rgs_data/attributes.csv     # Official field mappings
head -20 /rgs_data/rgsmkb_all4EN.json # Sample RGS data

# 4. Frappe app setup (if using bench)
bench get-app https://github.com/erjeve/nl_erpnext_rgs_mkb.git
bench install-app nl_erpnext_rgs_mkb --site your-site

# 5. Docker setup (production-style)
# Add to apps.json in frappe_docker
# Build with: docker buildx bake custom --set custom.args.APPS_JSON_BASE64=$(base64 -w 0 apps.json)
```

### Critical Implementation Guidelines

#### 1. Data Structure Principles
```python
# ALWAYS remember the hierarchy
def find_parent_rgs_code(rgs_code):
    """
    rgsCode hierarchy: B → BIva → BIvaKou → BIvaKouOnd
    Parent is found by removing last 3-character group
    """
    if len(rgs_code) <= 1 or rgs_code in ['B', 'W']:
        return None  # Root level
    
    # Remove last 3-character segment for parent
    if len(rgs_code) <= 4:
        return rgs_code[0]  # Return B or W
    else:
        return rgs_code[:-3]  # Remove last group

# ALWAYS use rgsCode as primary key
doctype_definition = {
    "name": rgs_code,  # PRIMARY KEY
    "account_number": rgs_reknr,  # User interface
    "account_name": rgs_omskort,  # User interface
    "parent_rgs_classification": parent_rgs_code  # Hierarchy
}
```

#### 2. Performance Optimization Patterns
```python
# Large fixture loading with Redis optimization
def optimize_for_large_datasets():
    """
    CRITICAL: 5,000+ RGS records require special handling
    """
    import frappe
    
    # Pre-warm Redis cache
    redis_client = frappe.cache()
    redis_client.config_set('maxmemory-policy', 'allkeys-lru')
    
    # Batch processing (max 500 records per batch)
    batch_size = 500
    
    # Clear cache periodically during import
    if record_count % 2000 == 0:
        frappe.clear_cache()
```

#### 3. Legal Compliance Validation
```python
# NEVER compromise on RGS compliance
def validate_rgs_compliance(account_doc):
    """
    Mandatory validation for Dutch legal compliance
    """
    # Ensure RGS classification exists
    if not account_doc.rgs_classification:
        frappe.throw("RGS classification is mandatory for Dutch entities")
    
    # Validate account number format
    if not re.match(r'^\d{5}$', account_doc.account_number):
        frappe.throw("Account number must be 5-digit RGS format")
    
    # Ensure hierarchy compliance
    validate_parent_child_relationship(account_doc)
```

### Common Pitfalls to Avoid

#### 1. **WRONG: Using rgsReknr as primary key**
```python
# DON'T DO THIS
naming_rule: "rgsReknr"  # Wrong - this is for user interface only
```

#### 2. **WRONG: Mixing up hierarchy references**
```python
# DON'T DO THIS
parent_rgs_classification: rgs_reknr  # Wrong - use rgsCode for hierarchy
```

#### 3. **WRONG: Ignoring performance optimization**
```python
# DON'T DO THIS - will cause memory overflow
for record in all_5000_rgs_records:
    frappe.get_doc("RGS Classification", record).insert()
```

### Debugging and Troubleshooting

#### Common Issues and Solutions
```bash
# 1. Fixture loading fails
Error: "Memory exceeded during fixture import"
Solution: Implement batch processing + Redis optimization

# 2. Hierarchy not working
Error: "Parent account not found"
Solution: Check rgsCode hierarchy logic, ensure parents created first

# 3. Docker build fails
Error: "App not found in container"
Solution: Verify apps.json path and base64 encoding

# 4. Account validation errors
Error: "RGS compliance validation failed"
Solution: Check custom field mapping from attributes.csv
```

### AI Decision Making Framework

#### When Implementing Features:
1. **Legal compliance FIRST** - always check Dutch requirements
2. **Performance SECOND** - consider 5,000+ record implications  
3. **User experience THIRD** - SME-friendly interfaces
4. **Future compatibility FOURTH** - RGS 3.8+ preparation

#### Priority Matrix:
```
HIGH PRIORITY:
- RGS compliance accuracy
- Data integrity 
- Performance with large datasets
- Legal audit trail

MEDIUM PRIORITY:
- User interface enhancements
- Template customization
- Multi-member accounting
- Reporting features

LOW PRIORITY:
- Advanced visualizations
- Non-essential integrations
- Experimental features
```

### Success Criteria for AI

Your implementation is successful when:
1. ✅ All 5,000+ RGS codes load without memory issues
2. ✅ Account hierarchy displays correctly (B→BIva→BIvaKou)
3. ✅ Dutch SME can create legally compliant Chart of Accounts
4. ✅ Templates work for all entity types (ZZP, BV, EZ, SVC)
5. ✅ Performance remains acceptable with full dataset
6. ✅ Compliance validation prevents legal errors
7. ✅ Multi-member accounting works for cooperatives/VOF

### Resource References

#### Documentation Priority:
1. **THIS DOCUMENT** - Complete specification and context
2. **attributes.csv** - Authoritative field mappings  
3. **Frappe Documentation** - Framework patterns
4. **ERPNext Accounting** - Integration points
5. **Dutch RGS Standards** - Legal requirements

#### Code Patterns:
```python
# Study existing implementations in:
- /nl_erpnext_rgs_mkb/doctype/rgs_classification/
- /nl_erpnext_rgs_mkb/account_validation.py
- /nl_erpnext_rgs_mkb/fixtures/

# Follow established patterns for:
- DocType relationships
- Custom field integration  
- Fixture loading optimization
- Validation implementation
```

---

## Development Workflow

### Infrastructure Overview

The RGS MKB app development utilizes a sophisticated multi-VPS architecture designed for production-ready deployment with development flexibility:

#### VPS Architecture
```
Production VPS: frappe.fivi.eu
├── /opt/frappe_docker/ (Production deployment)
│   ├── Source: https://github.com/frappe/frappe_docker
│   ├── Extensions: Invoice parsing microservices (invoice2data integration)
│   ├── Database: Persistent bind mounts (production-ready)
│   ├── Stack: Sophisticated upstream adaptability with flexible customization
│   └── Status: Production-ready but no actual business data yet
│
├── /tmp/nl_erpnext_rgs_mkb/ (Local development)
│   ├── Local Git repository for active development
│   ├── Remote: https://github.com/erjeve/nl_erpnext_rgs_mkb
│   ├── IDE: VSCode remote development
│   └── Status: Active development and testing
│
└── Optional: Separate VPS for clean development
    ├── Cleaner ERPNext implementation
    ├── Dedicated RGS MKB development environment
    └── Isolated from production complexity
```

### Development Workflow

#### 1. Remote Development Setup
```bash
# Connect via VSCode Remote SSH
code --remote ssh-remote+frappe.fivi.eu /tmp/nl_erpnext_rgs_mkb

# Local development environment
cd /tmp/nl_erpnext_rgs_mkb
git status
git pull origin main
```

#### 2. Development Cycle
```bash
# Development workflow
1. Edit code in VSCode (remote)
2. Test locally in /tmp/nl_erpnext_rgs_mkb
3. Commit and push to GitHub
4. Deploy to /opt/frappe_docker production stack

# Git workflow
git add -A
git commit -m "Feature: Description"
git push origin main
```

#### 3. Deployment Pipeline
```bash
# GitHub-based deployment workflow

# 1. Development and push to GitHub
cd /tmp/nl_erpnext_rgs_mkb
git add -A
git commit -m "Feature: Description"
git push origin main

# 2. Update apps.json with GitHub URL (production deployment)
cd /opt/frappe_docker
cat > apps.json << EOF
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/erjeve/nl_erpnext_rgs_mkb",
    "branch": "main"
  }
]
EOF

# 3. Build from GitHub source
base64 -w 0 apps.json
docker buildx bake custom --no-cache --set custom.args.APPS_JSON_BASE64=$(base64 -w 0 apps.json)

# 4. Deploy with profile
docker compose down
docker compose --profile rgs up -d
```

#### Development vs Production Apps.json
```bash
# Development (local path for rapid iteration)
apps_dev.json:
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"
  },
  {
    "url": "/tmp/nl_erpnext_rgs_mkb",
    "branch": "main"
  }
]

# Production (GitHub URL for stable deployment)
apps.json:
[
  {
    "url": "https://github.com/frappe/erpnext", 
    "branch": "version-15"
  },
  {
    "url": "https://github.com/erjeve/nl_erpnext_rgs_mkb",
    "branch": "main"
  }
]
```

### Production Stack Integration

#### Frappe Docker Extensions
```yaml
# Enhanced /opt/frappe_docker with:
services:
  # Core Frappe/ERPNext stack (upstream)
  backend:
    # RGS MKB app integrated
  
  # Invoice parsing microservices
  invoice-parser:
    # Similar to https://github.com/invoice-x/invoice2data
    # Automatic invoice data extraction
    # Integration with ERPNext Purchase Invoice
  
  ocr-service:
    # Document digitization
    # Integration with RGS account classification
  
  # Additional microservices for business automation
```

#### Database Management
```bash
# Persistent storage using bind mounts
/opt/frappe_docker/volumes/
├── db-data/          # MariaDB persistent data
├── redis-data/       # Redis cache and sessions
├── sites/            # ERPNext sites data
└── logs/             # Application logs

# Clean slate procedures (when needed)
docker compose down -v  # Remove all volumes
rm -rf volumes/         # Clean persistent data
# Requires thorough cleanup for fresh start
```

### Performance Optimization

#### Redis Cache Management for Large Fixtures
```python
# Performance optimization for large RGS datasets
import frappe
import redis

def optimize_rgs_fixture_loading():
    """
    Active Redis cache tweaking for large RGS fixtures
    Especially important for 5,000+ RGS classification records
    """
    # Get Redis connection
    redis_client = frappe.cache()
    
    # Pre-warm cache for RGS master data
    if not redis_client.exists("rgs_classification_cache"):
        rgs_data = frappe.get_all("RGS Classification", 
                                  fields=["rgs_code", "rgs_reknr", "rgs_omskort"],
                                  limit=None)
        
        # Cache RGS lookup data for 24 hours
        redis_client.setex("rgs_classification_cache", 86400, 
                          frappe.as_json(rgs_data))
    
    # Optimize memory usage during fixture import
    redis_client.config_set('maxmemory-policy', 'allkeys-lru')
    redis_client.config_set('maxmemory', '512mb')
    
    return True

# Usage during fixture loading
@frappe.whitelist()
def import_large_rgs_fixtures():
    """Enhanced fixture import with Redis optimization"""
    optimize_rgs_fixture_loading()
    
    # Import in batches to prevent memory overflow
    batch_size = 500
    fixture_path = 'nl_erpnext_rgs_mkb/fixtures/rgs_classification.json'
    
    with open(frappe.get_app_path('nl_erpnext_rgs_mkb', fixture_path)) as f:
        data = json.load(f)
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        process_rgs_batch(batch)
        frappe.db.commit()  # Commit each batch
        
        # Clear cache periodically
        if i % 2000 == 0:
            frappe.clear_cache()
```

#### Docker Performance Tuning
```yaml
# docker-compose.override.yml for development
services:
  backend:
    environment:
      # Increase memory limits for large fixtures
      - FRAPPE_MEMORY_LIMIT=2G
      - REDIS_CACHE_MAXMEMORY=512mb
    volumes:
      # Development bind mount
      - /tmp/nl_erpnext_rgs_mkb:/home/frappe/frappe-bench/apps/nl_erpnext_rgs_mkb
  
  redis-cache:
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    
  redis-queue:
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Migration and Maintenance Strategy

#### Clean Development Environment
```bash
# Option 1: Clean slate on same VPS
cd /opt/frappe_docker
docker compose down -v
sudo rm -rf volumes/
git pull  # Update base frappe_docker
# Rebuild from scratch

# Option 2: Separate development VPS
# Cleaner ERPNext implementation
# Dedicated RGS MKB development
# No production complexity interference
```

#### Data Migration Workflow
```python
# Production-safe migration procedures
def migrate_rgs_data():
    """
    Safe migration with rollback capability
    """
    # 1. Backup current state
    frappe.utils.backup.new_backup(
        ignore_files=False,
        backup_path_db="/opt/backups/pre_rgs_migration.sql",
        backup_path_files="/opt/backups/pre_rgs_migration_files.tar"
    )
    
    # 2. Test migration in isolation
    test_migration_compatibility()
    
    # 3. Execute migration with progress tracking
    migrate_with_progress_tracking()
    
    # 4. Validate post-migration state
    validate_rgs_compliance()
    
    return True
```

### Integration Points

#### Upstream Compatibility
```yaml
# Maintains frappe_docker upstream adaptability
git_strategy:
  upstream: https://github.com/frappe/frappe_docker
  local_branch: rgs_production
  merge_strategy: rebase_upstream
  
custom_services:
  - invoice_parser
  - ocr_service  
  - rgs_compliance_checker
  
preservation:
  - Original Docker architecture
  - Standard Frappe deployment patterns
  - ERPNext upgrade compatibility
```

#### Business Process Integration
```
RGS MKB App Integration Points:
├── Chart of Accounts (Core ERPNext)
├── Invoice Processing (Custom microservice)
├── Tax Compliance (Netherlands localization)
├── Financial Reporting (RGS-compliant)
└── Audit Trail (Legal requirement compliance)
```

### Best Practices

#### Development Guidelines
```bash
# 1. Always develop in /tmp/nl_erpnext_rgs_mkb first
# 2. Test with local Docker before production deployment
# 3. Use Redis cache optimization for large datasets
# 4. Maintain database backup before major changes
# 5. Preserve upstream frappe_docker compatibility
# 6. Document all customizations and integrations
```

#### Production Deployment Checklist
```
□ Code tested in development environment
□ Database backup completed
□ Redis cache optimized for large fixtures
□ Docker build successful without errors
□ Apps.json updated with correct references
□ Stack deployed with appropriate profile
□ RGS compliance validation passed
□ Performance benchmarks met
□ Rollback procedure documented
```

---

## Project Overview

### What is RGS?
The **Referentiegrootboekschema (RGS)** is the Dutch national standard for Chart of Accounts classification, mandated for legal financial reporting. The current RGS 3.7 contains approximately 5,000 predefined account codes, with RGS 3.8 already in development.

### What is RGS MKB?
**RGS MKB (Midden- en Kleinbedrijf)** is the SME subset developed by GBNED and adopted in the official standard. It provides:
- **Stable 5-digit decimal scheme** (`rgsReknr`) that remains unchanged across RGS versions
- **Entity-specific selections** for different legal forms (ZZP, BV, EZ, SVC)
- **Compliance mapping** for legal reporting requirements (IB/VPB, BTW, KvK, CBS)

### Problem Statement
Dutch businesses using ERPNext need:
- **Legal compliance** with mandatory RGS reporting requirements
- **Version-resilient** Chart of Accounts that survives RGS updates
- **Entity-specific templates** for different legal forms
- **Account extensibility** for business-specific sub-ledgers (e.g., multiple bank accounts)
- **Future-proof** integration with RGS 3.8+ standards

### App Purpose
Provide seamless RGS integration with ERPNext's Chart of Accounts system, ensuring:
- **Automatic compliance** with Dutch financial reporting
- **Forward compatibility** with evolving RGS standards
- **Business flexibility** through account extensions
- **Legal auditability** through complete RGS traceability

---

## RGS System Architecture

### RGS Code Structure
RGS uses a sophisticated multi-level identification system:

#### 1. **rgsCode** (Primary Classification) ⭐ **PRIMARY KEY**
```
Format: Letter-based hierarchical codes
Examples: 
- 'B' (Balance Sheet root)
- 'BIva' (Intangible Fixed Assets)
- 'WAkfAkf' (Specific P&L account)

Characteristics:
- Hierarchical structure using letter groups
- Stable across RGS versions (existing codes don't change)
- New codes may be added in future versions
- Used for RGS compliance mapping
```

#### 2. **rgsReferentienr** (Reference Number) 
```
Format: Numeric reference with optional extensions
Examples:
- "1010" (Basic reference)
- "1010.001" (Extension with period separator)
- "1010:IBAN" (Extension with colon separator)

Characteristics:
- May change between RGS versions
- Used for cross-referencing
- Not suitable as primary ERPNext identifier
- Stored for reference and compliance only
```

#### 3. **rgsReknr** (Decimal Account Number) 
```
Format: 5-digit decimal number (stable across versions)
Examples:
- "01000" (Formatted with leading zero)
- "10101" (Cash account)
- "45105" (Rent expense)

Characteristics:
- Stable across ALL RGS versions (3.7 → 3.8 → future)
- Used as ERPNext account_number
- Some legacy data has 4 digits - requires zero-padding
- Primary integration point with ERPNext
```

#### 4. **rgsOmskort** (Account Name)
```
Format: Dutch account description
Purpose: Used as ERPNext account_name
Translation: English descriptions available for international use
```

### RGS Version Evolution
```
RGS 3.7 (Current)    → RGS 3.8 (Development) → RGS 4.0 (Future)
├── Stable: rgsReknr ✅ (Never changes)
├── Stable: rgsCode  ✅ (Existing codes preserved)  
├── May change: rgsReferentienr ⚠️ (Reference only)
└── Versioned: rgsVersie (Historical compliance)
```

---

## Core Concept

### ❌ What RGS is NOT:
- User-creatable account classifications
- Customizable accounting taxonomies  
- Company-specific account hierarchies
- Editable reference data

### ✅ What RGS IS:
- **National standard** defined by Dutch authorities
- **Evolving framework** (3.7 → 3.8 → future versions)
- **Read-only master data** with version-stable identifiers
- **Selection-based system** where users choose relevant codes
- **Extensible framework** allowing business-specific sub-accounts

### Key Principles

#### 1. **Selection, Not Creation**
Users select appropriate RGS codes for their business rather than creating classifications.

#### 2. **Version Resilience**
Using `rgsReknr` as the primary identifier ensures Chart of Accounts survives RGS updates.

#### 3. **Business Extensibility** 
```
Example: Bank Account Extensions
Base RGS: 10101 - "Bank current account"
Extensions:
├── 10101.NL91ABNA0417164300 - "ABN AMRO Main Account"
├── 10101.NL91RABO0315273637 - "Rabobank Savings"
└── 10101.NL26INGB0002445588 - "ING Business Account"
```

#### 4. **Compliance Traceability**
Every account maintains full RGS lineage for audit and reporting requirements.

---

## Data Sources Integration

### Three-Document Architecture
The RGS MKB implementation leverages three complementary data sources for complete coverage:

#### 1. **Canonical Data Source**
```
File: /opt/frappe_docker/rgs_mkb/rgsmkb_all4EN.json
Purpose: Complete RGS MKB dataset with all account records
Content: ~5,000 RGS codes with full attribute data
Usage: Primary data source for RGS Classification DocType
```

#### 2. **Field Specifications**  
```
File: /opt/frappe_docker/rgs_mkb/attributes.csv
Purpose: Official field definitions and ERPNext mappings
Content: JSON attribute → ERPNext field → Frappe characteristics
Usage: Schema definition for DocType fields and data conversion
Key Mappings:
├── rgsCode → custom_rgsCode (Read-Only, Unique, Searchable)
├── rgsOmskort → account_name (Translatable)  
├── rgsReknr → account_number (5-digit decimal)
├── rgsDc → balance_must_be (Debit/Credit selection)
└── Entity flags → applicability indicators (ZZP/BV/EZ/SVC)
```

#### 3. **Translation & Legal Basis**
```
File: /tmp/nl_erpnext_rgs_mkb/20210913 RGS NL en EN labels.csv
Purpose: Translation mappings and legal framework references
Content: RGS code → Concept → Legal basis → NL/EN labels
Usage: Intelligent ERPNext account classification
Legal Framework:
├── jenv-bw2-i_Assets → Legal basis for asset classification
├── jenv-bw2-i_Liabilities → Legal basis for liability classification
├── bd-i_* → Tax/fiscal reporting requirements
└── rj-i_* → Financial reporting standards
```

### Integration Workflow
```python
Step 1: Load canonical data (rgsmkb_all4EN.json)
Step 2: Apply field specifications (attributes.csv) 
Step 3: Enhance with translation concepts (labels.csv)
Step 4: Generate intelligent ERPNext mappings
Step 5: Create Frappe fixtures with complete metadata
```

This three-source approach ensures:
- ✅ **Completeness**: All RGS data properly captured
- ✅ **Compliance**: Official field mappings maintained  
- ✅ **Intelligence**: Legal basis drives ERPNext classification
- ✅ **Multilingual**: Dutch/English translation support
- ✅ **Traceability**: Legal framework references preserved

---

### 1. RGS Master Data (Read-Only)
```
Source: /opt/frappe_docker/rgs_mkb/rgsmkb_all4EN.json
Content: Complete RGS 3.7 dataset (~5,000 codes)
Structure: Hierarchical (1st, 2nd, 3rd level codes)
Access: Read-only reference data
Usage: Source for account selection
```

### 2. Entity-Specific Templates
```
ZZP Template: coa_zzp_standard.json (Sole Trader)
BV Template:  export_bv_standard.json (Private Limited Company)
EZ Template:  export_ez_standard.json (One-person Company)  
SVC Template: export_svc_standard.json (Foundation, Association, Cooperative, VOF)
```

Note: The SVC template provides the foundation for multi-member entities including:
- **Coöperaties** (Cooperatives) - with member equity and profit sharing
- **VOF** (General Partnerships) - with partner current accounts
- **Associations** - with member dues and reserves
- **Foundations** - with restricted and unrestricted funds

### 3. ERPNext Integration Points
- **Chart of Accounts Template**: Standard ERPNext CoA creation
- **Account DocType**: Enhanced with RGS compliance fields
- **Company Setup**: RGS template selection during company creation
- **Reporting**: RGS-compliant financial statements

### 4. Field Mapping Strategy

#### RGS → ERPNext Account Mapping (Official Specification)
```
JSON Field         → ERPNext Field           → Frappe Characteristics
──────────────────────────────────────────────────────────────────────
rgsCode            → custom_rgsCode          → Read-Only, Unique, Searchable, Mandatory (Data)
rgsOmskort         → account_name            → Translatable (Data)
rgsReknr           → account_number          → 5-digit decimal number (Data)
rgsDc              → balance_must_be         → Selection: null/Debit/Credit
rgsNivo            → custom_rgs_Nivo         → Int (1=Balance/P&L, 2=Main, 3=Sub, 4=Account, 5=Mutation)
rgsOmslang         → custom_rgsOmslang       → Translatable (Small Text)
rgsOmsEngels       → custom_rgsEngels        → Translatable (Data)
rgsSortering       → custom_rgsSortering     → Sort order (Data)
rgsOmslag          → custom_rgsOmslag        → Contra account reference (Data)
rgsReferentienr    → custom_rgsReferentienr  → External reference (Data)
rgsBranche         → custom_rgsBranche       → Industry code (Int)
rgsStatus          → custom_rgsStatus        → Selection: A/P/V (Active/Passive/Obsolete)
rgsVersie          → custom_rgsVersie        → RGS version (Data)
rgsZZP             → custom_rgsZZP           → Selection: J/P/N (ZZP applicability)
rgsEZ              → custom_rgsEZ            → Selection: J/P/N (EZ/VOF applicability)
rgsBV              → custom_rgsBV            → Selection: J/P/N (BV applicability)
rgsSVC             → custom_rgsSVC           → Selection: J/P/N (SVC applicability)
rgsUITG            → custom_rgsUITG          → Check (Extended/Core RGS MKB)
srtExport          → custom_srtExport        → Export source (Data)
```

#### Hierarchy Processing
```
Level 1: Root Categories 
├── rgsNivo: "1"
├── rgsCode: "B" (Balance Sheet), "W" (Profit & Loss)
├── Parent: Company root
└── Examples: "B - BALANS", "W - WINST- EN VERLIESREKENING"

Level 2: Major Account Groups
├── rgsNivo: "2" 
├── rgsCode: "BIva", "WOmz", etc.
├── Parent: Level 1 (B or W)
└── Examples: "BIva - Immateriële vaste activa", "WOmz - Omzet"

Level 3-5: Detailed Accounts
├── rgsNivo: "3", "4", "5"
├── rgsCode: "BIvaKou", "WOmzPro", etc.
├── Parent: Higher level group
└── Examples: "BIvaKou - Kosten van ontwikkeling"
```

#### Data Processing Pipeline
```
Step 1: Load Master Data
rgsmkb_all4EN.json → RGS Classification DocType
├── Create parent-child relationships using rgsCode hierarchy
├── Validate 5-digit rgsReknr consistency (zero-pad if needed)
├── Index by rgsCode for hierarchical queries
└── Link rgsKenmerk to ERPNext account types

Step 2: Generate Templates  
RGS Master Data → Entity-Specific CoA Templates
├── Filter by business relevance (ZZP excludes complex corporate codes)
├── Include mandatory statutory accounts
├── Add commonly-used optional accounts
└── Maintain complete hierarchy (include parent accounts)

Step 3: Account Creation
CoA Template → ERPNext Account Records
├── rgsReknr → account_number (guaranteed unique)
├── rgsOmskort → account_name (user-friendly)
├── Auto-set account_type based on rgsKenmerk
└── Create parent-child relationships from hierarchy
```

#### Extension Pattern
```
Base Account: 10101 (rgsReknr)
├── Name: "Bank lopende rekening" (rgsOmskort)
├── Number: "10101" (stable identifier)
└── Extensions:
    ├── 10101.001 → "ABN AMRO Main Business Account"
    ├── 10101.002 → "ING Savings Account" 
    └── 10101.NL91ABNA0417164300 → "ABN AMRO IBAN Account"

Benefits:
✅ Maintains RGS compliance at base level
✅ Enables detailed sub-ledger management
✅ Supports business-specific requirements
✅ Preserves reporting aggregation
```

#### Multi-Member Accounting (Cooperatives & Partnerships)

Cooperatives, general partnerships (VOF), and similar multi-member legal entities require individual member account tracking while maintaining RGS compliance. The implementation supports two complementary approaches:

##### Option 1: Account Number Extensions (Simple Implementation)
```
Base RGS Account: 14010 - "Rekening-courant deelnemers"
├── 14010.MEMBER001 → "John Doe - Member Account"
├── 14010.MEMBER002 → "Jane Smith - Member Account"  
├── 14010.MEMBER003 → "ACME Corp - Corporate Member"
└── 14010.BOARD001 → "Board of Directors Reserve"

Benefits:
✅ Simple implementation using existing account_number field
✅ Maintains RGS compliance (all roll up to 14010)
✅ Clear member identification in Chart of Accounts
✅ Standard ERPNext reporting includes member detail
✅ No additional setup required

Limitations:
❌ Member-specific reporting requires custom queries
❌ Limited to string-based member identification
❌ No built-in member metadata (joining date, class, etc.)
```

##### Option 2: Accounting Dimensions Integration (Advanced Implementation)
```
Base Setup:
├── RGS Account: 14010 - "Rekening-courant deelnemers"
├── Accounting Dimension: "Member" (Custom DocType)
└── Dimension Values: Individual member records

Member DocType Structure:
doctype: "Cooperative Member"
fields:
  - member_id: Data (unique identifier)
  - member_name: Data (full legal name)
  - member_type: Select (Individual/Corporate/Board)
  - joining_date: Date
  - member_class: Select (A/B/C shares, voting rights)
  - equity_contribution: Currency
  - profit_share_percentage: Percent
  - is_active: Check

Account Integration:
├── Account: 14010 - "Rekening-courant deelnemers"
├── Dimension: "Member" (linked to Cooperative Member)
└── All transactions tagged with specific member

Benefits:
✅ Rich member metadata and classification
✅ Built-in member lifecycle management
✅ Automated profit/loss distribution capabilities
✅ Member-specific financial statements
✅ Integration with ERPNext's dimension filtering
✅ Supports complex equity structures
✅ Audit trail for member transactions

Advanced Features:
✅ Member profit distribution based on share classes
✅ Automated year-end equity adjustments
✅ Member statement generation
✅ Integration with member dues and assessments
```

##### Implementation Strategy for Different Entity Types

**Cooperative (Coöperatie):**
```
Required RGS Accounts with Member Extensions:
├── 14010 - "Rekening-courant deelnemers"
│   ├── Member current accounts (Option 1 or 2)
│   └── Board/management reserves
├── 20010 - "Ingebracht kapitaal leden"
│   ├── Member equity contributions by class
│   └── Voting vs. non-voting shares
└── 28090 - "Overige reserves"
    ├── Statutory reserves
    └── Member profit participation reserves

Legal Requirements:
✅ Individual member equity tracking (Article 2:53 BW)
✅ Profit distribution according to articles of association
✅ Member liability limitations properly accounted
✅ Cooperative-specific reporting for annual members meeting
```

**General Partnership (VOF):**
```
Required RGS Accounts with Partner Extensions:
├── 14010 - "Rekening-courant deelnemers" 
│   ├── Partner current accounts
│   └── Management compensation accounts
├── 20010 - "Ingebracht kapitaal leden"
│   ├── Initial partner contributions
│   └── Additional capital calls
└── 26010 - "Resultaat vorig boekjaar"
    ├── Partner profit/loss allocations
    └── Retained earnings by partner

Legal Requirements:
✅ Joint and several liability properly disclosed
✅ Partner profit/loss allocation per partnership agreement
✅ Individual partner capital account tracking
✅ Withdrawal and distribution controls
```

##### Technical Implementation Guide

**Phase 1: Basic Extension Implementation**
```python
def create_member_accounts(base_rgs_reknr, members_list):
    """
    Create member-specific account extensions
    """
    base_account = frappe.get_doc("Account", {
        "account_number": base_rgs_reknr,
        "company": company
    })
    
    for member in members_list:
        member_account = frappe.get_doc({
            "doctype": "Account",
            "account_name": f"{member['name']} - Member Account",
            "account_number": f"{base_rgs_reknr}.{member['id']}",
            "parent_account": base_account.name,
            "account_type": base_account.account_type,
            "balance_must_be": base_account.balance_must_be,
            "company": company,
            # Inherit RGS classification from parent
            "rgs_classification": base_account.rgs_classification,
            "rgs_reknr": base_rgs_reknr,  # Base RGS for compliance
            "rgs_compliance_status": "Extension"
        })
        member_account.insert()

# Usage example
members = [
    {"id": "MEMBER001", "name": "John Doe"},
    {"id": "MEMBER002", "name": "Jane Smith"},
    {"id": "CORP001", "name": "ACME Corp"}
]
create_member_accounts("14010", members)
```

**Phase 2: Accounting Dimensions Integration**
```python
# Custom DocType: Cooperative Member
def setup_member_dimension():
    """
    Configure Accounting Dimension for member tracking
    """
    # Create Accounting Dimension
    dimension = frappe.get_doc({
        "doctype": "Accounting Dimension",
        "document_type": "Cooperative Member",
        "dimension_name": "Member",
        "mandatory_for_bs": 0,
        "mandatory_for_pl": 0
    })
    dimension.insert()
    
    # Link specific accounts to require member dimension
    member_accounts = ["14010", "20010", "28090"]  # Member-related RGS accounts
    for account_number in member_accounts:
        add_dimension_to_account(account_number, "Member", mandatory=True)

def create_member_profit_distribution(members, net_profit):
    """
    Automate profit distribution based on member share classes
    """
    for member in members:
        share_percentage = member.profit_share_percentage / 100
        member_share = net_profit * share_percentage
        
        # Create journal entry for profit allocation
        je = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": frappe.utils.today(),
            "accounts": [
                {
                    "account": "26010",  # Retained earnings
                    "debit_in_account_currency": member_share,
                    "member": member.name  # Accounting dimension
                },
                {
                    "account": "14010",  # Member current account  
                    "credit_in_account_currency": member_share,
                    "member": member.name
                }
            ]
        })
        je.submit()
```

##### Best Practices and Compliance Notes

**Legal Compliance:**
- ✅ All member accounts maintain proper RGS classification
- ✅ Financial statements aggregate correctly for statutory reporting
- ✅ Member equity changes properly documented and auditable
- ✅ Dutch GAAP compliance maintained throughout member lifecycle

**Operational Benefits:**
- ✅ Individual member statements automatically generated
- ✅ Member profit/loss tracking integrated with general ledger
- ✅ Supports complex ownership structures (different share classes)
- ✅ Automated distribution calculations based on member agreements

**Integration Points:**
- ✅ Works with existing ERPNext customer/supplier if members trade with entity
- ✅ Integrates with payroll for member-employees
- ✅ Supports multi-currency for international members
- ✅ Compatible with consolidation for holding structures

---

## User Experience

### Company Creation Workflow
```
1. User creates new company
2. Selects "Netherlands" as country
3. System offers RGS-based CoA templates:
   • Netherlands - ZZP (Sole Proprietor)
   • Netherlands - BV (Private Limited Company)
   • Netherlands - EZ (One-person Company)
   • Netherlands - SVC (Foundation/Association/Cooperative/VOF)
   • Netherlands - Custom Selection
4. User selects appropriate template
5. System creates RGS-compliant Chart of Accounts
6. For SVC entities, system prompts for multi-member setup:
   • Simple account extensions (account_number.MEMBER_ID)
   • Advanced Accounting Dimensions (member tracking DocType)
7. User can customize by adding/removing accounts
8. All accounts maintain RGS classification links
```

### Template Customization
```
1. Start with base template (e.g., ZZP)
2. Browse RGS master data (search/filter)
3. Add relevant accounts for specific business
4. Remove superfluous accounts (e.g., manufacturing codes for service business)
5. Save as custom template for future use
6. Export template for other companies
```

### Account Management
```
1. All accounts link to official RGS codes
2. RGS properties auto-populate during account creation
3. Validation ensures proper RGS compliance
4. Reporting automatically uses RGS structure
```

---

## Technical Implementation

### DocTypes Structure

#### 1. RGS Classification (Master Data)
```python
# Read-only master data DocType (Official RGS MKB Specification)
doctype: "RGS Classification"
naming_rule: "rgsCode"  # Official RGS classification code as primary key
fields:
  # Core RGS Fields (from attributes.csv)
  - rgs_code: Data (Read-Only, Unique, Searchable, Mandatory) # PRIMARY KEY
  - rgs_omskort: Data (Translatable - user-friendly account name for SME)
  - rgs_reknr: Data (5-digit decimal account number - SME identifier)
  - rgs_dc: Select (null/Debit/Credit - balance_must_be mapping)
  - rgs_nivo: Int (1=Balance/P&L, 2=Main, 3=Sub, 4=Account, 5=Mutation)
  - rgs_omslang: Small Text (Translatable, long description)
  - rgs_oms_engels: Data (Translatable, English description)
  - rgs_sortering: Data (Sort order for logical balance/P&L layout)
  - rgs_omslag: Data (References another rgsCode for contra accounts)
  - rgs_referentienr: Data (External reference, standard RGS)
  - rgs_branche: Int (Industry: 1=Standard, 2=Construction, 4=Agriculture, 5=Housing)
  - rgs_status: Select (A=Active, P=Passive, V=Obsolete)
  - rgs_versie: Data (RGS version/subversion)
  # Entity Applicability Flags
  - rgs_zzp: Select (J=Standard, P=Extended, N=Not applicable)
  - rgs_ez: Select (J=Standard, P=Extended, N=Not applicable)
  - rgs_bv: Select (J=Standard, P=Extended, N=Not applicable)
  - rgs_svc: Select (J=Standard, P=Extended, N=Not applicable)
  - rgs_uitg: Check (Extended indicator - N=RGS MKB, J=Extended)
  - srt_export: Data (Export source identifier)
  # Tree Structure
  - parent_rgs_classification: Link (References parent rgsCode for hierarchy)
  - is_group: Check (Derived from rgs_nivo < 5)
  # ERPNext Integration (Derived Fields)
  - erpnext_report_type: Select (Balance Sheet/Profit and Loss)
  - erpnext_root_type: Select (Asset/Liability/Equity/Income/Expense)
  - erpnext_account_type: Select (Bank/Receivable/Payable/Fixed Asset/etc.)
  - concept_mappings: Long Text (JSON from translation CSV)

indexes:
  - rgs_code (PRIMARY KEY - hierarchical queries and uniqueness)
  - rgs_reknr (SME identifier lookup)
  - rgs_nivo, is_group (filtering and tree operations)
  - rgs_status (active/passive/obsolete filtering)
  - entity flags (rgs_zzp, rgs_ez, rgs_bv, rgs_svc) for template creation

# Key Design Principle:
# - rgsCode: Official classification (primary key, hierarchical structure)
# - rgsReknr + rgsOmskort: User-friendly SME identifiers (shown in UI)
# - rgsOmslag: References another rgsCode (not rgsReknr)
```

#### 2. Enhanced Account DocType
```python
# Custom fields added to ERPNext Account via hooks
custom_fields = [
    {
        "fieldname": "rgs_reknr",
        "label": "RGS Account Number",
        "fieldtype": "Data",
        "read_only": 1,
        "description": "Stable 5-digit RGS identifier"
    },
    {
        "fieldname": "rgs_classification",
        "label": "RGS Classification",
        "fieldtype": "Link",
        "options": "RGS Classification",
        "description": "Link to official RGS code"
    },
    {
        "fieldname": "rgs_code",
        "label": "RGS Code",
        "fieldtype": "Data", 
        "read_only": 1,
        "fetch_from": "rgs_classification.rgs_code"
    },
    {
        "fieldname": "rgs_nivo",
        "label": "RGS Level",
        "fieldtype": "Select",
        "options": "1\n2\n3\n4\n5",
        "read_only": 1,
        "fetch_from": "rgs_classification.rgs_nivo"
    },
    {
        "fieldname": "rgs_dc_normal_balance",
        "label": "RGS Normal Balance",
        "fieldtype": "Select",
        "options": "Debit\nCredit",
        "read_only": 1,
        "description": "Normal balance from rgsDc field"
    },
    {
        "fieldname": "rgs_compliance_status",
        "label": "RGS Compliance",
        "fieldtype": "Select",
        "options": "Compliant\nNon-compliant\nExtension",
        "default": "Compliant"
    }
]
```
  - rgs_compliance_status: Validation status
```

#### 3. RGS CoA Template
```python
# ERPNext Chart of Accounts Template extension
doctype: "Chart of Accounts Template"
custom_fields:
  - rgs_entity_type: ZZP, BV, EZ, SVC
  - rgs_template_base: Base template reference
  - rgs_customizations: Added/removed accounts
```

### Data Loading Strategy

#### Phase 1: RGS Master Data Conversion (Official Implementation)
```python
# Convert rgsmkb_all4EN.json to Frappe fixtures with official field mappings
def convert_rgs_to_fixtures():
    """
    Transform rgsmkb_all4EN.json to fixtures/rgs_classification.json
    Using official attributes.csv mappings and translation CSV concepts
    """
    source_data = load_json('/opt/frappe_docker/rgs_mkb/rgsmkb_all4EN.json')
    csv_concepts = load_csv_concepts('/tmp/nl_erpnext_rgs_mkb/20210913 RGS NL en EN labels.csv')
    fixtures = []
    
    for record in source_data:
        # Use rgsCode as primary key (official classification)
        rgs_code = record.get('rgsCode', '')
        rgs_reknr = str(record.get('rgsReknr', '0')).zfill(5)  # SME identifier
        
        # Get translation concepts for intelligent ERPNext mapping
        concept_mappings = parse_concept_mappings_from_csv(rgs_code, csv_concepts)
        
        # Determine ERPNext mappings using translation concepts
        report_type = determine_report_type_from_code(rgs_code)
        root_type = determine_root_type_from_rgs_code(rgs_code, concept_mappings)
        account_type = determine_account_type_from_rgs_code(rgs_code, root_type, concept_mappings)
        
        # Build fixture using official field mappings
        fixture = {
            "doctype": "RGS Classification",
            "name": rgs_code,  # Primary key (official classification)
            # Core RGS fields (official mapping from attributes.csv)
            "rgs_code": rgs_code,
            "rgs_omskort": record.get('rgsOmskort', ''),  # SME account name
            "rgs_reknr": rgs_reknr,  # SME account number
            "rgs_dc": map_rgs_dc_to_selection(record.get('rgsDc')),
            "rgs_nivo": parse_int_safe(record.get('rgsNivo')),
            "rgs_omslang": record.get('rgsOmslang', ''),
            "rgs_oms_engels": record.get('rgsOmsEngels', ''),
            "rgs_sortering": record.get('rgsSortering', ''),
            "rgs_omslag": record.get('rgsOmslag', ''),  # References another rgsCode
            "rgs_referentienr": record.get('rgsReferentienr', ''),
            "rgs_branche": parse_int_safe(record.get('rgsBranche')),
            "rgs_status": record.get('rgsStatus', 'A'),
            "rgs_versie": record.get('rgsVersie', '3.7'),
            # Entity applicability flags
            "rgs_zzp": record.get('rgsZZP', 'N'),
            "rgs_ez": record.get('rgsEZ', 'N'),
            "rgs_bv": record.get('rgsBV', 'N'),
            "rgs_svc": record.get('rgsSVC', 'N'),
            "rgs_uitg": record.get('rgsUITG', 'N'),
            "srt_export": record.get('srtExport', ''),
            # Tree structure (using rgsCode hierarchy)
            "parent_rgs_classification": find_parent_rgs_code(rgs_code, source_data),
            "is_group": determine_if_group_from_nivo(record.get('rgsNivo')),
            # ERPNext integration (derived)
            "erpnext_report_type": report_type,
            "erpnext_root_type": root_type,
            "erpnext_account_type": account_type,
            "concept_mappings": json.dumps(concept_mappings)
        }
        fixtures.append(fixture)
    
    # Write to fixtures/rgs_classification.json
    save_fixtures(fixtures, 'rgs_classification.json')

def map_rgs_dc_to_selection(rgs_dc):
    """Map rgsDc to ERPNext balance_must_be selection"""
    if not rgs_dc:
        return ""
    dc = str(rgs_dc).strip().upper()
    return "Debit" if dc == "D" else "Credit" if dc == "C" else ""

def parse_int_safe(value):
    """Safely parse integer values"""
    try:
        return int(str(value)) if value else 0
    except (ValueError, TypeError):
        return 0

def find_parent_rgs_code(rgs_code, source_data):
    """
    Find parent rgsCode using RGS hierarchical structure
    B → BIva → BIvaKou → BIvaKouOnd (each level removes 3 chars)
    Returns the parent rgsCode (not rgsReknr)
    """
    if len(rgs_code) <= 1 or rgs_code in ['B', 'W']:
        return None  # Root level
    
    # Determine parent code by removing last 3-character segment
    if len(rgs_code) <= 4:
        parent_code = rgs_code[0]  # B or W
    else:
        parent_code = rgs_code[:-3]
    
    # Find parent rgsCode (verify it exists in source data)
    for record in source_data:
        if record.get('rgsCode') == parent_code:
            return parent_code  # Return the rgsCode directly
    
    return None

def load_csv_concepts(csv_file_path):
    """Load translation CSV for concept mappings and legal basis"""
    import csv
    concepts = []
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            concepts.append(row)
    return concepts

def parse_concept_mappings_from_csv(rgs_code, csv_data):
    """Extract concept mappings and legal basis for RGS code"""
    concepts = []
    for row in csv_data:
        if row['RGS code'] == rgs_code:
            concepts.append({
                'concept': row['Concept'],
                'nl_label': row['NL Label'],
                'en_label': row['EN Label'],
                'nl_terse': row['NL Terse label'],
                'en_terse': row['EN terse label']
            })
    return concepts
```

def determine_if_group_from_nivo(nivo):
    """RGS accounts with nivo < 5 are typically groups"""
    try:
        nivo_int = int(str(nivo))
        return nivo_int < 5  # Groups are levels 1-4, ledgers are level 5
    except (ValueError, TypeError):
        return False

def find_parent_reknr(record):
    """Determine parent using rgsCode hierarchy (B → BIva → BIvaKou)"""
    rgs_code = record.get('rgsCode', '')
    if rgs_code in ['B', 'W']:
        return None  # Root level accounts have no parent
    
    # Find parent by removing last segment
    if len(rgs_code) <= 1:
        return None
    elif len(rgs_code) <= 4:
        parent_code = rgs_code[0]  # B or W
    else:
        # Remove last 3 characters for longer codes
        parent_code = rgs_code[:-3]
    
    return lookup_reknr_by_code(parent_code)

def map_rgs_dc_to_balance(rgs_dc):
    """Map rgsDc to ERPNext balance_must_be field"""
    if not rgs_dc:
        return ""
    dc = str(rgs_dc).strip().upper()
    return "Debit" if dc == "D" else "Credit" if dc == "C" else ""

def determine_report_type_from_code(rgs_code):
    """Map B/W prefix to ERPNext report_type"""
    if not rgs_code:
        return ""
    first_char = rgs_code[0].upper()
    return "Balance Sheet" if first_char == "B" else "Profit and Loss" if first_char == "W" else ""

def determine_root_type_from_rgs_code(rgs_code, concept_mappings):
    """
    Determine ERPNext root_type from RGS code and concept mappings
    Uses intelligent pattern matching based on CSV analysis
    """
    if not rgs_code:
        return ""
    
    # Check concept mappings for explicit classification
    if concept_mappings:
        for concept in concept_mappings:
            if 'jenv-bw2-i_Assets' in concept:
                return "Asset" 
            elif 'jenv-bw2-i_Liabilities' in concept:
                return "Liability"
            elif 'jenv-bw2-i_Equity' in concept:
                return "Equity"
            elif any(x in concept for x in ['jenv-bw2-i_Income', 'jenv-bw2-i_NetRevenue', 'jenv-bw2-i_Revenue']):
                return "Income"
            elif 'jenv-bw2-i_Expenses' in concept:
                return "Expense"
    
    # Fallback to intelligent RGS code analysis
    code_upper = rgs_code.upper()
    
    # Balance Sheet accounts (B prefix)
    if code_upper.startswith('B'):
        # Assets patterns
        if any(pattern in code_upper for pattern in ['IVA', 'MVA', 'FIN', 'VOR', 'EFF', 'LIQ']):
            return "Asset"
        # Liability patterns 
        elif any(pattern in code_upper for pattern in ['LAS', 'KRE', 'SCH']):
            return "Liability"
        # Equity patterns
        elif any(pattern in code_upper for pattern in ['EIV', 'KAP', 'RES', 'WIN']):
            return "Equity"
        else:
            # Default for unclassified B codes - likely assets
            return "Asset"
    
    # Profit & Loss accounts (W prefix)
    elif code_upper.startswith('W'):
        # Income patterns
        if any(pattern in code_upper for pattern in ['OMZ', 'OPB', 'BAT', 'FBE']):
            return "Income"
        # Expense patterns
        else:
            return "Expense"
    
    return ""

def determine_account_type_from_rgs_code(rgs_code, root_type, concept_mappings):
    """
    Determine specific ERPNext account_type from RGS code and root_type
    Based on Dutch accounting standards and RGS classification patterns
    """
    if not rgs_code or not root_type:
        return ""
    
    code_upper = rgs_code.upper()
    
    if root_type == "Asset":
        if any(pattern in code_upper for pattern in ['IVA']):  # Immateriële vaste activa
            return "Fixed Asset"
        elif any(pattern in code_upper for pattern in ['MVA']):  # Materiële vaste activa
            return "Fixed Asset"
        elif any(pattern in code_upper for pattern in ['FIN']):  # Financiële vaste activa
            return "Fixed Asset"
        elif any(pattern in code_upper for pattern in ['VOR']):  # Vorderingen
            return "Receivable"
        elif any(pattern in code_upper for pattern in ['LIQ', 'KAS', 'BANK']):  # Liquide middelen
            return "Bank"
        elif any(pattern in code_upper for pattern in ['EFF']):  # Effecten
            return "Stock"
        else:
            return "Current Asset"
    
    elif root_type == "Liability":
        if any(pattern in code_upper for pattern in ['LAS']):  # Langlopende schulden
            return "Payable"
        elif any(pattern in code_upper for pattern in ['KRE']):  # Crediteuren
            return "Payable"
        else:
            return "Current Liability"
    
    elif root_type == "Equity":
        if any(pattern in code_upper for pattern in ['KAP']):  # Kapitaal
            return "Equity"
        elif any(pattern in code_upper for pattern in ['RES']):  # Reserves
            return "Equity" 
        else:
            return "Equity"
    
    elif root_type == "Income":
        if any(pattern in code_upper for pattern in ['OMZ']):  # Omzet
            return "Income Account"
        else:
            return "Income Account"
    
    elif root_type == "Expense":
        if any(pattern in code_upper for pattern in ['AFS']):  # Afschrijvingen
            return "Depreciation"
        elif any(pattern in code_upper for pattern in ['KOS']):  # Kosten
            return "Expense Account"
        elif any(pattern in code_upper for pattern in ['BEL']):  # Belastingen
            return "Tax"
        else:
            return "Expense Account"
    
    return ""

#### Intelligent Account Classification

The system uses a sophisticated approach to determine ERPNext `root_type` and `account_type` from RGS codes:

##### 1. **Hierarchical Structure Derivation**
```python
# RGS codes are naturally hierarchical:
B                    → Root: Balance Sheet (Level 1)
├── BIva            → Fixed Assets (Level 2) 
│   └── BIvaKou     → Development Costs (Level 3)
├── BLas            → Liabilities (Level 2)
│   └── BLasKre     → Trade Creditors (Level 3)
└── BEiv            → Equity (Level 2)
    └── BEivKap     → Share Capital (Level 3)

W                    → Root: Profit & Loss (Level 1)
├── WOmz            → Revenue (Level 2)
│   └── WOmzPro     → Product Sales (Level 3)
└── WAfs            → Expenses (Level 2)
    └── WAfsIva     → Depreciation (Level 3)
```

##### 2. **Multi-Layer Classification Logic**
```python
Priority 1: CSV Concept Mappings (Most Accurate)
├── jenv-bw2-i_Assets           → root_type: "Asset"
├── jenv-bw2-i_Liabilities      → root_type: "Liability" 
├── jenv-bw2-i_Equity           → root_type: "Equity"
├── jenv-bw2-i_Income           → root_type: "Income"
└── jenv-bw2-i_Expenses         → root_type: "Expense"

Priority 2: RGS Code Pattern Analysis (Fallback)
├── B + IVA/MVA/FIN patterns    → Asset (Fixed/Current)
├── B + LAS/KRE patterns        → Liability
├── B + EIV/KAP patterns        → Equity
├── W + OMZ/OPB patterns        → Income
└── W + Other patterns          → Expense
```

##### 3. **Account Type Refinement** 
```python
Asset Classifications:
├── IVA (Immateriële vaste activa)     → "Fixed Asset"
├── MVA (Materiële vaste activa)       → "Fixed Asset"  
├── FIN (Financiële vaste activa)      → "Fixed Asset"
├── VOR (Vorderingen)                  → "Receivable"
├── LIQ/KAS/BANK (Liquide middelen)    → "Bank"
├── EFF (Effecten)                     → "Stock"
└── Other                              → "Current Asset"

Liability Classifications:
├── LAS (Langlopende schulden)         → "Payable" 
├── KRE (Crediteuren)                  → "Payable"
└── Other                              → "Current Liability"

Income Classifications:
├── OMZ (Omzet)                        → "Income Account"
└── Other                              → "Income Account"

Expense Classifications:
├── AFS (Afschrijvingen)               → "Depreciation"
├── KOS (Kosten)                       → "Expense Account"
├── BEL (Belastingen)                  → "Tax"
└── Other                              → "Expense Account"
```
    """
    Extract concept mappings for a specific RGS code from the translation CSV
    Returns list of concept identifiers that help classify the account
    """
    concepts = []
    for row in csv_data:
        if row['RGS code'] == rgs_code:
            concepts.append(row['Concept'])
    return concepts
```

#### Phase 2: Entity Template Processing
```python
# Convert entity-specific templates to ERPNext CoA Templates
templates = {
    'ZZP': '/opt/frappe_docker/rgs_mkb/coa_zzp_standard.json',
    'BV': '/opt/frappe_docker/rgs_mkb/export_bv_standard.json', 
    'EZ': '/opt/frappe_docker/rgs_mkb/export_ez_standard.json',
    'SVC': '/opt/frappe_docker/rgs_mkb/export_svc_standard.json'
}

def create_coa_template(entity_type, source_file):
    """Convert entity template to ERPNext Chart of Accounts Template"""
    template_data = {
        "doctype": "Chart of Accounts Template",
        "name": f"Netherlands - {entity_type}",
        "country": "Netherlands", 
        "rgs_entity_type": entity_type,
        "template_data": convert_to_erpnext_format(source_file)
    }
    
    # Process each account in template
    accounts = []
    for account in load_json(source_file):
        rgs_reknr = str(account.get('rgsReknr', '')).zfill(5)
        rgs_classification = get_rgs_classification(rgs_reknr)
        
        erpnext_account = {
            "account_number": rgs_reknr,
            "account_name": account.get('rgsOmskort', ''),
            "account_type": map_rgs_to_account_type(rgs_classification),
            "report_type": determine_report_type_from_code(rgs_classification.rgs_code),
            "balance_must_be": map_rgs_dc_to_balance(rgs_classification.rgs_dc),
            "is_group": rgs_classification.is_group,
            "parent_account": get_parent_account_number(rgs_classification),
            "rgs_classification": rgs_reknr,  # Link to RGS master data
            "rgs_reknr": rgs_reknr,
            "rgs_code": rgs_classification.rgs_code,
            "rgs_nivo": rgs_classification.rgs_nivo
        }
        accounts.append(erpnext_account)
    
    template_data["accounts"] = accounts
    return template_data
```

#### Phase 3: Installation & Integration
```python
# hooks.py integration
def after_install():
    """Post-installation setup"""
    # Load RGS master data from fixtures
    import_fixtures(['rgs_classification.json'])
    
    # Create CoA templates for each entity type
    for entity_type in ['ZZP', 'BV', 'EZ', 'SVC']:
        create_and_save_coa_template(entity_type)
    
    # Register custom pages and reports
    install_custom_pages()
    setup_rgs_dashboards()

# Account validation hooks
doc_events = {
    "Account": {
        "validate": "nl_erpnext_rgs_mkb.account_validation.validate_rgs_compliance",
        "before_save": "nl_erpnext_rgs_mkb.account_validation.auto_populate_rgs_fields"
    },
    "Company": {
        "after_insert": "nl_erpnext_rgs_mkb.company_setup.offer_rgs_templates"
    }
}
```

### Integration Points
```python
# ERPNext hooks
doc_events:
  Account:
    validate: "validate_rgs_compliance"
    before_save: "auto_populate_rgs_fields"
  Company:
    after_insert: "offer_rgs_templates"

# Custom pages/reports
- RGS Browser: Search/select RGS codes
- RGS Compliance Report: Validation status
- Dutch Financial Statements: RGS-formatted reports
```

---

## Lessons Learned and Implementation Guide

This section captures critical insights gained during development and deployment of the Dutch RGS MKB app, providing guidance for successful implementation.

### Critical Design Corrections

#### 1. **Primary Key and Hierarchy Structure** ⚠️ **CRITICAL**
```
WRONG: Using rgsReknr as primary key
CORRECT: Using rgsCode as primary key with rgsReknr as SME identifier

Key Learning:
- rgsCode: Official RGS classification (hierarchical structure, primary key)
- rgsReknr: SME-friendly 5-digit decimal number (shown to users)
- rgsOmskort: SME-friendly account description (shown to users)
- rgsOmslag: References another rgsCode (not rgsReknr)

Parent-Child Structure:
parent_rgs_classification → Links to rgsCode (not rgsReknr)
Tree hierarchy follows: B → BIva → BIvaKou → BIvaKouOnd
```

#### 2. **ERPNext vs RGS Account Mapping**
```
Existing Dutch CoA in ERPNext:
- Non-RGS compliant
- Designed for larger enterprises
- Asset/Liability/Equity classification issues
- NOT suitable for SME compliance requirements

RGS MKB Approach:
- Official classification via rgsCode
- SME-friendly display via rgsReknr + rgsOmskort
- Legal compliance through attributes.csv mappings
- Three-document integration (canonical + specs + translations)
```

### Docker Deployment Lessons

#### 1. **Frappe Docker Configuration** 🐳
```bash
# Working Profile-Based Architecture
COMPOSE_FILE="compose.yaml:compose.yml"
COMPOSE_PROFILES="mariadb,create-site"

# Critical Environment Variables
ERPNEXT_VERSION=v15.0.0
FRAPPE_VERSION=v15.0.0
DB_ROOT_USER=root
DB_ROOT_PASSWORD=admin

# Sites Directory Structure
/opt/frappe_docker/
├── compose.yaml (profile-based architecture)
├── apps.json (ERPNext + nl_erpnext_rgs_mkb)
└── sites/
    └── frappe.fivi.eu/ (working site)
```

**Key Learnings:**
- ✅ Use profile-based Docker Compose (simpler than override files)
- ✅ MariaDB + create-site profiles work reliably
- ✅ Avoid complex networking configs initially
- ❌ Don't use custom domain configs until basic setup works

#### 2. **App Installation Process** 📦
```bash
# Working Installation Sequence
1. Build custom image with apps.json
2. Start MariaDB profile
3. Create site with create-site profile  
4. Install apps in correct order
5. Run migrations and fixture loading

# Critical Commands
docker buildx bake custom --set custom.args.APPS_JSON_BASE64=$(base64 -w 0 apps.json)
docker compose --profile create-site up -d
docker exec frappe_docker-backend-1 bench --site frappe.fivi.eu install-app nl_erpnext_rgs_mkb
```

**Key Learnings:**
- ✅ Apps.json must include ERPNext + custom app
- ✅ Build cache issues require --no-cache occasionally
- ✅ Site creation separate from app installation
- ❌ Don't run migrations during Docker build
- ❌ Large fixtures cause installation failures

#### 3. **Fixture Management** 📊
```python
# Fixture Size Limitations
Problem: Large RGS fixtures (>5000 records) cause memory issues
Solution: Staged fixture loading

# Working Approach
fixtures/
├── custom_field.json (small, always works)
├── rgs_classification.json (large, staged loading)
└── *.json.bak (disabled until needed)

# Loading Strategy
1. Load custom fields first (DocType creation)
2. Load small fixtures during install
3. Load large fixtures via bench commands post-install
```

**Key Learnings:**
- ✅ Keep fixture files <1MB for reliable installation
- ✅ Use .bak extension to disable large fixtures temporarily
- ✅ Load DocType definitions before data
- ❌ Don't include large datasets in initial installation

### Modern Frappe Framework Patterns

#### 1. **DocType Design** 🏗️
```python
# Tree DocType Structure
class RGSClassification:
    naming_rule: "rgsCode"  # Official classification
    is_tree: True
    tree_parent_field: "parent_rgs_classification"
    
    # User Interface Fields
    display_fields = ["rgs_reknr", "rgs_omskort"]  # SME identifiers
    
    # Hierarchical Validation
    def validate_parent_child_relationship(self):
        # Ensure rgsCode hierarchy consistency
        pass
```

**Key Learnings:**
- ✅ Use official identifiers as primary keys
- ✅ Display user-friendly fields in UI
- ✅ Implement proper tree validation
- ❌ Don't use user-friendly IDs as primary keys

#### 2. **Custom Field Integration** 🔗
```python
# Account DocType Enhancement
custom_fields = [
    {
        "fieldname": "rgs_classification",
        "fieldtype": "Link",
        "options": "RGS Classification",
        "fetch_from": "rgs_classification.rgs_reknr"  # Display SME number
    }
]

# Auto-population Strategy
def before_save(doc):
    if doc.rgs_classification:
        rgs = frappe.get_doc("RGS Classification", doc.rgs_classification)
        doc.account_number = rgs.rgs_reknr  # SME identifier
        doc.account_name = rgs.rgs_omskort  # SME description
```

**Key Learnings:**
- ✅ Link to official classification, display user-friendly values
- ✅ Auto-populate from RGS master data
- ✅ Maintain data integrity through validation
- ❌ Don't duplicate RGS data in Account records

### Data Architecture Insights

#### 1. **Three-Document Integration** 📚
```
Official RGS Documentation:
1. rgsmkb_all4EN.json → Canonical dataset (~5000 codes)
2. attributes.csv → Field specifications and ERPNext mappings
3. labels.csv → Translations and legal basis

Benefits:
✅ Authoritative source (not invented fields)
✅ Complete field specifications
✅ Legal compliance documentation
✅ Multilingual support
```

#### 2. **Field Mapping Strategy** 🗺️
```
RGS Field → ERPNext Field → User Display
rgsCode → primary key → (hidden from users)
rgsReknr → account_number → "10101"
rgsOmskort → account_name → "Bank lopende rekening"
rgsDc → balance_must_be → "Debit"/"Credit"
rgsOmslag → custom field → Link to another rgsCode
```

### Performance and Scalability

#### 1. **Database Indexing** 🔍
```sql
-- Critical Indexes for Performance
CREATE INDEX idx_rgs_code ON `tabRGS Classification` (rgs_code);
CREATE INDEX idx_rgs_reknr ON `tabRGS Classification` (rgs_reknr);
CREATE INDEX idx_rgs_nivo ON `tabRGS Classification` (rgs_nivo);
CREATE INDEX idx_entity_flags ON `tabRGS Classification` (rgs_zzp, rgs_ez, rgs_bv, rgs_svc);
```

#### 2. **Query Optimization** ⚡
```python
# Efficient RGS Queries
def get_entity_accounts(entity_type):
    filters = {
        f"rgs_{entity_type.lower()}": ["in", ["J", "P"]],
        "rgs_status": "A"
    }
    return frappe.get_all("RGS Classification", filters=filters)

# Tree Navigation
def get_rgs_children(parent_code):
    return frappe.get_all("RGS Classification", 
                         filters={"parent_rgs_classification": parent_code})
```

### Testing and Validation

#### 1. **Installation Testing** ✅
```bash
# Verification Commands
docker exec frappe_docker-backend-1 bench --site frappe.fivi.eu list-apps
docker exec frappe_docker-backend-1 bench --site frappe.fivi.eu console

# ERPNext Console Validation
>>> frappe.db.count("RGS Classification")
>>> frappe.get_list("RGS Classification", limit=5)
>>> frappe.get_doc("Account", {"account_number": "10101"})
```

#### 2. **Data Integrity Checks** 🔍
```python
# Hierarchical Validation
def validate_rgs_hierarchy():
    orphaned = frappe.db.sql("""
        SELECT name FROM `tabRGS Classification` 
        WHERE parent_rgs_classification IS NOT NULL 
        AND parent_rgs_classification NOT IN (
            SELECT name FROM `tabRGS Classification`
        )
    """)
    return orphaned

# Compliance Validation
def validate_rgs_compliance():
    accounts_without_rgs = frappe.db.count("Account", {
        "company": "Test Company",
        "rgs_classification": ["is", "not set"]
    })
    return accounts_without_rgs
```

### Common Pitfalls and Solutions

#### 1. **Docker Issues** 🚨
```
Problem: "failed to solve" during Docker build
Solution: Clear build cache, use --no-cache flag

Problem: Site creation fails
Solution: Verify MariaDB is running, check environment variables

Problem: App installation timeout
Solution: Reduce fixture size, use staged loading

Problem: Permission denied errors
Solution: Check user ownership of frappe_docker directory
```

#### 2. **Frappe Framework Issues** ⚠️
```
Problem: AttributeError on lft/rgt fields
Solution: Remove obsolete nested set references

Problem: Fixture loading fails
Solution: Validate JSON format, reduce file size

Problem: Tree structure broken
Solution: Verify parent_field configuration, rebuild tree

Problem: Custom fields not appearing
Solution: Clear cache, check field permissions
```

#### 3. **RGS Data Issues** 📊
```
Problem: Missing parent relationships
Solution: Implement proper rgsCode hierarchy parsing

Problem: Inconsistent account numbering
Solution: Use zero-padding for rgsReknr (5 digits)

Problem: Invalid balance_must_be values
Solution: Map rgsDc properly (D→Debit, C→Credit)

Problem: Entity filters not working
Solution: Check entity flag values (J/P/N format)
```

### Analysis of Existing ERPNext Dutch CoA

#### 1. **Structure and Limitations** 📋
```json
// From nl_grootboekschema.json (ERPNext standard)
{
  "country_code": "nl",
  "name": "Netherlands - Grootboekschema",
  "tree": {
    "VASTE ACTIVA, EIGEN VERMOGEN, LANGLOPEND VREEMD VERMOGEN EN VOORZIENINGEN": {
      "root_type": "Equity"  // ❌ Mixing Asset and Equity
    },
    "FINANCIELE REKENINGEN, KORTLOPENDE VORDERINGEN EN SCHULDEN": {
      "root_type": "Asset"   // ❌ Mixing Asset and Liability
    }
  }
}
```

**Key Issues with Standard Dutch CoA:**
- ❌ **Not RGS compliant** - no official classification codes
- ❌ **Incorrect root_type assignments** - mixes Balance Sheet categories
- ❌ **Enterprise-focused** - not suitable for SME compliance
- ❌ **Fixed structure** - no customization for entity types
- ❌ **No legal compliance** - missing mandatory reporting categories

#### 2. **Asset/Liability/Equity Classification Problems** ⚠️
```
Standard Dutch CoA Issues:
1. "VASTE ACTIVA" (Fixed Assets) marked as root_type: "Equity"
   Should be: root_type: "Asset"

2. "KORTLOPENDE SCHULDEN" (Current Liabilities) under Asset section
   Should be: root_type: "Liability"

3. "VOORZIENINGEN" (Provisions) marked as Equity accounts
   Should be: root_type: "Liability" (per Dutch GAAP)

4. No distinction between different equity types
   Missing: Share capital, retained earnings, statutory reserves
```

#### 3. **RGS MKB Improvements** ✅
```
Our Approach Fixes:
✅ Official RGS classification codes (rgsCode)
✅ Correct ERPNext root_type mapping via attributes.csv
✅ SME-specific account selections per entity type
✅ Legal compliance through rgsDc → balance_must_be mapping
✅ Extensible for business-specific sub-accounts
✅ Forward compatibility with RGS 3.8+

Root Type Mapping Strategy:
rgsCode starting with 'B' → Balance Sheet analysis
├── Asset codes → root_type: "Asset"  
├── Liability codes → root_type: "Liability"
└── Equity codes → root_type: "Equity"

rgsCode starting with 'W' → Profit & Loss analysis  
├── Income codes → root_type: "Income"
└── Expense codes → root_type: "Expense"
```

#### 4. **Migration Path from Standard Dutch CoA** 🔄
```python
def migrate_from_standard_dutch_coa():
    """
    Migration strategy for companies using standard Dutch CoA
    """
    # 1. Map existing accounts to RGS codes where possible
    # 2. Identify unmapped accounts for manual review
    # 3. Create RGS-compliant structure
    # 4. Transfer balances and historical data
    # 5. Update reporting to use RGS classifications
    
    mapping_rules = {
        "Bank": "10101",  # Standard to RGS mapping
        "Kas": "10001",   # Cash accounts
        "Debiteuren": "13010",  # Receivables
        # ... additional mappings
    }
```

---

## Business Value

### Legal Compliance
- **Automatic RGS 3.7 compliance** for financial reporting
- **Audit-ready** Chart of Accounts structure
- **Regulatory alignment** with Dutch accounting standards
- **Error prevention** through validation rules

### Operational Benefits  
- **Faster setup** with pre-configured templates
- **Reduced errors** through standardized classifications
- **Consistent reporting** across companies
- **Easy customization** for specific business needs

### Strategic Advantages
- **Benchmarking** using standardized KPIs
- **Industry comparison** with sector metrics
- **Business intelligence** through consistent data structure
- **Future-proof** compliance with regulatory changes

---

## Development Phases

### Phase 1: Foundation (Current Priority)
**Goal:** Load and access RGS master data
```
- Convert rgsmkb_all4EN.json to proper Frappe fixtures
- Create RGS Classification DocType with read-only access
- Build search/filter interface for RGS browsing
- Resolve current fixture loading issues
```

### Phase 2: CoA Integration
**Goal:** Seamless Chart of Accounts creation
```
- Convert entity templates to ERPNext CoA Templates
- Integrate with company creation workflow
- Add RGS fields to Account DocType
- Implement template customization interface
```

### Phase 3: Compliance & Validation
**Goal:** Ensure RGS compliance
```
- Account validation rules
- RGS compliance checking
- Error detection and reporting
- Audit trail for RGS changes
```

### Phase 4: Reporting & Analytics
**Goal:** Dutch financial reporting
```
- RGS-compliant financial statements
- Standard Dutch KPI calculations
- Industry benchmarking reports
- Performance dashboards
```

---

## Success Criteria

### Technical Success
- ✅ Complete RGS 3.7 dataset loaded and accessible
- ✅ Entity-specific CoA templates working in ERPNext
- ✅ Account creation with automatic RGS compliance
- ✅ Template customization without breaking compliance

### Business Success
- ✅ Dutch companies can create legally compliant Chart of Accounts
- ✅ Automatic financial reporting meets regulatory requirements
- ✅ Users can customize templates for specific business needs
- ✅ Benchmarking and KPI calculations work correctly

### User Experience Success
- ✅ Intuitive template selection during company setup
- ✅ Easy browsing and selection of RGS codes
- ✅ Clear validation messages for compliance issues
- ✅ Familiar ERPNext workflow with RGS enhancements

---

## Current Status & Next Steps

### What's Working
- ✅ App installation and basic DocTypes
- ✅ Custom fields integration
- ✅ Profile-based Docker deployment
- ✅ ERPNext site with app installed

### Immediate Blockers
- ❌ RGS master data not loaded (fixture format issues)
- ❌ Entity templates not accessible in ERPNext
- ❌ No integration with CoA creation workflow
- ❌ RGS browsing interface missing

### Next Priority: Phase 1 Completion
1. **Fix fixture format** for RGS master data loading
2. **Convert rgsmkb_all4EN.json** to proper Frappe format
3. **Load complete RGS dataset** into RGS Classification DocType
4. **Build RGS browser interface** for code selection
5. **Test master data access** and search functionality

---

## Lessons Learned and Implementation Guide

### Analysis of Existing Dutch CoA Implementation

ERPNext includes a non-RGS compliant Dutch Chart of Accounts (`nl_grootboekschema.json`) that reveals important patterns and issues:

#### ✅ **Good Practices from Existing Implementation:**
```json
Tree Structure Example:
"VASTE ACTIVA, EIGEN VERMOGEN, LANGLOPEND VREEMD VERMOGEN EN VOORZIENINGEN": {
    "EIGEN VERMOGEN": {
        "Aandelenkapitaal": {
            "account_type": "Equity"
        },
        "root_type": "Equity"
    },
    "root_type": "Equity"
}
```

- **Hierarchical Structure**: Proper nesting with parent-child relationships
- **Dutch Language Support**: Native language account names
- **Specific Account Types**: Detailed account_type mappings for ERPNext integration
- **Business Context**: Industry-specific accounts (retail, manufacturing)

#### ❌ **Issues Identified in Existing Implementation:**

**1. Incorrect Root Type Classifications:**
```json
// WRONG: Provisions classified as Equity instead of Liability
"VOORZIENINGEN": {
    "Garantieverplichtingen": {
        "account_type": "Equity"  // Should be "Liability"
    },
    "root_type": "Equity"       // Should be "Liability"
}

// WRONG: Mixed classifications
"KORTLOPENDE SCHULDEN": {
    "root_type": "Liability"    // Correct
    "TUSSENREKENINGEN": {
        "account_type": "Cash"   // Incorrect for all sub-accounts
    }
}
```

**2. Asset/Liability/Equity Confusion:**
- Provisions (Voorzieningen) incorrectly classified as Equity instead of Liability
- Intermediate accounts (Tussenrekeningen) all marked as "Cash" regardless of nature
- Long-term debt components sometimes misclassified

**3. Missing RGS Compliance:**
- No standardized account numbers
- No connection to official Dutch reporting requirements
- No entity-specific templates (ZZP vs BV requirements differ significantly)

### Critical Lessons Learned from RGS MKB Development

#### **1. Docker and Build Process Lessons**

**Challenge: Custom App Building in Docker**
```bash
# OBSOLETE APPROACH: Direct local path references (development only)
docker buildx bake custom --set custom.args.APPS_JSON_BASE64=...

# ROOT CAUSE: Local paths should only be used for rapid development iteration
# PRODUCTION SOLUTION: Use GitHub URLs in apps.json for stable deployment
# apps.json with GitHub URL:
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15"
  },
  {
    "url": "https://github.com/erjeve/nl_erpnext_rgs_mkb",
    "branch": "main"
  }
]
```

**Lesson**: Production builds should always use GitHub URLs for reproducibility and version control.

**Challenge: Profile-Based Deployment**
```bash
# WORKING APPROACH: Use profiles for specific deployments
docker compose --profile rgs up -d

# BENEFIT: Separates development (rgs profile) from production (default profile)
```

**Lesson**: Profile-based architecture enables clean separation of environments.

#### **2. Frappe Framework Integration Lessons**

**Challenge: Fixture Format Requirements**
```python
# FAILED: Large JSON arrays cause memory issues during migration
"fixtures": [
    "fixtures/rgs_definitions.json",     # 5000+ records = failure
    "fixtures/rgs_selections.json"       # Large datasets = timeout
]

# SOLUTION: Progressive fixture loading
"fixtures": [
    "fixtures/custom_field.json",        # Start with structure
    "fixtures/rgs_classification.json"   # Load data separately if needed
]
```

**Lesson**: Break large datasets into manageable chunks; prioritize DocType structure over data loading.

**Challenge: Tree Structure Implementation**
```python
# WRONG: Obsolete NestedSet fields
class RGSClassification(Document):
    def __init__(self):
        self.lft = 0  # Obsolete in modern Frappe
        self.rgt = 0  # Causes AttributeError

# CORRECT: Parent-child relationships only  
{
    "doctype": "RGS Classification",
    "parent_rgs_classification": "14000",  # Simple parent reference
    "is_group": 1                          # Group indicator
}
```

**Lesson**: Modern Frappe uses simple parent-child relationships; avoid obsolete NestedSet fields.

#### **3. Data Architecture Lessons**

**Challenge: Primary Key Selection**
```python
# The offical Reference Classification System of Financial Information uses a so called "RGS Code"
naming_rule: "rgsCode" # is the reference code for officially defined types of financial information, but not often used to indicate accounts in bookkeeping

# WRONG: Using unstable identifiers
naming_rule: "gsReferentienr"  # Is not guaranteed to be consistently linked to a rgsCode and might eventually change between RGS versions

# CORRECT: Using stable 5 digit identifier for the official subset that has been defined for use by SME companies (Dutch MKB) and will be consistently linked to its rgsCode
naming_rule: "rgsReknr"  # Stable 5-digit decimal, never changes and follows a decimal account numbering scheme commonly used in SME accounting.   

each rgsReknr also has a rgsOms
```

**Lesson**: Always use the most stable identifier as primary key for master data.

**Challenge: Field Mapping Accuracy**
```python
# WRONG: Invented field names
"rgsEenheid": "..."  # Does not exist in official RGS

# CORRECT: Official field mappings from attributes.csv
"rgsNivo": "..."     # Official hierarchy field
"rgsDc": "..."       # Official debit/credit indicator
```

**Lesson**: Always use official documentation sources; never invent field names.

#### **4. Multi-Source Integration Lessons**

**Discovery: Three-Document Architecture**
```
Official RGS Implementation Requires:
1. rgsmkb_all4EN.json     → Canonical dataset (~5,000 records)
2. attributes.csv         → Field specifications and characteristics  
3. 20210913 RGS labels.csv → Translation and legal basis mapping
```

**Lesson**: Complex standards require multiple authoritative sources; design for multi-source integration.

#### **5. Account Type Mapping Lessons**

**Challenge: ERPNext Account Type Classification**
```python
# RGS codes must map correctly to ERPNext account types
def determine_account_type_from_rgs_code(rgs_code, root_type, concepts):
    """
    Map RGS codes to ERPNext account types using multiple criteria
    """
    # Use RGS code patterns
    if rgs_code.startswith('BVLMKAS'):
        return "Cash"
    elif rgs_code.startswith('BVLMBAN'):
        return "Bank"
    elif rgs_code.startswith('BKLSCH'):
        return "Payable"
    
    # Use translation concepts for complex cases
    if 'Bank' in concepts:
        return "Bank"
    elif 'Receivable' in concepts:
        return "Receivable"
    
    # Fall back to root_type defaults
    return DEFAULT_ACCOUNT_TYPES[root_type]
```

**Lesson**: Account type mapping requires multiple information sources and fallback logic.

#### **6. Legal Compliance Lessons**

**Discovery: Entity-Specific Requirements**
```python
# Different entity types have different mandatory accounts
ZZP_REQUIRED = [
    "20010",  # Capital account  
    "28090"   # Retained earnings
]

BV_REQUIRED = [
    "20010",  # Share capital
    "20020",  # Share premium
    "14010"   # Current account holders (if applicable)
]

COOPERATIVE_REQUIRED = [
    "14010",  # Member current accounts (mandatory)
    "20010",  # Member equity contributions
    "28090"   # Cooperative reserves
]
```

**Lesson**: Legal compliance requires entity-specific account templates, not one-size-fits-all.

### Best Practices Derived from Experience

#### **1. Development Process**

**✅ Progressive Implementation:**
1. Start with minimal viable structure (DocTypes only)
2. Add custom fields to existing ERPNext DocTypes  
3. Load master data in small, manageable chunks
4. Test integration points thoroughly
5. Add business logic incrementally

**✅ Git Workflow:**
```bash
# Commit frequently with descriptive messages
git commit -m "Fix AttributeError by removing obsolete lft/rgt references"
git commit -m "Temporarily disable large fixtures for clean migration"
```

#### **2. Docker Development**

**✅ Environment Separation:**
```yaml
# Use profiles for different deployment scenarios
profiles:
  rgs:
    services: [backend, frontend, db]  # Development
  production:
    services: [all]                     # Full production stack
```

**✅ Build Context Management:**
```bash
# Always copy apps to build context
cp -r /path/to/custom_app /opt/frappe_docker/
```

#### **3. Data Quality**

**✅ Multiple Validation Layers:**
```python
def validate_rgs_compliance(account_doc):
    """Multi-layer validation"""
    # 1. Structural validation
    if not account_doc.account_number:
        frappe.throw("Account number required for RGS compliance")
    
    # 2. RGS format validation  
    if not re.match(r'^\d{5}$', account_doc.account_number):
        frappe.throw("Account number must be 5-digit RGS format")
    
    # 3. Legal compliance validation
    validate_entity_specific_requirements(account_doc)
```

#### **4. User Experience**

**✅ Progressive Disclosure:**
- Start with simple entity templates
- Offer customization options for power users
- Provide guided setup for beginners
- Include extensive help documentation

### Implementation Checklist

**Phase 1: Foundation ✅ COMPLETED**
- [x] DocType structure established
- [x] Custom fields added to Account DocType
- [x] Docker build process working
- [x] App successfully installed in ERPNext
- [x] Basic fixture loading functional

**Phase 2: Data Integration (NEXT)**
- [ ] Convert rgsmkb_all4EN.json to proper fixtures
- [ ] Implement field mapping from attributes.csv
- [ ] Add translation support from labels CSV
- [ ] Create entity-specific templates

**Phase 3: Business Logic**
- [ ] Account validation rules
- [ ] Template selection workflow
- [ ] Multi-member accounting features
- [ ] Reporting integration

**Phase 4: Testing & Deployment**
- [ ] Comprehensive test suite
- [ ] Performance optimization
- [ ] Production deployment guide
- [ ] User documentation

---

## Key Decisions & Constraints

### Architecture Decisions
- **Read-only RGS data**: Users select, never create RGS codes
- **ERPNext CoA integration**: Leverage existing template system
- **Template-based approach**: Predefined + customizable templates
- **Validation-first**: Ensure compliance at all stages

### Technical Constraints
- **Frappe fixture format**: Must convert existing JSON properly
- **ERPNext compatibility**: Work within v15 framework constraints
- **Performance**: ~5,000 RGS records must be searchable
- **Data integrity**: Master data must remain unchanged

### Business Constraints
- **Legal compliance**: Must meet Dutch regulatory requirements
- **User flexibility**: Allow customization without breaking compliance
- **Industry coverage**: Support all major Dutch entity types
- **Future-proofing**: Design for RGS version updates

---

*This specification serves as the north star for nl_erpnext_rgs_mkb development. All implementation decisions should align with these core principles and success criteria.*
