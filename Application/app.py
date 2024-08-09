from __init__ import create_app
import base64
app = create_app()

#custom function for uploaded images

@app.template_filter('b64encode')
def b64encode_filter(data):
    if isinstance(data, bytes):
        return base64.b64encode(data).decode('utf-8')
    return None


if __name__ == "__main__":
    app.run(debug=True)