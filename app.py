import os
import dash
import dash_bootstrap_components as dbc

from layout import create_layout
from callbacks import register_callbacks
from server import setup_download_route


# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "🌱 CiampittiLab Labels Generator"
app.config.suppress_callback_exceptions = True

# Create necessary directories (only for local development)
if not os.environ.get('RENDER'):  # Only create dirs locally, not on Render
    os.makedirs("labels_pdf", exist_ok=True)

# Global storage for in-memory PDFs (for deployment)
pdf_storage = {}

# Set up the layout
app.layout = create_layout()

# Register all callbacks
register_callbacks(app, pdf_storage)

# Setup download route
setup_download_route(app, pdf_storage)

# Expose the server for gunicorn
server = app.server

if __name__ == '__main__':
    # Only enable debug mode if not running on deployment
    debug_mode = not bool(os.environ.get('RENDER'))
    app.run_server(debug=debug_mode) 