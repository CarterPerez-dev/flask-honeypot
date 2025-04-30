# honeypot/cli.py
import click
import os
import shutil
from importlib import resources
import stat


_TEMPLATE_PACKAGE = 'honeypot.deploy_templates'

def _copy_resource(resource_path, target_path, is_dir=False):
    """
    Copies a resource (file or directory) from the package to the target path.
    Uses importlib.resources for robust path finding within the installed package.
    """
    try:
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)


        pkg_files = resources.files(_TEMPLATE_PACKAGE)
        source_resource = pkg_files.joinpath(resource_path)

        if not source_resource.is_file() and not source_resource.is_dir():
             raise FileNotFoundError(f"Resource '{resource_path}' not found.")

        if source_resource.is_dir():
            if os.path.exists(target_path) and not os.path.isdir(target_path):
                 raise FileExistsError(f"Target path '{target_path}' exists but is not a directory.")
            os.makedirs(target_path, exist_ok=True) 
            for item in source_resource.iterdir():
                _copy_resource(os.path.join(resource_path, item.name),
                               os.path.join(target_path, item.name))
        else: 
            with source_resource.open('rb') as src_fp: 
                with open(target_path, 'wb') as dest_fp:
                    shutil.copyfileobj(src_fp, dest_fp)


        if not is_dir or not resource_path.startswith(os.path.dirname(target_path)):
             click.echo(f"  Created {target_path}")


    except FileNotFoundError:
        click.secho(f"Error: Template resource '{resource_path}' not found in package.", fg='red')
        return False
    except Exception as e:
        click.secho(f"Error creating '{target_path}': {e}", fg='red')
        return False
    return True


@click.group()
def main():
    """Flask-Honeypot deployment and utility tools."""
    pass

@main.command()
@click.option('--force', is_flag=True, default=False, help="Overwrite existing files.")
def init(force):
    """
    Creates deployment files (docker-compose.yml, Dockerfiles, nginx config, etc.)
    in the current directory based on templates included with the package.

    IMPORTANT: Run this command from the root of your cloned source repository
    if you intend to use the included Dockerfile.nginx, as it needs access
    to the frontend source code during the Docker build process.
    """
    click.echo("Initializing Flask-Honeypot deployment files...")


    files_to_create = {
        "docker-compose.yml.template": "docker-compose.yml",
        "Dockerfile.nginx.template": "Dockerfile.nginx",
        "Dockerfile.backend.template": "Dockerfile.backend",
        "dot_env.example": ".env.example",
        "nginx": "nginx", 
    }

    all_successful = True
    cwd = os.getcwd()

    for template_resource, target_name in files_to_create.items():
        target_path = os.path.join(cwd, target_name)

        if not force and os.path.exists(target_path):
            click.secho(f"Skipping: '{target_name}' already exists. Use --force to overwrite.", fg='yellow')
            continue


        is_dir = template_resource == "nginx"

        if not _copy_resource(template_resource, target_path, is_dir=is_dir):
            all_successful = False

    if all_successful:
        click.secho("\nDeployment files created successfully!", fg='green')
        click.echo("----------------------------------------")
        click.secho("IMPORTANT NEXT STEPS:", bold=True)
        click.echo("1. Review the generated files (docker-compose.yml, Dockerfile.*, nginx/*).")
        click.echo("2. Copy '.env.example' to '.env'.")
        click.echo("3. Generate SECURE, RANDOM secrets and fill in the '.env' file.")
        click.echo("   (Do NOT use default or easily guessable passwords!)")
        click.echo("4. Ensure Docker and Docker Compose are installed.")

        click.secho("\n--- Setting up HTTPS (Recommended for Production) ---", bold=True, fg='yellow')
        click.echo("5. Obtain an SSL certificate for your domain (e.g., using Certbot).")
        click.echo("   - A common method involves running Certbot on your host machine or using a Certbot Docker container.")
        click.echo("   - See Certbot documentation: https://certbot.eff.org/")
        click.echo("6. Edit the generated 'nginx/sites-enabled/proxy.conf':")
        click.echo("   - Uncomment the 'server {...}' block listening on port 443.")
        click.echo("   - Update 'server_name' with your actual domain(s).")
        click.echo("   - Update 'ssl_certificate' and 'ssl_certificate_key' paths to point to your generated certificate files.")
        click.echo("   - Review and uncomment desired SSL settings (protocols, ciphers).")
        click.echo("   - Optionally, uncomment the HTTP-to-HTTPS redirect in the port 80 server block.")
        click.echo("7. Edit the generated 'docker-compose.yml':")
        click.echo("   - Uncomment the '443:443' port mapping for the 'nginx' service.")
        click.echo("   - Uncomment and adjust the 'volumes:' section for the 'nginx' service to mount your certificate directory (e.g., Let's Encrypt's '/etc/letsencrypt') into '/etc/nginx/certs' (read-only).")
        click.secho("8. Configure your firewall to allow traffic on port 443.", fg='yellow')

        click.secho("\n--- Running the Application ---", bold=True)
        click.echo("9. Run 'docker-compose up --build' to build images and start services.")
        click.secho("\nNOTE: The generated Dockerfiles expect to be run from the root of the source code repository containing the 'honeypot/frontend' directory.", fg='cyan')

    else:
        click.secho("\nSome deployment files could not be created. Please check errors above.", fg='red')



if __name__ == '__main__':
    main()
