import os
import pandas as pd
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from datetime import datetime


def make_qr(text, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_H):
    """Generate QR code image"""
    qr = qrcode.QRCode(
        version=1, error_correction=error_correction, box_size=box_size, border=1
    )
    qr.add_data(text)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def create_qr_pdf(df, pdf_file_name):
    """Create QR code PDF labels (Luiz Felipe Almeida Style)"""
    custom_page_size = (2 * inch, 3 * inch)
    
    # Use in-memory buffer for deployment, file system for local dev
    if os.environ.get('RENDER'):
        from io import BytesIO
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=custom_page_size)
    else:
        pdf_path = os.path.join("labels_pdf", pdf_file_name)
        c = canvas.Canvas(pdf_path, pagesize=custom_page_size)
    width, height = custom_page_size

    info_list = ["Plot", "Site", "Year", "Sampling Stage/Depth", "Project", "Treatment"]

    for _, row in df.iterrows():
        qr_code = make_qr(str(row.get("ID", "NO_ID")))
        qr_image = f"temp_{row.get('ID', 'temp')}.png"
        qr_code.save(qr_image)

        c.drawImage(
            qr_image, inch / 2, height - 1.25 * inch, width=1 * inch, height=1 * inch
        )
        for iter, attr in enumerate(info_list):
            if attr == "Plot":
                c.setFont("Helvetica-Bold", 10)
            else:
                c.setFont("Helvetica", 8)
            text_y_position = height - 1.55 * inch - iter * 15
            value = row.get(attr, "N/A")
            c.drawString(inch * 0.1, text_y_position, f"{attr}: {value}")

        c.showPage()
        # Clean up temp QR image
        if os.path.exists(qr_image):
            os.remove(qr_image)
    
    c.save()
    
    if os.environ.get('RENDER'):
        buffer.seek(0)
        return buffer  # Return buffer for in-memory serving
    else:
        return pdf_path  # Return file path for local development


def create_biomass_pdf(df, pdf_file_name, use_qr=False):
    """Create biomass PDF labels (Luiz Rosso Style) with barcode or QR code"""
    page_width = 3
    page_height = 2
    
    # Use in-memory buffer for deployment, file system for local dev
    if os.environ.get('RENDER'):
        from io import BytesIO
        buffer = BytesIO()
        page = canvas.Canvas(buffer)
    else:
        pdf_path = os.path.join("labels_pdf", pdf_file_name)
        page = canvas.Canvas(pdf_path)
    
    page.setPageSize(size=(page_width*inch, page_height*inch))
    
    for i in range(len(df)):
        # Draw border
        page.rect(0.05*inch, (0.05-0.025)*inch, 2.9*inch, 1.9*inch, stroke=1, fill=0)
        
        # Draw text
        page.setFont('Helvetica-Bold', 14)
        page.drawCentredString(1.5*inch, 1.6*inch, str(df.iloc[i]['info1']))
        
        page.setFont('Helvetica-Bold', 12)
        page.drawCentredString(1.5*inch, 1.2*inch, str(df.iloc[i]['info2']))
        
        page.setFont('Helvetica', 10)
        page.drawCentredString(1.5*inch, 0.9*inch, str(df.iloc[i]['info3']))
        
        if use_qr:
            # Draw QR code instead of barcode
            qr_id = str(df.iloc[i]['info1'])
            qr_code = make_qr(qr_id)
            safe_qr_id = qr_id.replace('/', '_').replace('\\', '_').replace(' ', '_')
            qr_image = f"temp_{safe_qr_id}_{i}.png"
            qr_code.save(qr_image)
            
            # Position QR code in the same area as barcode
            qr_size = 0.6*inch
            qr_x = (page_width*inch - qr_size) / 2
            qr_y = 0.2*inch
            page.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
            
            # Clean up temp QR image
            if os.path.exists(qr_image):
                os.remove(qr_image)
        else:
            # Draw barcode (original style)
            b_code128 = code128.Code128(str(df.iloc[i]['info1']),
                                       barHeight=0.4*inch, barWidth=0.7)
            b_code128.lquiet = 0
            b_code128.rquiet = 0
            b_code_start = (page_width/2) - (b_code128.width/inch)/2
            b_code128.drawOn(page, b_code_start*inch, 0.3*inch)
        
        # Draw unique code if available
        if pd.notna(df.iloc[i].get('ucode', '')):
            page.setFont('Helvetica-Bold', 8)
            page.drawCentredString(1.5*inch, 0.08*inch, str(df.iloc[i]['ucode']))
        
        page.showPage()
    
    page.save()
    
    if os.environ.get('RENDER'):
        buffer.seek(0)
        return buffer  # Return buffer for in-memory serving
    else:
        return pdf_path  # Return file path for local development


def create_line_pdf(df, pdf_file_name):
    """Create line-style PDF labels for narrow plastic pieces - column layout with QR in center"""
    page_width = 3
    page_height = 2
    
    # Use in-memory buffer for deployment, file system for local dev
    if os.environ.get('RENDER'):
        from io import BytesIO
        buffer = BytesIO()
        page = canvas.Canvas(buffer)
    else:
        pdf_path = os.path.join("labels_pdf", pdf_file_name)
        page = canvas.Canvas(pdf_path)
    
    page.setPageSize(size=(page_width*inch, page_height*inch))
    
    for i in range(len(df)):
        # Draw a thin border for reference (optional)
        page.rect(0.05*inch, 0.05*inch, 2.9*inch, 1.9*inch, stroke=1, fill=0)
        
        # Define layout: QR code in center, text columns on sides
        center_x = 1.5*inch  # Center of the 3-inch width
        center_y = 1.0*inch  # Center of the 2-inch height
        
        # QR code settings - use ucode if available, fallback to info1
        qr_data = str(df.iloc[i].get('ucode', df.iloc[i].get('info1', 'ID')))
        qr_code = make_qr(qr_data)
        safe_qr_id = qr_data.replace('/', '_').replace('\\', '_').replace(' ', '_')
        qr_image = f"temp_line_{safe_qr_id}_{i}.png"
        qr_code.save(qr_image)
        
        # QR code in the center of the label
        qr_size = 0.7*inch  # Keep QR code size
        qr_x = center_x - qr_size/2  # Center the QR code horizontally
        qr_y = center_y - qr_size/2  # Center the QR code vertically
        page.drawImage(qr_image, qr_x, qr_y, width=qr_size, height=qr_size)
        
        # Left column - Plot title and ID text (better margins and bigger fonts)
        left_x = 0.15*inch  # Increased margin from border
        
        # Add "Plot" title above the ID
        page.setFont('Helvetica', 10)
        page.drawString(left_x, center_y + 0.2*inch, "Plot")
        
        # Main ID text
        page.setFont('Helvetica-Bold', 14)  # Increased from 12
        id_text = str(df.iloc[i].get('info1', 'ID'))
        page.drawString(left_x, center_y - 0.15*inch, id_text)
        
        # Right column - Concatenated info2 and info3 on same line
        right_x = 2.1*inch  # Moved away from right border (was 2.4*inch)
        
        # Concatenate info2 and info3 on the same line
        info_parts = []
        if df.iloc[i].get('info2') and str(df.iloc[i]['info2']).strip():
            info_parts.append(str(df.iloc[i]['info2']))
        if df.iloc[i].get('info3') and str(df.iloc[i]['info3']).strip():
            info_parts.append(str(df.iloc[i]['info3']))
        
        if info_parts:
            page.setFont('Helvetica-Bold', 12)  # Bold font for concatenated info
            combined_info = " ".join(info_parts)  # Separate with pipe symbol
            page.drawString(right_x, center_y + 0.2*inch, combined_info)
        
        # Ucode display
        if df.iloc[i].get('ucode') and str(df.iloc[i]['ucode']).strip():
            page.setFont('Helvetica', 10)  # Increased from 8
            ucode_text = f"Code: {str(df.iloc[i]['ucode'])}"
            page.drawString(right_x, center_y - 0.15*inch, ucode_text)
        
        # Clean up temp QR image
        if os.path.exists(qr_image):
            os.remove(qr_image)
        
        page.showPage()
    
    page.save()
    
    if os.environ.get('RENDER'):
        buffer.seek(0)
        return buffer  # Return buffer for in-memory serving
    else:
        return pdf_path  # Return file path for local development


def create_qr_dataframe(project_name, site_name, study_year, num_blocks, treatments, sampling_stage):
    """Create DataFrame for QR code labels"""
    data = {
        "Project": [], "Site": [], "Year": [], "Block": [],
        "Treatment": [], "Plot": [], "Sampling Stage/Depth": [],
        "Experiment Type": [], "ID": []
    }
    
    treatment_list = [t.strip() for t in treatments.split(',')] if treatments else ["Treatment"]
    
    for block in range(1, (num_blocks or 1) + 1):
        for i, treatment in enumerate(treatment_list):
            plot = f"{block}{str(i+1).zfill(2)}"
            
            data["Project"].append(project_name or "Project")
            data["Site"].append(site_name or "Site")
            data["Year"].append(study_year or 2024)
            data["Block"].append(block)
            data["Treatment"].append(treatment)
            data["Plot"].append(plot)
            data["Sampling Stage/Depth"].append(sampling_stage or "V4")
            data["Experiment Type"].append("Randomized Complete Block")
            
            id_parts = [
                project_name or "Project", 
                site_name or "Site", 
                str(study_year or 2024), 
                f"Block-{block}",
                f"Treat-{treatment}",
                sampling_stage or "V4",
                plot
            ]
            data["ID"].append("_".join(filter(None, id_parts)))
    
    return pd.DataFrame(data) 
