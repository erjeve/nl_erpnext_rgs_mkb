# Dutch RGS MKB for ERPNext

A comprehensive ERPNext app that provides Dutch RGS (Reference Classification System) MKB 3.7 compliance for Chart of Accounts, enabling SME businesses to meet Dutch financial reporting requirements.

## 🎯 Purpose

This app implements the official Dutch RGS MKB 3.7 standard in ERPNext, providing:
- **Legal Compliance**: Meets Dutch financial reporting requirements (Article 2:362 BW)
- **SME Focus**: Optimized for small and medium enterprises
- **Entity-Specific**: Templates for ZZP, BV, EZ, and SVC legal structures
- **Professional**: Audit-ready Chart of Accounts structure

## ✨ Key Features

### RGS Compliance Engine
- **1,598 Official RGS Codes**: Complete MKB subset with intelligent ERPNext mapping
- **Multi-Factor Classification**: Determines account types using RGS structure, descriptions, and D/C indicators
- **Hierarchical Structure**: Proper tree navigation (B → BIva → BIvaKou)
- **Legal Traceability**: Links to official RGS classification codes

### Entity-Specific Templates
- **ZZP**: Zelfstandig Zonder Personeel (328 applicable accounts)
- **EZ**: Eenmanszaak / VOF (680 applicable accounts)  
- **BV**: Besloten Vennootschap (735 applicable accounts)
- **SVC**: Stichting / Vereniging / Coöperatie (659 applicable accounts)

### ERPNext Integration
- **Smart Mapping**: Automatic determination of `root_type`, `account_type`, `balance_must_be`
- **Custom Fields**: RGS classification seamlessly integrated with Account DocType
- **Template Builder**: Visual interface for Chart of Accounts customization
- **Validation Rules**: Ensures ongoing RGS compliance

### Professional Features
- **Performance Optimized**: Pre-processed fixtures for instant deployment
- **Multi-Language**: Dutch/English translations included
- **Future-Proof**: Designed for RGS version updates (3.8+)
- **Build-Time Processing**: Docker-optimized for production deployment

## 🚀 Installation

### Docker Deployment (Recommended)

The app is optimized for Docker deployment with frappe_docker:

```json
// apps.json
[
  {"url": "https://github.com/frappe/erpnext", "branch": "version-15"},
  {"url": "https://github.com/erjeve/nl_erpnext_rgs_mkb", "branch": "main"}
]
```

```bash
# Build with RGS MKB included
docker buildx bake custom --set custom.args.APPS_JSON_BASE64=$(base64 -w 0 apps.json)

# Deploy with app installation
INSTALL_APPS=erpnext,nl_erpnext_rgs_mkb
```

### Traditional Installation

```bash
# Get the app
bench get-app nl_erpnext_rgs_mkb https://github.com/erjeve/nl_erpnext_rgs_mkb.git

# Install on site
bench install-app nl_erpnext_rgs_mkb --site your-site

# Run post-installation setup
bench --site your-site migrate
```

## 📖 Quick Start

### 1. Company Setup
When creating a new company with country "Netherlands", the system will offer RGS-based CoA templates:
- **Netherlands - ZZP** (Sole Proprietor)
- **Netherlands - BV** (Private Limited)
- **Netherlands - EZ** (Partnership)
- **Netherlands - SVC** (Association/Foundation)

### 2. Browse RGS Codes
Navigate to **Dutch RGS MKB > RGS Classification** to:
- Explore the hierarchical RGS structure
- Search by code or description
- Filter by entity type (ZZP/BV/EZ/SVC)
- View ERPNext mappings

### 3. Create Chart of Accounts
- Select an appropriate RGS template for your entity type
- Customize by adding/removing accounts
- Generate compliant Chart of Accounts
- All accounts maintain RGS classification links

### 4. Account Management
All accounts include RGS custom fields:
- **RGS Code**: Official classification (e.g., "BIvaKou")
- **RGS Number**: SME identifier (e.g., "10101")
- **RGS Description**: Dutch account name
- **ERPNext Integration**: Automatic `root_type`, `account_type` mapping

## 🏢 Dutch Legal Entity Support

| Entity Type | Dutch Name | Description | Accounts |
|-------------|------------|-------------|----------|
| **ZZP** | Zelfstandig Zonder Personeel | Sole Trader without Personnel | 328 |
| **EZ** | Eenmanszaak / VOF | Sole Proprietorship / Partnership | 680 |
| **BV** | Besloten Vennootschap | Private Limited Company | 735 |
| **SVC** | Stichting / Vereniging / Coöperatie | Foundation / Association / Cooperative | 659 |

## 📊 Technical Specifications

### Data Architecture
- **Source**: Official Dutch RGS 3.7 standard (1,598 MKB codes)
- **Processing**: Multi-factor intelligent mapping to ERPNext
- **Distribution**: Root types: Asset (403), Liability (255), Equity (60), Income (283), Expense (597)
- **Performance**: Pre-processed fixtures for sub-30-second deployment

### ERPNext Integration
```python
# Intelligent field mapping
rgsCode → Primary key (hierarchical classification)
rgsReknr → account_number (SME 5-digit identifier)
rgsOmskort → account_name (Dutch description)
rgsDc → balance_must_be (Debit/Credit validation)

# Automatic derivation
root_type: Based on RGS structure + Dutch accounting principles
account_type: Pattern analysis + description keywords + D/C logic
report_type: "Balance Sheet" (B codes) / "Profit and Loss" (W codes)
```

### Architecture Principles
- **Selection, Not Creation**: Users select from official RGS codes
- **Version Resilience**: Stable identifiers across RGS updates
- **Business Extensibility**: Account numbering pattern supports custom sub-accounts
- **Compliance Traceability**: Complete audit trail to official standards

## 📚 Standards & References

### Official Sources
- **RGS 3.7 Standard**: [www.referentiegrootboekschema.nl](https://www.referentiegrootboekschema.nl/)
- **RGS MKB Subset**: [GBNED RGS MKB](https://www.boekhoudplaza.nl/pag_epa/137/RGS_MKB.php)
- **Decimal Scheme**: [RGS Decimal Classification](https://www.boekhoudplaza.nl/cmm/rgs/decimaal_rekeningschema_rgs.php?kz3=2&bra=1&rgsv=&kzUI=J&kzB=MKB)
- **Legal Basis**: Article 2:362 BW (Dutch Civil Code)

### Key Benefits vs. Standard Dutch CoA
| Feature | Standard Dutch ERPNext | RGS MKB App |
|---------|----------------------|-------------|
| **Legal Compliance** | ❌ Not RGS compliant | ✅ Official RGS 3.7 |
| **SME Focus** | ❌ Enterprise-oriented | ✅ SME-optimized templates |
| **Entity Support** | ❌ Generic structure | ✅ ZZP/BV/EZ/SVC specific |
| **Field Mapping** | ❌ Incorrect root_types | ✅ Intelligent classification |
| **Audit Readiness** | ❌ Manual compliance | ✅ Automatic validation |
| **Customization** | ❌ Fixed structure | ✅ Template-based flexibility |

## 🔧 Development & Contribution

### Project Structure
```
nl_erpnext_rgs_mkb/
├── fixtures/
│   ├── rgs_classification.json    # 1,598 enhanced RGS codes
│   └── custom_field.json          # ERPNext Account integration
├── doctype/
│   ├── rgs_classification/        # Master data DocType
│   ├── rgs_template/              # Template management
│   └── rgs_template_item/         # Template details
├── utils/
│   └── enhanced_rgs_mapping.py    # Mapping logic for future updates
└── www/                           # Public pages
```

### Contributing
1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Testing
```bash
# Run with Docker
docker buildx bake custom --set custom.args.APPS_JSON_BASE64=$(base64 -w 0 apps.json)

# Test RGS compliance
bench --site test.local execute "frappe.get_list('RGS Classification', limit=5)"

# Validate Chart of Accounts creation
# Navigate to: Company → Netherlands → Select RGS Template
```

## 📄 License

MIT License - see [LICENSE](license.txt) for details.

## 🆘 Support & Community

- **Issues**: [GitHub Issues](https://github.com/erjeve/nl_erpnext_rgs_mkb/issues)
- **Discussions**: [GitHub Discussions](https://github.com/erjeve/nl_erpnext_rgs_mkb/discussions)
- **ERPNext Community**: [ERPNext Discuss](https://discuss.erpnext.com/)

## 🚀 Roadmap

- [x] **Phase 1**: RGS 3.7 MKB integration with intelligent mapping
- [x] **Phase 2**: Entity-specific templates (ZZP/BV/EZ/SVC)
- [x] **Phase 3**: Docker optimization and distribution strategy
- [ ] **Phase 4**: Advanced compliance features and reporting
- [ ] **Phase 5**: RGS 3.8+ compatibility

---

**Made with ❤️ for the Dutch SME community and ERPNext ecosystem**
