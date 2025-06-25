import os
import base64
import io
import pandas as pd
from datetime import datetime
from dash import Input, Output, State, callback_context, dash_table, html, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from utils import create_qr_pdf, create_biomass_pdf, create_qr_dataframe


def register_callbacks(app, pdf_storage):
    """Register all callbacks for the Dash application"""
    
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
                            id="download-pdf-btn",
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

    # Download callback using Dash's dcc.Download
    @app.callback(
        Output("download-pdf", "data"),
        [Input("download-pdf-btn", "n_clicks")],
        [State("current-csv-data", "data"),
         State("current-label-options", "data")],
        prevent_initial_call=True
    )
    def download_pdf(n_clicks, csv_data, label_options):
        if not n_clicks or not csv_data or not label_options:
            return None
        
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
            
            # For local development, read the file
            if not os.environ.get('RENDER'):
                # Read the PDF file that was saved locally
                pdf_path = os.path.join("labels_pdf", pdf_filename)
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        pdf_content = f.read()
                else:
                    return None
            else:
                # For deployment, use the in-memory PDF
                pdf_content = pdf_storage.get(pdf_filename)
                if not pdf_content:
                    return None
            
            # Return the download data
            return dcc.send_bytes(pdf_content, pdf_filename)
            
        except Exception as e:
            print(f"Download error: {str(e)}")
            return None 