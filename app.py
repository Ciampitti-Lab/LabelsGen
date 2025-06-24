import os
import glob
import pandas as pd
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
import base64
import io
import zipfile
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "🌱 CiampittiLab Labels Generator"
app.config.suppress_callback_exceptions = True

# Create necessary directories (only for local development)
if not os.environ.get('RENDER'):  # Only create dirs locally, not on Render
    os.makedirs("labels_pdf", exist_ok=True)

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



# Enhanced app layout
app.layout = dbc.Container([
    # Header Section
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("🌱 CiampittiLab Labels Generator", 
                       className="text-center mb-3", 
                       style={
                           "color": "#2c3e50", 
                           "font-weight": "300", 
                           "font-size": "3rem",
                           "letter-spacing": "2px"
                       }),
                html.Hr(style={
                    "border": "none",
                    "height": "2px",
                    "background": "linear-gradient(90deg, #3498db, #2ecc71)",
                    "width": "300px",
                    "margin": "0 auto"
                }),
                html.P("Label generation for agricultural research", 
                      className="text-center text-muted mt-3 mb-5", 
                      style={"font-size": "1.1rem", "font-weight": "300"})
            ], style={"padding": "3rem 0 2rem 0"})
        ])
    ]),
    
    # Control Panel
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Label Style", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="label-style",
                                options=[
                                    {"label": "Luiz Felipe Almeida Style (QR Codes)", "value": "qr"},
                                    {"label": "Biomass Luiz Rosso Style (Barcodes/QR)", "value": "barcode"}
                                ],
                                value="qr",
                                clearable=False,
                                style={"font-size": "14px"}
                            )
                        ], md=6),
                        dbc.Col([
                            dbc.Label("CSV Upload", className="fw-bold mb-2"),
                            html.Div([
                                dbc.Button(
                                    "Upload CSV File", 
                                    id="upload-modal-btn", 
                                    color="outline-primary",
                                    className="w-100",
                                    style={"border-radius": "8px"}
                                )
                            ])
                        ], md=6)
                    ])
                ], style={"padding": "1.5rem"})
            ], className="mb-4 shadow-sm", style={"border": "none", "border-radius": "12px"})
        ])
    ]),
    
    # Upload Modal
    dbc.Modal([
        dbc.ModalHeader("Upload CSV File"),
        dbc.ModalBody([
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    html.I(className="fas fa-cloud-upload-alt", style={"font-size": "2.5rem", "color": "#6c757d"}),
                    html.Br(),
                    html.P("Drag and drop or click to select a CSV file", 
                          style={"margin": "1rem 0 0 0", "color": "#6c757d", "font-size": "1rem", "text-align": "center", "width": "100%"})
                ], style={
                    "display": "flex", 
                    "flex-direction": "column", 
                    "align-items": "center", 
                    "justify-content": "center",
                    "height": "100%"
                }),
                style={
                    'width': '100%',
                    'height': '150px',
                    'borderWidth': '2px',
                    'borderStyle': 'dashed',
                    'borderRadius': '10px',
                    'borderColor': '#dee2e6',
                    'backgroundColor': '#f8f9fa',
                    'cursor': 'pointer',
                    'display': 'flex'
                },
                multiple=False
            ),
            html.Div(id="upload-feedback", className="mt-3"),
            html.Div(id="upload-data-preview", className="mt-3"),
            
            # Upload Options (shown after file is uploaded)
            html.Div([
                html.Hr(className="my-4"),
                html.H6("Generation Options", className="mb-3", style={"color": "#2c3e50"}),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Label Style", className="fw-bold mb-2"),
                        dcc.Dropdown(
                            id="upload-label-style",
                            options=[
                                {"label": "Luiz Felipe Almeida Style (QR Codes)", "value": "qr"},
                                {"label": "Biomass Luiz Rosso Style", "value": "biomass"}
                            ],
                            value="qr",
                            clearable=False,
                            style={"font-size": "14px"}
                        )
                    ], md=6),
                    dbc.Col([
                        html.Div([
                            dbc.Label("Biomass Output Type", className="fw-bold mb-2"),
                            dbc.RadioItems(
                                id="upload-biomass-output-type",
                                options=[
                                    {"label": "QR Codes", "value": "qr"},
                                    {"label": "Barcodes", "value": "barcode"}
                                ],
                                value="barcode",
                                inline=True
                            )
                        ], id="upload-biomass-options", style={"display": "none"})
                    ], md=6)
                ])
            ], id="upload-options", style={"display": "none"})
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-upload-modal", className="me-2", color="secondary"),
            dbc.Button("Load CSV Data", id="load-csv-btn", color="success", disabled=True)
        ])
    ], id="upload-modal", size="xl"),
    
    # Manual QR Code Input Section
    html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H5("Manual Data Entry - QR Code Labels", className="mb-0", style={"color": "#2c3e50", "font-weight": "400"})
            ]),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Project Name", className="fw-bold"),
                        dbc.Input(id="project-name", placeholder="e.g., Nfix", value="TestProject", 
                                style={"border-radius": "6px"})
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Site Name", className="fw-bold"),
                        dbc.Input(id="site-name", placeholder="e.g., Topeka", value="TestSite",
                                style={"border-radius": "6px"})
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Study Year", className="fw-bold"),
                        dbc.Input(id="study-year", type="number", value=2024, min=2020, max=2030,
                                style={"border-radius": "6px"})
                    ], md=4)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Number of Blocks", className="fw-bold"),
                        dbc.Input(id="num-blocks", type="number", value=3, min=1, max=20,
                                style={"border-radius": "6px"})
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Treatments (comma-separated)", className="fw-bold"),
                        dbc.Input(id="treatments", placeholder="Treatment1, Treatment2, Control", 
                                value="Control,Treatment1,Treatment2", style={"border-radius": "6px"})
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Sampling Stage", className="fw-bold"),
                        dbc.Input(id="sampling-stage", placeholder="e.g., V4, R2, R6", value="V4",
                                style={"border-radius": "6px"})
                    ], md=4)
                ], className="mb-4"),
                
                html.Div([
                    dbc.Button("Generate CSV Data", id="generate-csv-btn", color="success", 
                             size="lg", className="px-5", 
                             style={"border-radius": "8px", "font-weight": "500"})
                ], className="text-center")
            ], style={"padding": "2rem"})
        ], className="mb-4 shadow-sm", style={"border": "none", "border-radius": "12px"})
    ], id="qr-section"),
    
    # Manual Biomass Input Section
    html.Div([
        dbc.Card([
            dbc.CardHeader([
                html.H5("Manual Data Entry - Biomass Labels", className="mb-0", style={"color": "#2c3e50", "font-weight": "400"})
            ]),
            dbc.CardBody([
                # QR vs Barcode choice for biomass style
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Output Type", className="fw-bold"),
                        dbc.RadioItems(
                            id="biomass-output-type",
                            options=[
                                {"label": "QR Codes", "value": "qr"},
                                {"label": "Barcodes", "value": "barcode"}
                            ],
                            value="barcode",
                            inline=True,
                            style={"margin-top": "0.5rem"}
                        )
                    ], md=12)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Info 1 (Main ID)", className="fw-bold"),
                        dbc.Input(id="biomass-info1", placeholder="Primary identifier",
                                style={"border-radius": "6px"})
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Info 2", className="fw-bold"),
                        dbc.Input(id="biomass-info2", placeholder="Secondary info",
                                style={"border-radius": "6px"})
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Info 3", className="fw-bold"),
                        dbc.Input(id="biomass-info3", placeholder="Tertiary info",
                                style={"border-radius": "6px"})
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Unique Code (optional)", className="fw-bold"),
                        dbc.Input(id="biomass-ucode", placeholder="Optional unique code",
                                style={"border-radius": "6px"})
                    ], md=3)
                ], className="mb-4"),
                
                html.Div([
                    dbc.Button("Add Row", id="add-row-btn", color="outline-primary", 
                             className="me-3", style={"border-radius": "6px"}),
                    dbc.Button("Generate CSV Data", id="generate-biomass-csv-btn", color="success", 
                             disabled=True, style={"border-radius": "6px", "font-weight": "500"})
                ], className="text-center mb-3"),
                
                html.Hr(style={"border-top": "1px solid #dee2e6", "margin": "2rem 0"}),
                html.Div(id="biomass-table-container")
            ], style={"padding": "2rem"})
        ], className="mb-4 shadow-sm", style={"border": "none", "border-radius": "12px"})
    ], id="biomass-section", style={"display": "none"}),
    
    # Data and Preview Section
    dbc.Row([
        # CSV Data Viewer
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H6("Data Viewer", className="mb-0", style={"color": "#2c3e50", "font-weight": "500"})
                        ], md=8),
                        dbc.Col([
                            html.Div([
                                dbc.Button("Generate PDF", id="generate-pdf-btn", color="primary", size="sm", 
                                         disabled=True, style={"border-radius": "6px", "font-weight": "500"})
                            ], className="text-end", id="pdf-btn-container")
                        ], md=4)
                    ])
                ]),
                dbc.CardBody([
                    # Progress bar (hidden by default)
                    html.Div([
                        html.P("Generating PDF...", className="text-center mb-2", style={"color": "#2c3e50", "font-weight": "500"}),
                        dbc.Progress(id="pdf-progress", value=0, style={"height": "20px"}, className="mb-3")
                    ], id="progress-container", style={"display": "none"}),
                    
                    html.Div(id="csv-viewer-content", 
                            children=[
                                html.P("Upload CSV or generate data to view here", 
                                      className="text-center text-muted py-5", 
                                      style={"font-style": "italic"})
                            ])
                ], style={"max-height": "400px", "overflow-y": "auto", "padding": "1rem"})
            ], className="shadow-sm h-100", style={"border": "none", "border-radius": "10px"})
        ], md=6),
        
        # PDF Preview
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H6("PDF Preview", className="mb-0", style={"color": "#2c3e50", "font-weight": "500"})
                ]),
                dbc.CardBody([
                    html.Div(id="pdf-viewer-content", 
                            children=[
                                html.P("Generate labels to preview PDF", 
                                      className="text-center text-muted py-5", 
                                      style={"font-style": "italic"})
                            ])
                ], style={"padding": "1rem"})
            ], className="shadow-sm h-100", style={"border": "none", "border-radius": "10px"})
        ], md=6)
    ], className="mb-4"),
    
    # Results area
    html.Div(id="results-area"),
    
    # Credits Section
    html.Hr(style={"border": "none", "height": "1px", "background-color": "#dee2e6", "margin": "3rem 0 2rem 0"}),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Development Credits", className="text-center mb-3", 
                           style={"color": "#2c3e50", "font-weight": "500"}),
                    html.Div([
                        html.P([
                            "Developed by ",
                            html.A("Pedro Cisdeli", href="https://github.com/cisdeli/", 
                                  target="_blank", style={"color": "#007bff", "text-decoration": "none"}),
                            " | Adapted from ",
                            html.A("Luiz Felipe Almeida", href="https://github.com/luizfelipeaa", 
                                  target="_blank", style={"color": "#007bff", "text-decoration": "none"}),
                            " and ",
                            html.A("Luiz Rosso", href="https://github.com/lhmrosso", 
                                  target="_blank", style={"color": "#007bff", "text-decoration": "none"})
                        ], className="text-center mb-2", style={"font-size": "0.9rem", "margin": "0"}),
                        html.P([
                            html.A("CiampittiLab", href="https://github.com/Ciampitti-Lab", 
                                  target="_blank", style={"color": "#6c757d", "text-decoration": "none"}),
                            " - Purdue University"
                        ], className="text-center text-muted", style={"font-size": "0.8rem", "margin": "0"})
                    ])
                ], style={"padding": "1rem"})
            ], className="shadow-sm", 
            style={
                "border": "none", 
                "border-radius": "8px", 
                "background-color": "#f8f9fa"
            })
        ], md=8, lg=6, className="mx-auto")
    ], className="mb-4"),
    
    # Store components
    dcc.Store(id="stored-data"),
    dcc.Store(id="biomass-data-store", data=[]),
    dcc.Store(id="current-csv-data"),
    dcc.Store(id="current-label-options"),
    
    # Interval component for progress updates
    dcc.Interval(id="progress-interval", interval=100, n_intervals=0, disabled=True)
], fluid=True, style={
    "background-color": "#ffffff", 
    "min-height": "100vh", 
    "padding": "1rem 0",
    "font-family": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
})

# Modal callbacks
@app.callback(
    Output("upload-modal", "is_open"),
    [Input("upload-modal-btn", "n_clicks"), Input("close-upload-modal", "n_clicks"), Input("load-csv-btn", "n_clicks")],
    [State("upload-modal", "is_open")],
)
def toggle_modal(n1, n2, n3, is_open):
    if n1 or n2 or n3:
        return not is_open
    return is_open

# Upload style options callback
@app.callback(
    Output("upload-biomass-options", "style"),
    [Input("upload-label-style", "value")]
)
def toggle_upload_biomass_options(style):
    if style == "biomass":
        return {"display": "block"}
    return {"display": "none"}

# Callback to show/hide sections based on label style
@app.callback(
    [Output("qr-section", "style"),
     Output("biomass-section", "style")],
    [Input("label-style", "value")]
)
def toggle_sections(label_style):
    if label_style == "qr":
        return {"display": "block"}, {"display": "none"}
    else:
        return {"display": "none"}, {"display": "block"}

# Callback for adding biomass rows
@app.callback(
    [Output("biomass-table-container", "children"),
     Output("generate-biomass-csv-btn", "disabled"),
     Output("biomass-data-store", "data"),
     Output("biomass-info1", "value"),
     Output("biomass-info2", "value"),
     Output("biomass-info3", "value"),
     Output("biomass-ucode", "value")],
    [Input("add-row-btn", "n_clicks")],
    [State("biomass-info1", "value"),
     State("biomass-info2", "value"),
     State("biomass-info3", "value"),
     State("biomass-ucode", "value"),
     State("biomass-data-store", "data")]
)
def add_biomass_row(n_clicks, info1, info2, info3, ucode, stored_data):
    if not n_clicks or not info1:
        if stored_data:
            # Show existing table
            table = dash_table.DataTable(
                data=stored_data,
                    columns=[
        {"name": "Info 1", "id": "info1"},
        {"name": "Info 2", "id": "info2"},
        {"name": "Info 3", "id": "info3"},
        {"name": "Unique Code", "id": "ucode"}
    ],
                editable=True,
                row_deletable=True,
                style_cell={'textAlign': 'left'},
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
            )
            return table, False, stored_data, info1 or "", info2 or "", info3 or "", ucode or ""
        return html.Div("No data added yet."), True, [], "", "", "", ""
        
    stored_data = stored_data or []
    new_row = {
        "info1": info1 or "",
        "info2": info2 or "",
        "info3": info3 or "",
        "ucode": ucode or ""
    }
    stored_data.append(new_row)
    
    # Create table
    table = dash_table.DataTable(
        data=stored_data,
        columns=[
            {"name": "Info 1", "id": "info1"},
            {"name": "Info 2", "id": "info2"},
            {"name": "Info 3", "id": "info3"},
            {"name": "Unique Code", "id": "ucode"}
        ],
        editable=True,
        row_deletable=True,
        style_cell={'textAlign': 'left'},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'}
    )
    
    return table, False, stored_data, "", "", "", ""

# Callback for file upload
@app.callback(
    [Output("upload-feedback", "children"),
     Output("upload-data-preview", "children"),
     Output("load-csv-btn", "disabled"),
     Output("stored-data", "data"),
     Output("csv-viewer-content", "children"),
     Output("upload-options", "style")],
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")]
)
def process_upload(contents, filename):
    default_csv_viewer = html.P("Upload CSV or generate data to view here", 
                               className="text-center text-muted py-5", 
                               style={"font-style": "italic"})
    
    if contents is None:
        return "", "", True, None, default_csv_viewer, {"display": "none"}
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            
            feedback = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Successfully uploaded {filename} with {len(df)} rows"
            ], color="success")
            
            preview = html.Div([
                html.H6("Data Preview (first 10 rows):", style={"color": "#2c3e50", "font-size": "0.9rem"}),
                dash_table.DataTable(
                    data=df.head(10).to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df.columns],
                    style_cell={
                        'textAlign': 'left', 
                        'padding': '8px',
                        'fontSize': '12px',
                        'fontFamily': 'inherit'
                    },
                    style_header={
                        'backgroundColor': '#f8f9fa', 
                        'color': '#495057', 
                        'fontWeight': '600',
                        'border': '1px solid #dee2e6'
                    },
                    style_data={
                        'backgroundColor': 'white',
                        'border': '1px solid #dee2e6'
                    }
                )
            ])
            
            # CSV Viewer content
            csv_viewer = html.Div([
                html.H6(f"{filename}", style={"color": "#2c3e50", "margin-bottom": "0.5rem", "font-size": "0.9rem"}),
                html.P(f"{len(df)} rows × {len(df.columns)} columns", 
                      style={"color": "#6c757d", "margin-bottom": "1rem", "font-size": "0.8rem"}),
                dash_table.DataTable(
                    data=df.to_dict('records'),
                    columns=[{"name": i, "id": i} for i in df.columns],
                    style_cell={
                        'textAlign': 'left', 
                        'padding': '6px', 
                        'fontSize': '11px',
                        'fontFamily': 'inherit'
                    },
                    style_header={
                        'backgroundColor': '#f8f9fa', 
                        'color': '#495057', 
                        'fontWeight': '600',
                        'border': '1px solid #dee2e6'
                    },
                    style_data={
                        'backgroundColor': 'white',
                        'border': '1px solid #dee2e6'
                    },
                    page_size=10,
                    sort_action="native",
                    filter_action="native"
                )
            ])
            
            return feedback, preview, False, df.to_dict('records'), csv_viewer, {"display": "block"}
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Please upload a CSV file"
            ], color="danger"), "", True, None, default_csv_viewer, {"display": "none"}
            
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-times-circle me-2"),
            f"Error processing file: {str(e)}"
        ], color="danger"), "", True, None, default_csv_viewer, {"display": "none"}

# CSV generation callbacks
@app.callback(
    [Output("csv-viewer-content", "children", allow_duplicate=True),
     Output("current-csv-data", "data"),
     Output("current-label-options", "data"),
     Output("generate-pdf-btn", "disabled")],
    [Input("generate-csv-btn", "n_clicks"),
     Input("generate-biomass-csv-btn", "n_clicks"),
     Input("load-csv-btn", "n_clicks")],
    [State("project-name", "value"),
     State("site-name", "value"),
     State("study-year", "value"),
     State("num-blocks", "value"),
     State("treatments", "value"),
     State("sampling-stage", "value"),
     State("biomass-data-store", "data"),
     State("stored-data", "data"),
     State("upload-label-style", "value"),
     State("upload-biomass-output-type", "value")],
    prevent_initial_call=True
)
def generate_csv_data(qr_clicks, biomass_clicks, upload_clicks, 
                     project_name, site_name, study_year, num_blocks, treatments,
                     sampling_stage, biomass_data, uploaded_data,
                     upload_label_style, upload_biomass_output_type):
    
    ctx = callback_context
    if not ctx.triggered:
        return None, None, None, True
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == "generate-csv-btn":
            # Generate CSV data from manual QR input
            df = create_qr_dataframe(project_name, site_name, study_year, num_blocks, 
                                   treatments, sampling_stage)
            label_options = {"style": "qr", "output_type": "qr"}
            
        elif button_id == "generate-biomass-csv-btn" and biomass_data:
            # Generate CSV data from manual biomass input
            df = pd.DataFrame(biomass_data)
            label_options = {"style": "biomass", "output_type": "barcode"}  # Default to barcode for biomass
            
        elif button_id == "load-csv-btn" and uploaded_data:
            # Load uploaded CSV data
            df = pd.DataFrame(uploaded_data)
            label_options = {
                "style": upload_label_style or "qr",
                "output_type": upload_biomass_output_type or "barcode"
            }
            
        else:
            return None, None, None, True
        
        # Create CSV viewer for generated data
        csv_viewer = html.Div([
            html.H6("CSV Data Ready", style={"color": "#28a745", "margin-bottom": "0.5rem", "font-size": "0.9rem"}),
            html.P(f"{len(df)} rows × {len(df.columns)} columns", 
                  style={"color": "#6c757d", "margin-bottom": "1rem", "font-size": "0.8rem"}),
            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={
                    'textAlign': 'left', 
                    'padding': '6px', 
                    'fontSize': '11px',
                    'fontFamily': 'inherit'
                },
                style_header={
                    'backgroundColor': '#f8f9fa', 
                    'color': '#495057', 
                    'fontWeight': '600',
                    'border': '1px solid #dee2e6'
                },
                style_data={
                    'backgroundColor': 'white',
                    'border': '1px solid #dee2e6'
                },
                page_size=10,
                sort_action="native",
                filter_action="native"
            )
        ])
        
        return csv_viewer, df.to_dict('records'), label_options, False
        
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-times-circle me-2"),
            f"Error generating CSV: {str(e)}"
        ], color="danger"), None, None, True
        
# Progress bar control callback
@app.callback(
    [Output("progress-container", "style"),
     Output("progress-interval", "disabled"),
     Output("pdf-progress", "value", allow_duplicate=True)],
    [Input("generate-pdf-btn", "n_clicks")],
    prevent_initial_call=True
)
def start_progress(n_clicks):
    if n_clicks:
        return {"display": "block"}, False, 0  # Show progress, enable interval, reset progress
    return {"display": "none"}, True, 0

# PDF generation callback
@app.callback(
    [Output("pdf-viewer-content", "children"),
     Output("results-area", "children")],
    [Input("generate-pdf-btn", "n_clicks")],
    [State("current-csv-data", "data"),
     State("current-label-options", "data")],
    prevent_initial_call=True
)
def generate_pdf_from_csv(n_clicks, csv_data, label_options):
    if not n_clicks or not csv_data or not label_options:
        return None, None
    
    try:
        df = pd.DataFrame(csv_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Generate PDF based on options
        if label_options["style"] == "biomass":
            if label_options["output_type"] == "qr":
                pdf_filename = f"biomass_qr_labels_{timestamp}.pdf"
                pdf_result = create_biomass_pdf(df, pdf_filename, use_qr=True)
            else:
                pdf_filename = f"biomass_barcode_labels_{timestamp}.pdf"
                pdf_result = create_biomass_pdf(df, pdf_filename, use_qr=False)
        else:
            pdf_filename = f"qr_labels_{timestamp}.pdf"
            pdf_result = create_qr_pdf(df, pdf_filename)
        
        # Store PDF in memory for deployment
        if os.environ.get('RENDER'):
            pdf_storage[pdf_filename] = pdf_result
        
        # Create PDF viewer content
        pdf_viewer = html.Div([
            html.H6(f"{pdf_filename}", style={"color": "#2c3e50", "margin-bottom": "1rem", "font-size": "0.9rem"}),
            html.Div([
                html.Div([
                    html.I(className="fas fa-file-pdf", style={"font-size": "3rem", "color": "#dc3545", "margin-bottom": "1rem"}),
                    html.H6("PDF Generated Successfully", style={"color": "#2c3e50", "margin-bottom": "0.5rem"}),
                    html.P(f"Generated {len(df)} labels", 
                          style={"color": "#6c757d", "margin-bottom": "1.5rem", "font-size": "0.9rem"}),
                    dbc.Button(
                        [html.I(className="fas fa-download me-2"), "Download PDF"], 
                        href=f"/download/{pdf_filename}", 
                        external_link=True, 
                        color="primary", 
                        size="lg",
                        style={"border-radius": "8px", "font-weight": "500"}
                    ),
                    html.Div([
                        html.A(
                            [html.I(className="fas fa-external-link-alt me-1"), "Open in new tab"], 
                            href=f"/download/{pdf_filename}", 
                            target="_blank",
                            style={"color": "#6c757d", "text-decoration": "none", "font-size": "0.85rem"}
                        )
                    ], className="mt-2")
                ], className="text-center", style={"padding": "2rem"})
            ], style={
                "border": "2px dashed #dee2e6",
                "border-radius": "10px",
                "background-color": "#f8f9fa"
            })
        ])
        
        # Create success alert
        result_alert = dbc.Alert([
            html.H5([
                html.I(className="fas fa-check-circle me-2"),
                "PDF Generated Successfully"
            ], className="alert-heading mb-3", style={"color": "#28a745", "font-weight": "500"}),
            html.P(f"Generated {len(df)} labels", style={"margin-bottom": "1rem", "color": "#155724"}),
            dbc.Button([
                html.I(className="fas fa-download me-2"),
                "Download PDF"
            ], href=f"/download/{pdf_filename}", 
                      external_link=True, color="success", size="lg",
                      style={"border-radius": "8px", "font-weight": "500"})
        ], color="success", style={"border": "none", "border-radius": "10px"})
        
        return pdf_viewer, result_alert
        
    except Exception as e:
        error_alert = dbc.Alert([
            html.I(className="fas fa-times-circle me-2"),
            f"Error generating PDF: {str(e)}"
        ], color="danger")
        
        return None, error_alert

# Progress bar simulation callback
@app.callback(
    [Output("pdf-progress", "value"),
     Output("progress-interval", "disabled", allow_duplicate=True),
     Output("progress-container", "style", allow_duplicate=True)],
    [Input("progress-interval", "n_intervals")],
    prevent_initial_call=True
)
def update_progress(n_intervals):
    # Simulate progress over 3 seconds (30 intervals * 100ms each)
    progress = min(100, n_intervals * 4)
    
    if progress >= 100:
        return 100, True, {"display": "none"}  # Complete progress, stop interval, hide progress
    return progress, False, {"display": "block"}

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

# Global storage for in-memory PDFs (for deployment)
pdf_storage = {}

# Download route
@app.server.route('/download/<filename>')
def download_file(filename):
    import flask
    
    if os.environ.get('RENDER'):
        # Serve from memory on Render
        if filename in pdf_storage:
            return flask.send_file(
                pdf_storage[filename],
                mimetype='application/pdf',
                as_attachment=False,
                download_name=filename
            )
        else:
            flask.abort(404)
    else:
        # Serve from file system locally
        return flask.send_from_directory('labels_pdf', filename, as_attachment=False)

if __name__ == '__main__':
    app.run_server(debug=True) 