import dash
from dash import dcc, html
import dash_bootstrap_components as dbc


def create_layout():
    """Create and return the main application layout"""
    return dbc.Container([
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
        
        # Main Options Section
        html.Div([
            html.H4("Choose Your Method", className="text-center mb-4", style={"color": "#2c3e50", "font-weight": "400"}),
            html.P("Select one of the two options below to generate your labels", 
                  className="text-center text-muted mb-5", style={"font-size": "1.1rem"}),
            
            dbc.Row([
                # Option 1: CSV Upload
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-upload", style={"font-size": "3rem", "color": "#007bff", "margin-bottom": "1rem"}),
                                html.H5("Option 1: Upload CSV File", className="mb-3", style={"color": "#2c3e50", "font-weight": "500"}),
                                html.P("Have an existing CSV file? Upload it here to generate labels quickly.", 
                                      className="text-muted mb-4", style={"font-size": "0.95rem"}),
                                dbc.Button(
                                    [html.I(className="fas fa-cloud-upload-alt me-2"), "Upload CSV File"], 
                                    id="upload-modal-btn", 
                                    color="primary",
                                    size="lg",
                                    className="w-100",
                                    style={"border-radius": "8px", "font-weight": "500"}
                                )
                            ], className="text-center")
                        ], style={"padding": "2rem"})
                    ], className="h-100 shadow-sm", style={"border": "2px solid #e3f2fd", "border-radius": "12px"})
                ], md=6),
                
                # Option 2: Manual Entry
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-edit", style={"font-size": "3rem", "color": "#28a745", "margin-bottom": "1rem"}),
                                html.H5("Option 2: Manual Data Entry", className="mb-3", style={"color": "#2c3e50", "font-weight": "500"}),
                                html.P("Prefer to create data manually? Fill out the form below to generate custom labels.", 
                                      className="text-muted mb-4", style={"font-size": "0.95rem"}),
                                dbc.Button(
                                    [html.I(className="fas fa-edit me-2"), "Start Manual Entry"], 
                                    id="manual-entry-modal-btn", 
                                    color="success",
                                    size="lg",
                                    className="w-100",
                                    style={"border-radius": "8px", "font-weight": "500"}
                                )
                            ], className="text-center")
                        ], style={"padding": "2rem"})
                    ], className="h-100 shadow-sm", style={"border": "2px solid #e8f5e8", "border-radius": "12px"})
                ], md=6)
            ], className="mb-5")
        ], className="mb-5"),
        
        # Divider
        html.Hr(style={"border": "none", "height": "2px", "background": "linear-gradient(90deg, #007bff, #28a745)", "margin": "3rem 0", "opacity": "0.3"}),
        
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
                                    {"label": "Biomass Luiz Rosso Style", "value": "biomass"},
                                    {"label": "Line Style (Centered for Narrow Plastic)", "value": "line"}
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
        
        # Manual Entry Modal
        dbc.Modal([
            dbc.ModalHeader("Manual Data Entry"),
            dbc.ModalBody([
                # Label Style Selection
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Label Style", className="fw-bold mb-2"),
                        dcc.Dropdown(
                            id="label-style",
                            options=[
                                {"label": "Luiz Felipe Almeida Style (QR Codes)", "value": "qr"},
                                {"label": "Biomass Luiz Rosso Style (Barcodes/QR)", "value": "barcode"},
                                {"label": "Line Style (Centered for Narrow Plastic)", "value": "line"}
                            ],
                            value="qr",
                            clearable=False,
                            style={"font-size": "14px"}
                        )
                    ], md=12)
                ], className="mb-4"),
                
                # QR Code Entry Form (shown by default)
                html.Div([
                    html.H6("QR Code Labels", className="mb-3", style={"color": "#2c3e50"}),
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
                            dbc.Input(id="study-year", type="number", value=2025, min=2020, max=2030,
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
                    ], className="mb-4")
                ], id="modal-qr-section"),
                
                # Biomass Entry Form (hidden by default)
                html.Div([
                    html.H6("Biomass Labels", className="mb-3", style={"color": "#2c3e50"}),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Output Type", className="fw-bold"),
                            dbc.RadioItems(
                                id="modal-biomass-output-type",
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
                            dbc.Input(id="modal-biomass-info1", placeholder="Primary identifier",
                                    style={"border-radius": "6px"})
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Info 2", className="fw-bold"),
                            dbc.Input(id="modal-biomass-info2", placeholder="Secondary info",
                                    style={"border-radius": "6px"})
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Info 3", className="fw-bold"),
                            dbc.Input(id="modal-biomass-info3", placeholder="Tertiary info",
                                    style={"border-radius": "6px"})
                        ], md=3),
                        dbc.Col([
                            dbc.Label("Unique Code (optional)", className="fw-bold"),
                            dbc.Input(id="modal-biomass-ucode", placeholder="Optional unique code",
                                    style={"border-radius": "6px"})
                        ], md=3)
                    ], className="mb-4"),
                    
                    html.Div([
                        dbc.Button("Add Row", id="modal-add-row-btn", color="outline-primary", 
                                 className="me-3", style={"border-radius": "6px"}),
                    ], className="text-center mb-3"),
                    
                    html.Hr(style={"border-top": "1px solid #dee2e6", "margin": "2rem 0"}),
                    html.Div(id="modal-biomass-table-container")
                ], id="modal-biomass-section", style={"display": "none"})
            ]),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-manual-modal", className="me-2", color="secondary"),
                dbc.Button("Generate CSV Data", id="modal-generate-csv-btn", color="success")
            ])
        ], id="manual-entry-modal", size="xl"),
        
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
                        # Loading overlay (hidden by default)
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.I(className="fas fa-spinner fa-spin", style={
                                        "font-size": "2rem", 
                                        "color": "#007bff", 
                                        "margin-bottom": "1rem"
                                    }),
                                    html.H6("Generating PDF...", style={
                                        "color": "#2c3e50", 
                                        "font-weight": "500",
                                        "margin-bottom": "0.5rem"
                                    }),
                                    html.P("Please wait while we create your labels", style={
                                        "color": "#6c757d", 
                                        "font-size": "0.9rem",
                                        "margin": "0"
                                    })
                                ], style={
                                    "text-align": "center",
                                    "padding": "2rem"
                                })
                            ], style={
                                "position": "absolute",
                                "top": "0",
                                "left": "0",
                                "right": "0", 
                                "bottom": "0",
                                "background-color": "rgba(255, 255, 255, 0.95)",
                                "display": "flex",
                                "align-items": "center",
                                "justify-content": "center",
                                "z-index": "1000",
                                "border-radius": "10px"
                            })
                        ], id="loading-overlay", style={"display": "none"}),
                        
                        html.Div(id="csv-viewer-content", 
                                children=[
                                    html.P("Upload CSV or generate data to view here", 
                                          className="text-center text-muted py-5", 
                                          style={"font-style": "italic"})
                                ])
                    ], style={"max-height": "400px", "overflow-y": "auto", "padding": "1rem", "position": "relative"})
                ], className="shadow-sm h-100", style={"border": "none", "border-radius": "10px"})
            ], md=6),
            
            # PDF Preview
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H6("PDF Preview", className="mb-0", style={"color": "#2c3e50", "font-weight": "500"})
                            ], md=8),
                            dbc.Col([
                                html.Div(style={"height": "31px"})  # Invisible spacer to match button height
                            ], md=4)
                        ])
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
        
        # Download component for PDF downloads
        dcc.Download(id="download-pdf")
    ], fluid=True, style={
        "background-color": "#ffffff", 
        "min-height": "100vh", 
        "padding": "1rem 0",
        "font-family": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    }) 