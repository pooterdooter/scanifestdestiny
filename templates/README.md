# Example Templates

This folder contains example CSV templates for metadata extraction.

## Templates

### `extraction_template.csv` - Universal Template

A comprehensive template covering common fields across multiple document types:

| Field | Use Case |
|-------|----------|
| Document Type | Invoices, bills, receipts, EOBs, statements |
| Document Date | Date on the document |
| Vendor/Provider | Company, healthcare provider, utility company |
| Account Number | Customer/member account |
| Invoice/Reference Number | Invoice #, confirmation #, reference # |
| Amount Due | Outstanding balance |
| Amount Paid | Payment amount |
| Due Date | Payment due date |
| Service Date | Date of service (healthcare, utilities) |
| Description | Brief description of document contents |
| Patient/Member Name | Healthcare documents |
| Policy Number | Insurance documents |
| Claim Number | Insurance claims, EOBs |
| Project Number | Business/contractor invoices |
| Notes | Additional extracted information |

## Usage

### Extract using the universal template:

```bash
# Windows
.\run.bat extract "C:\Scans" --template templates\extraction_template.csv -o results.csv

# macOS/Linux
./run.sh extract "/path/to/scans" --template templates/extraction_template.csv -o results.csv
```

### Create a custom template:

```bash
# Simple invoice template
.\run.bat extract --create-template "Vendor,Invoice Number,Date,Amount" -o my_template.csv

# Healthcare template
.\run.bat extract --create-template "Provider,Patient,Service Date,Claim Number,Amount Billed,Amount Owed" -o healthcare_template.csv
```

### Tips

- Not all fields will be found in every document - empty cells are normal
- The AI will extract what it can find and leave others blank
- Use simpler templates (fewer columns) for faster, more accurate extraction
- Review results and adjust your template based on what fields actually appear in your documents
