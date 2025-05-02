import click
import os
import shutil
from importlib import resources
import stat 

_TEMPLATE_PACKAGE = 'honeypot.deploy_templates'


def _copy_resource(resource_path, target_path):
    """
    Copies a resource (file or directory) from the package to the target path.
    Uses importlib.resources for robust path finding within the installed package.
    Renames files by removing .template suffix from the source name when creating the target.
    """
    try:
        target_parent_dir = os.path.dirname(target_path)
        if target_parent_dir:
            os.makedirs(target_parent_dir, exist_ok=True)

        pkg_files = resources.files(_TEMPLATE_PACKAGE)
        source_resource = pkg_files.joinpath(resource_path)

        if not source_resource.is_file() and not source_resource.is_dir():
            raise FileNotFoundError(f"Resource '{resource_path}' not found in package.")

        if source_resource.is_dir():

            if os.path.exists(target_path) and not os.path.isdir(target_path):
                raise FileExistsError(f"Target path '{target_path}' exists but is not a directory.")
            os.makedirs(target_path, exist_ok=True)


            is_top_level_dir_copy = target_path.endswith(os.path.sep + os.path.basename(resource_path)) \
                                  or target_path == os.path.basename(resource_path)
            if is_top_level_dir_copy:
                click.echo(f"  Created Directory {target_path}/")

            for item in source_resource.iterdir():
                recursive_source_path = os.path.join(resource_path, item.name)
                recursive_target_path = os.path.join(target_path, item.name)
                _copy_resource(recursive_source_path, recursive_target_path)

        else: 
            final_target_filename = os.path.basename(target_path) 
            source_basename = os.path.basename(resource_path)
            if source_basename.endswith('.template'):
                final_target_filename = source_basename[:-len('.template')]


            final_target_path = os.path.join(target_parent_dir, final_target_filename)


            with source_resource.open('rb') as src_fp:
                with open(final_target_path, 'wb') as dest_fp:
                    shutil.copyfileobj(src_fp, dest_fp)


            click.echo(f"  Created {final_target_path}")


    except FileNotFoundError:
        click.secho(f"Error: Template resource '{resource_path}' not found in package.", fg='red')
        return False
    except Exception as e:
        click.secho(f"Error creating target '{target_path}': {e}", fg='red')
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
    # ... (rest of docstring) ...
    """
    click.echo("Initializing Flask-Honeypot deployment files...")

    files_to_create = {
        "docker-compose.yml.template": "docker-compose.yml",
        "Dockerfile.nginx.template": "Dockerfile.nginx",
        "Dockerfile.backend.template": "Dockerfile.backend",
        "docker-compose.dev.yml.template": "docker-compose.dev.yml",
        "dev-nginx.conf.template": "dev-nginx.conf",
        "dot_env.example": ".env.example",
        "nginx": "nginx",
        "setup_honeypot.sh.template": "setup_honeypot.sh" ,
        "mongo-init.js.template": "mongo-init.js",
    }

    all_successful = True
    cwd = os.getcwd()

    for template_resource, target_name in files_to_create.items():
        target_path = os.path.join(cwd, target_name)

        if not force and os.path.exists(target_path):
            click.secho(f"Skipping: '{target_name}' already exists. Use --force to overwrite.", fg='yellow')
            continue


        if not _copy_resource(template_resource, target_path):
            all_successful = False

    if all_successful:
        try:
            setup_script_path = os.path.join(cwd, "setup_honeypot.sh")
            if os.path.exists(setup_script_path):
                os.chmod(setup_script_path, os.stat(setup_script_path).st_mode | stat.S_IEXEC)
        except Exception as e:
            click.secho(f"Warning: Could not set executable permissions on setup script: {e}", fg='yellow')
        
        click.secho("\nDeployment files created successfully!", fg='green')
        click.echo("----------------------------------------")
        click.secho("NEXT STEPS:", bold=True)
        click.echo("1. Run the setup script: ./setup_honeypot.sh")
        click.echo("   This will set up your environment and generate secure configurations")
        click.echo("2. Start the honeypot: docker-compose up --build -d")
        
        click.secho("\nOPTIONAL: For production HTTPS setup:", fg='yellow')
        click.echo("- Edit nginx/sites-enabled/proxy.conf and enable the HTTPS section")
        click.echo("- Configure your SSL certificates")
        click.echo("- See full instructions in the documentation")
        
        click.secho("\nFor development:", fg='cyan')
        click.echo("- Use docker-compose-dev.yml: docker-compose -f docker-compose-dev.yml up")
    else:
        click.secho("\nSome deployment files could not be created. Please check errors above.", fg='red')



if __name__ == '__main__':
    main()
