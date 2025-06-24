import os
import flask


def setup_download_route(app, pdf_storage):
    """Setup the download route for the Flask server"""
    
    @app.server.route('/download/<filename>')
    def download_file(filename):
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