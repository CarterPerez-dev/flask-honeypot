#!/bin/bash
# setup_honeypot.sh

set -e  # Exit on error

echo "###########################################################"
echo "# ███████╗██╗      █████╗ ███████╗██╗  ██╗                #"
echo "# ██╔════╝██║     ██╔══██╗██╔════╝██║ ██╔╝                #"
echo "# █████╗  ██║     ███████║███████╗█████╔╝                 #"
echo "# ██╔══╝  ██║     ██╔══██║╚════██║██╔═██╗                 #"
echo "# ██║     ███████╗██║  ██║███████║██║  ██╗                #"
echo "# ╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                #"
echo "#                                                         #"
echo "# ██╗  ██╗ ██████╗ ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ████████╗ #"
echo "# ██║  ██║██╔═══██╗████╗  ██║██╔════╝╚██╗ ██╔╝██╔══██╗██╔═══██╗╚══██╔══╝ #"
echo "# ███████║██║   ██║██╔██╗ ██║█████╗   ╚████╔╝ ██████╔╝██║   ██║   ██║    #"
echo "# ██╔══██║██║   ██║██║╚██╗██║██╔══╝    ╚██╔╝  ██╔═══╝ ██║   ██║   ██║    #"
echo "# ██║  ██║╚██████╔╝██║ ╚████║███████╗   ██║   ██║     ╚██████╔╝   ██║    #"
echo "# ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝      ╚═════╝    ╚═╝    #"
echo "###########################################################"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Would you like to install Docker? (y/n)"
    read -p "> " install_docker
    if [[ $install_docker == "y" || $install_docker == "Y" ]]; then
        echo "Installing Docker..."
        # Check OS and install appropriately
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux installation
            if command -v apt-get &> /dev/null; then
                # Debian/Ubuntu
                sudo apt-get update
                sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
                sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
                sudo apt-get update
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io
            elif command -v dnf &> /dev/null; then
                # Fedora/RHEL/CentOS
                sudo dnf -y install dnf-plugins-core
                sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
                sudo dnf install -y docker-ce docker-ce-cli containerd.io
            else
                echo "Unsupported Linux distribution. Please install Docker manually: https://docs.docker.com/engine/install/"
                exit 1
            fi
            # Start and enable Docker
            sudo systemctl start docker
            sudo systemctl enable docker
            # Add current user to docker group
            sudo usermod -aG docker $USER
            echo "Docker installed. You may need to log out and back in for group changes to take effect."
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS installation
            echo "Please download and install Docker Desktop for Mac from: https://www.docker.com/products/docker-desktop"
            echo "After installation, press Enter to continue or Ctrl+C to cancel."
            read
        else
            echo "Unsupported operating system. Please install Docker manually: https://docs.docker.com/engine/install/"
            exit 1
        fi
    else
        echo "Docker is required. Please install Docker and try again."
        exit 1
    fi
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    # Docker Compose V2 could be installed as a docker plugin
    if ! docker compose version &> /dev/null; then
        echo "Docker Compose not found. Would you like to install Docker Compose? (y/n)"
        read -p "> " install_compose
        if [[ $install_compose == "y" || $install_compose == "Y" ]]; then
            echo "Installing Docker Compose..."
            if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                # Linux installation
                COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
                sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                sudo chmod +x /usr/local/bin/docker-compose
            else
                echo "Docker Compose should be included with Docker Desktop for Mac or Windows."
                echo "If it's not, please install Docker Compose manually: https://docs.docker.com/compose/install/"
            fi
        else
            echo "Docker Compose is required. Please install Docker Compose and try again."
            exit 1
        fi
    else
        echo "Docker Compose V2 detected as Docker plugin."
    fi
fi

# Create and activate virtual environment
echo "Creating Python virtual environment..."
python -m venv honeypot_venv
source honeypot_venv/bin/activate

# Install the package
echo "Installing Honeypot Framework..."
pip install flask-honeypot

echo "Creating deployment files from templates..."
honeypot-deploy init

# Copy .env.example to .env if not already done
if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "Created .env file from template"
fi

# Generate secure configuration
echo "Generating secure configuration..."
python -m honeypot.utils.generate_config

# Prompt for MaxMind key
read -p "Enter your MaxMind license key (optional, press Enter to skip): " maxmind_key
if [ ! -z "$maxmind_key" ]; then
    # Add key to .env file
    if grep -q "MAXMIND_LICENSE_KEY=" .env; then
        sed -i "s/MAXMIND_LICENSE_KEY=.*/MAXMIND_LICENSE_KEY=\"$maxmind_key\"/g" .env
    else
        echo "MAXMIND_LICENSE_KEY=\"$maxmind_key\"" >> .env
    fi
    echo "MaxMind license key configured successfully!"
fi

echo ""
echo "+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+"
echo "|                      .-----.                              |"
echo "|       🐝            /       \\            🐝                |"
echo "|                    |         |                           |"
echo "|                     \\       /                            |"
echo "|  🍯                   '-----'                      🍯    |"
echo "|                                                          |"
echo "|  ██╗  ██╗ ██████╗ ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ████████╗  |"
echo "|  ██║  ██║██╔═══██╗████╗  ██║██╔════╝╚██╗ ██╔╝██╔══██╗██╔═══██╗╚══██╔══╝  |"
echo "|  ███████║██║   ██║██╔██╗ ██║█████╗   ╚████╔╝ ██████╔╝██║   ██║   ██║     |"
echo "|  ██╔══██║██║   ██║██║╚██╗██║██╔══╝    ╚██╔╝  ██╔═══╝ ██║   ██║   ██║     |"
echo "|  ██║  ██║╚██████╔╝██║ ╚████║███████╗   ██║   ██║     ╚██████╔╝   ██║     |"
echo "|  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝      ╚═════╝    ╚═╝     |"
echo "|                                                          |"
echo "|           🎉        SETUP COMPLETE        🎉            |"
echo "+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+~+"
echo ""
echo "To start the honeypot, run:"
echo "    docker-compose up --build -d"
echo ""
echo "To start in development mode, run:"
echo "    docker-compose -f docker-compose-dev.yml --build -d"
echo ""
echo "To access the admin dashboard, navigate to:"
echo "    http://localhost/honey/login"
echo ""
echo "Default admin password is in your .env file"
echo "======================================"
