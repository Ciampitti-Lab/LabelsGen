# Ciampitti Lab Labels Generator

A comprehensive Dash application for generating laboratory labels with QR codes and barcodes, adapted from original work by **Luiz Felipe Almeida** and **Luiz Rosso**.

## Features

### Luiz Felipe Almeida Style (QR Codes)
- Generate QR code labels for tissue and soil samples
- Support for experimental metadata including:
  - Project name, site, year
  - Block and treatment information
  - Sampling stage/depth and fraction
  - Randomized Complete Block and Split-Plot designs

### Biomass Luiz Rosso Style (Barcodes)
- Generate biomass labels with Code128 barcodes
- Support for multiple information fields
- Optional unique codes

## Data Input Methods
- **Manual Entry**: Fill in experiment details through the web interface
- **CSV Upload**: Upload existing CSV files with label data

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Local Usage

1. Run the application:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to `http://127.0.0.1:8050`

3. Select your label style (QR codes or Barcodes)

4. Choose your data input method (Manual or CSV Upload)

5. Fill in the required information or upload your CSV file

6. Generate and download your PDF labels

## File Structure

- `app.py` - Main Dash application
- `requirements.txt` - Python dependencies
- `labels_pdf/` - Directory for generated PDF files (created automatically)

## CSV Format Requirements

### For QR Code Labels (Luiz Felipe Almeida Style)
CSV should contain columns: `Project`, `Site`, `Year`, `Block`, `Treatment`, `Plot`, `Sampling Stage/Depth`, `Sampling Fraction`, `ID`

### For Biomass Labels (Luiz Rosso Style)
CSV should contain columns: `biomass_info1`, `biomass_info2`, `biomass_info3`, `biomass_ucode` (optional)

## Credits

This application was developed by **Pedro Cisdeli** and is adapted from original work by:
- **Luiz Felipe Almeida** - QR code label generation system
- **Luiz Rosso** - Biomass barcode label system

## License

This project is open source and available under the CC BY-NC-SA 4.0 license. See the [LICENSE](LICENSE) file for more details.
