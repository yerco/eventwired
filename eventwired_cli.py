import typer
import os

app = typer.Typer()

TEMPLATE_DIR = "cli_files"

common_files = {
    "app.py": "common/app_template.py",
    "routes.py": {
        "website": "common/routes_website_template.py",
        "api": "common/routes_api_template.py",
    },
    "di_setup.py": {
        "website": "common/di_setup_website_template.py",
        "api": "common/di_setup_api_template.py",
    },
    "config.py": {
        "website": "common/config_website_template.py",
        "api": "common/config_api_template.py",
    },
    "subscriber_setup.py": {
        "website": "common/subscriber_setup_website_template.py",
        "api": "common/subscriber_setup_api_template.py",
    },
}

# Define app structure templates
website_structure = {
    "controllers": [
        ("home_controller.py", "controllers/home_controller_template.py"),
    ],
    "templates": [
        ("home.html", "templates/home_template.html"),
    ],
    "static/css": [
        ("style.css", "static/css/style_template.css"),
    ],
    "static/images": [],
    "static/js": [],
}

api_structure = {
    "controllers": [
        ("api_login_controller.py", "controllers/api_login_controller_template.py"),
    ],
    "models": [
        ("user.py", "models/user_template.py"),
    ],
    "subscribers": [
        ("api_subscribers.py", "subscribers/api_subscribers_template.py"),
    ],
}


def load_template(template_path: str, replacements: dict = None) -> str:
    full_path = os.path.join(TEMPLATE_DIR, template_path)
    with open(full_path, "r") as f:
        content = f.read()

    if replacements:
        for placeholder, value in replacements.items():
            content = content.replace(f"{{{placeholder}}}", value)

    return content


def create_folder_structure(base_path: str, structure: dict, replacements: dict = None):
    for folder, files in structure.items():
        folder_path = os.path.join(base_path, folder)
        os.makedirs(folder_path, exist_ok=True)
        for file_info in files:
            if isinstance(file_info, tuple):  # File with a template
                file_name, template_path = file_info
                content = load_template(template_path, replacements)
            else:  # Empty file
                file_name = file_info
                content = ""
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, "w") as f:
                f.write(content)


def create_common_files(base_path: str, app_name: str, app_type: str):
    for file_name, template_info in common_files.items():
        if isinstance(template_info, dict):  # Handle dynamic template selection
            template_path = template_info.get(app_type)
        else:
            template_path = template_info

        if template_path:
            file_path = os.path.join(base_path, file_name)
            content = load_template(template_path, {"app_name": app_name})
            with open(file_path, "w") as f:
                f.write(content)


def print_run_instructions(app_type, app_name: str):
    typer.echo(typer.style("Next Steps:", fg=typer.colors.BRIGHT_BLUE, bold=True))
    typer.echo(typer.style(f"  To run your application, use:", fg=typer.colors.BRIGHT_GREEN, bold=True))
    typer.echo(typer.style(f"    python run_server.py --app {app_name}.app:app", fg=typer.colors.BRIGHT_YELLOW))
    typer.echo(typer.style("  Add '--reload' for debugging during development:", fg=typer.colors.BRIGHT_GREEN, bold=True))
    typer.echo(typer.style(f"    python run_server.py --app {app_name}.app:app --reload", fg=typer.colors.BRIGHT_YELLOW))
    if app_type == "api":
        typer.echo(typer.style("\nAPI Endpoints Testing Instructions:", fg=typer.colors.BRIGHT_BLUE, bold=True))
        typer.echo(typer.style(f"  1. Create a user:", fg=typer.colors.BRIGHT_GREEN, bold=True))
        typer.echo(typer.style(
            f"     curl -v -X POST -H \"Content-Type: application/json\" "
            f"-d '{{\"username\": \"cobreloa\", \"password\": \"campeon\"}}' http://localhost:8000/api/create",
            fg=typer.colors.BRIGHT_YELLOW,
        ))
        typer.echo(typer.style(f"  2. Log in to get a token:", fg=typer.colors.BRIGHT_GREEN, bold=True))
        typer.echo(typer.style(
            f"     curl -v -X POST -H \"Content-Type: application/json\" "
            f"-d '{{\"username\": \"cobreloa\", \"password\": \"campeon\"}}' http://localhost:8000/api/login",
            fg=typer.colors.BRIGHT_YELLOW,
        ))
        typer.echo(typer.style(f"  3. Access a protected endpoint:", fg=typer.colors.BRIGHT_GREEN, bold=True))
        typer.echo(typer.style(
            f"     curl -v -X GET -H \"Content-Type: application/json\" "
            f"-H 'Authorization: Bearer <TOKEN>' http://localhost:8000/api/protected",
            fg=typer.colors.BRIGHT_YELLOW,
        ))

# Initialize a new EventWired application
@app.command()
def init():
    typer.echo("Welcome to EventWired CLI!")
    app_type = typer.prompt("Do you want to create a [website] or an [api]?", default="website").lower()

    app_name = typer.prompt("Enter the directory name for your app", default="myapp")
    base_path = os.path.join(os.getcwd(), app_name)
    os.makedirs(base_path, exist_ok=True)

    if app_type == "website":
        typer.echo("Creating a website application...")
        create_folder_structure(base_path, website_structure, {"app_name": app_name})
    else:
        typer.echo("Creating a api application...")
        create_folder_structure(base_path, api_structure, {"app_name": app_name})

    # Create common files with dynamic replacements
    create_common_files(base_path, app_name, app_type)

    typer.echo(f"EventWired application '{app_name}' has been successfully created!")
    typer.echo(f"You can delete the 'demo_app' folder/app or keep it as reference for your implementation.")

    print_run_instructions(app_type, app_name)


if __name__ == "__main__":
    app()
