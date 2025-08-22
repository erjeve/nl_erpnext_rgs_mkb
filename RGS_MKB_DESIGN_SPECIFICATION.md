# Dutch RGS MKB App - Design Specification

**Version:** 2.0  
**Date:** August 21, 2025  
**Purpose:** ERPNext app for Dutch RGS 3.7+ compliance and Chart of Accounts management with forward compatibility

## Table of Contents
1. [Project Overview](#project-overview)
2. [RGS System Architecture](#rgs-system-architecture)
3. [Core Concept](#core-concept)
4. [Data Architecture](#data-architecture)
5. [User Experience](#user-experience)
6. [Technical Implementation](#technical-implementation)
7. [Modern Frappe Framework Integration](#modern-frappe-framework-integration)
8. [Business Value](#business-value)
9. [Development Phases](#development-phases)
10. [Success Criteria](#success-criteria)

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

#### 1. **rgsCode** (Primary Classification)
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

#### 3. **rgsReknr** (Decimal Account Number) ⭐ **PRIMARY KEY**
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
naming_rule: "rgsReknr"  # Use stable 5-digit identifier as primary key
fields:
  # Core RGS Fields (from attributes.csv)
  - rgs_code: Data (Read-Only, Unique, Searchable, Mandatory)
  - rgs_omskort: Data (Translatable - used as account_name)
  - rgs_reknr: Data (5-digit decimal account number)
  - rgs_dc: Select (null/Debit/Credit - balance_must_be mapping)
  - rgs_nivo: Int (1=Balance/P&L, 2=Main, 3=Sub, 4=Account, 5=Mutation)
  - rgs_omslang: Small Text (Translatable, long description)
  - rgs_oms_engels: Data (Translatable, English description)
  - rgs_sortering: Data (Sort order for logical balance/P&L layout)
  - rgs_omslag: Data (Contra account reference for mixed D/C accounts)
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
  - parent_rgs_classification: Link (Self-referencing for hierarchy)
  - is_group: Check (Derived from rgs_nivo < 5)
  # ERPNext Integration (Derived Fields)
  - erpnext_report_type: Select (Balance Sheet/Profit and Loss)
  - erpnext_root_type: Select (Asset/Liability/Equity/Income/Expense)
  - erpnext_account_type: Select (Bank/Receivable/Payable/Fixed Asset/etc.)
  - concept_mappings: Long Text (JSON from translation CSV)

indexes:
  - rgs_code (hierarchical queries and uniqueness)
  - rgs_reknr (primary key lookup)
  - rgs_nivo, is_group (filtering and tree operations)
  - rgs_status (active/passive/obsolete filtering)
  - entity flags (rgs_zzp, rgs_ez, rgs_bv, rgs_svc) for template creation
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
        # Use rgsReknr as primary key (already 5-digit or needs zero-padding)
        rgs_reknr = str(record.get('rgsReknr', '0')).zfill(5)
        rgs_code = record.get('rgsCode', '')
        
        # Get translation concepts for intelligent ERPNext mapping
        concept_mappings = parse_concept_mappings_from_csv(rgs_code, csv_concepts)
        
        # Determine ERPNext mappings using translation concepts
        report_type = determine_report_type_from_code(rgs_code)
        root_type = determine_root_type_from_rgs_code(rgs_code, concept_mappings)
        account_type = determine_account_type_from_rgs_code(rgs_code, root_type, concept_mappings)
        
        # Build fixture using official field mappings
        fixture = {
            "doctype": "RGS Classification",
            "name": rgs_reknr,  # Primary key
            # Core RGS fields (official mapping)
            "rgs_code": rgs_code,
            "rgs_omskort": record.get('rgsOmskort', ''),
            "rgs_reknr": rgs_reknr,
            "rgs_dc": map_rgs_dc_to_selection(record.get('rgsDc')),
            "rgs_nivo": parse_int_safe(record.get('rgsNivo')),
            "rgs_omslang": record.get('rgsOmslang', ''),
            "rgs_oms_engels": record.get('rgsOmsEngels', ''),
            "rgs_sortering": record.get('rgsSortering', ''),
            "rgs_omslag": record.get('rgsOmslag', ''),
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
            # Tree structure
            "parent_rgs_classification": find_parent_reknr_by_code(rgs_code, source_data),
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

def find_parent_reknr_by_code(rgs_code, source_data):
    """
    Find parent rgsReknr using RGS hierarchical structure
    B → BIva → BIvaKou → BIvaKouOnd (each level removes 3 chars)
    """
    if len(rgs_code) <= 1 or rgs_code in ['B', 'W']:
        return None  # Root level
    
    # Determine parent code by removing last 3-character segment
    if len(rgs_code) <= 4:
        parent_code = rgs_code[0]  # B or W
    else:
        parent_code = rgs_code[:-3]
    
    # Find parent's rgsReknr
    for record in source_data:
        if record.get('rgsCode') == parent_code:
            return str(record.get('rgsReknr', '0')).zfill(5)
    
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
