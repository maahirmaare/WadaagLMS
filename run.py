import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask.cli import with_appcontext
import click
from flask_migrate import Migrate

from app import create_app, db

# Create Flask app
app = create_app()

# Set up database migration
migrate = Migrate(app, db)

# Custom CLI command to create database
@app.cli.command("create-db")
@with_appcontext
def create_db():
    """Create all database tables."""
    db.create_all()
    click.echo("✅ Database created successfully.")

# Run app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)