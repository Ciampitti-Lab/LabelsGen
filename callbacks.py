import os
import base64
import io
import pandas as pd
from datetime import datetime
from dash import Input, Output, State, callback_context, dash_table, html, dcc
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from utils import create_qr_pdf, create_biomass_pdf, create_line_pdf, create_qr_dataframe


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

    # Manual entry modal callbacks
    @app.callback(
        Output("manual-entry-modal", "is_open"),
        [Input("manual-entry-modal-btn", "n_clicks"), Input("close-manual-modal", "n_clicks"), Input("modal-generate-csv-btn", "n_clicks")],
        [State("manual-entry-modal", "is_open")],
    )
    def toggle_manual_modal(n1, n2, n3, is_open):
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
        [Output("modal-qr-section", "style"),
         Output("modal-biomass-section", "style")],
        [Input("label-style", "value")]
    )
    def toggle_sections(label_style):
        if label_style == "qr":
            return {"display": "block"}, {"display": "none"}
        else:  # For both "barcode" (biomass) and "line" styles
            return {"display": "none"}, {"display": "block"}

    # Callback for adding biomass rows
    @app.callback(
        [Output("modal-biomass-table-container", "children"),
         Output("biomass-data-store", "data"),
         Output("modal-biomass-info1", "value"),
         Output("modal-biomass-info2", "value"),
         Output("modal-biomass-info3", "value"),
         Output("modal-biomass-ucode", "value")],
        [Input("modal-add-row-btn", "n_clicks")],
        [State("modal-biomass-info1", "value"),
         State("modal-biomass-info2", "value"),
         State("modal-biomass-info3", "value"),
         State("modal-biomass-ucode", "value"),
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
                return table, stored_data, info1 or "", info2 or "", info3 or "", ucode or ""
            return html.Div("No data added yet."), [], "", "", "", ""
            
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
        
        return table, stored_data, "", "", "", ""

    # Callback to control the generate CSV button state
    @app.callback(
        Output("modal-generate-csv-btn", "disabled"),
        [Input("label-style", "value"),
         Input("project-name", "value"),
         Input("site-name", "value"),
         Input("study-year", "value"),
         Input("num-blocks", "value"),
         Input("treatments", "value"),
         Input("sampling-stage", "value"),
         Input("biomass-data-store", "data")]
    )
    def control_generate_button(label_style, project_name, site_name, study_year, 
                               num_blocks, treatments, sampling_stage, biomass_data):
        if label_style in ["barcode", "line"]:  # Biomass or Line mode
            # Enable button if there's biomass data
            return not bool(biomass_data)
        else:  # QR mode
            # Enable button if all required QR fields are filled
            required_fields = [project_name, site_name, study_year, num_blocks, treatments, sampling_stage]
            return not all(field for field in required_fields)

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
        [Input("modal-generate-csv-btn", "n_clicks"),
         Input("load-csv-btn", "n_clicks")],
        [State("project-name", "value"),
         State("site-name", "value"),
         State("study-year", "value"),
         State("num-blocks", "value"),
         State("treatments", "value"),
         State("sampling-stage", "value"),
         State("label-style", "value"),
         State("biomass-data-store", "data"),
         State("stored-data", "data"),
         State("upload-label-style", "value"),
         State("upload-biomass-output-type", "value")],
        prevent_initial_call=True
    )
    def generate_csv_data(modal_clicks, upload_clicks, 
                         project_name, site_name, study_year, num_blocks, treatments,
                         sampling_stage, label_style, biomass_data, uploaded_data,
                         upload_label_style, upload_biomass_output_type):
        
        ctx = callback_context
        if not ctx.triggered:
            return None, None, None, True
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            if button_id == "modal-generate-csv-btn":
                # Use label style to determine which form type to process
                if label_style in ["barcode", "line"]:  # This is the biomass or line style
                    if biomass_data:
                        # Generate CSV data from manual biomass input
                        df = pd.DataFrame(biomass_data)
                        if label_style == "line":
                            label_options = {"style": "line", "output_type": "qr"}
                        else:
                            label_options = {"style": "biomass", "output_type": "barcode"}
                    else:
                        # No biomass data added yet
                        return dbc.Alert([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Please add at least one row of data before generating CSV."
                        ], color="warning"), None, None, True
                else:  # QR style
                    # Generate CSV data from manual QR input
                    if not all([project_name, site_name, study_year, num_blocks, treatments, sampling_stage]):
                        return dbc.Alert([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Please fill in all required fields for QR labels."
                        ], color="warning"), None, None, True
                    
                    df = create_qr_dataframe(project_name, site_name, study_year, num_blocks, 
                                           treatments, sampling_stage)
                    label_options = {"style": "qr", "output_type": "qr"}
                
            elif button_id == "load-csv-btn" and uploaded_data:
                # Load uploaded CSV data
                df = pd.DataFrame(uploaded_data)
                if upload_label_style == "line":
                    label_options = {"style": "line", "output_type": "qr"}
                else:
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
            
    # Loading overlay control callback
    @app.callback(
        Output("loading-overlay", "style"),
        [Input("generate-pdf-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def show_loading(n_clicks):
        if n_clicks:
            return {"display": "block"}  # Show loading overlay
        return {"display": "none"}

    # PDF generation callback
    @app.callback(
        [Output("pdf-viewer-content", "children"),
         Output("results-area", "children"),
         Output("loading-overlay", "style", allow_duplicate=True)],
        [Input("generate-pdf-btn", "n_clicks")],
        [State("current-csv-data", "data"),
         State("current-label-options", "data")],
        prevent_initial_call=True
    )
    def generate_pdf_from_csv(n_clicks, csv_data, label_options):
        if not n_clicks or not csv_data or not label_options:
            return None, None, {"display": "none"}
        
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
            elif label_options["style"] == "line":
                pdf_filename = f"line_labels_{timestamp}.pdf"
                pdf_result = create_line_pdf(df, pdf_filename)
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
            
            # Hide loading overlay when done and return results
            return pdf_viewer, None, {"display": "none"}
            
        except Exception as e:
            error_alert = dbc.Alert([
                html.I(className="fas fa-times-circle me-2"),
                f"Error generating PDF: {str(e)}"
            ], color="danger")
            
            # Hide loading overlay on error too
            return None, error_alert, {"display": "none"}

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
            elif label_options["style"] == "line":
                pdf_filename = f"line_labels_{timestamp}.pdf"
                pdf_result = create_line_pdf(df, pdf_filename)
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