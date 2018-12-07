from editorapp import app, db
from editorapp.models import Users

# app = create_app()
# cli.register(app)

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': Users }