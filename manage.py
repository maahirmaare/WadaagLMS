from app import create_app, db
from flask_migrate import Migrate
from flask.cli import with_appcontext
import click

app = create_app()
migrate = Migrate(app, db)

# ✅ Custom CLI command group
@app.cli.command("create-db")
@with_appcontext
def create_db():
    """Create the database tables."""
    db.create_all()
    click.echo("Database tables created.")

# Entry point
if __name__ == "__main__":
    app.run()