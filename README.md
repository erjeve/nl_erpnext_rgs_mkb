# Dutch RGS MKB for ERPNext

A comprehensive ERPNext app that provides Dutch RGS (Reference Classification System) MKB 3.7 compliance for Chart of Accounts.

## Features

- **RGS Classification Tree**: Complete hierarchical view of Dutch RGS MKB 3.7 codes
- **Entity-Specific Templates**: Pre-configured templates for ZZP, BV, EZ, and SVC entities
- **Automatic CoA Generation**: Generate compliant Chart of Accounts based on entity type
- **Custom Fields Integration**: Seamlessly integrates RGS fields with ERPNext Account DocType
- **Compliance Validation**: Ensures accounts meet Dutch financial reporting standards

## Installation

### Using frappe-bench

```bash
bench get-app nl_erpnext_rgs_mkb https://github.com/erjeve/nl_erpnext_rgs_mkb.git
bench install-app nl_erpnext_rgs_mkb --site your-site
```

### Using Docker (frappe_docker)

Add to your `apps.json`:

```json
[
  {"url": "https://github.com/frappe/erpnext", "branch": "version-15"},
  {"url": "https://github.com/erjeve/nl_erpnext_rgs_mkb", "branch": "main"}
]
```

Build with apps included and set `INSTALL_APPS=erpnext,nl_erpnext_rgs_mkb`

## Usage

### 1. RGS Classification

Access **Dutch RGS MKB > RGS Classification** to view the complete hierarchical tree of RGS codes.

### 2. RGS Templates

Access **Dutch RGS MKB > RGS Template** to manage entity-specific Chart of Accounts templates.

### 3. Generate Chart of Accounts

1. Open an RGS Template (e.g., "ZZP_Standard")
2. Click **Actions > Generate CoA**
3. Select your company
4. The app will create all applicable accounts with proper RGS compliance

### 4. Account Integration

All created accounts automatically include RGS custom fields:
- RGS Code
- RGS Nivo (hierarchy level)
- RGS Reference Number

## Entity Types Supported

- **ZZP**: Zelfstandig Zonder Personeel (Sole Trader without Personnel)
- **EZ**: Eenmanszaak / VOF (Sole Proprietorship / Partnership)
- **BV**: Besloten Vennootschap (Private Limited Company)
- **SVC**: Stichting / Vereniging / Coöperatie (Foundation / Association / Cooperative)

## Data Source

Based on official Dutch RGS MKB 3.7 standard with 1,598+ account definitions.

## License

MIT License

## Support

For issues and questions, please use the GitHub Issues tracker.
