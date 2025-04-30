from setuptools import setup, find_packages

setup(
    name="honeypot-framework",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask>=2.0.0",
        "flask-cors>=3.0.0",
        "flask-session>=0.4.0",
        "redis>=4.0.0",
        "pymongo>=4.0.0",
        "geoip2>=4.0.0", 
        "python-dotenv>=0.19.0",
        "bcrypt>=3.2.0",
        "user-agents>=2.0.0",
        "python-socketio>=5.0.0",
        "gevent>=21.0.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "flake8>=4.0.0",
            "black>=22.0.0"
        ]
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive honeypot framework with admin dashboard",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/honeypot-framework",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Security",
    ],
)
