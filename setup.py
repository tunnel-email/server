from setuptools import setup, find_packages

setup(
    name="mailtunnel",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "asyncio",
        "python-dotenv",
        "pydantic",
        "requests",
        "redis",
        "mysql",
        "uvicorn",
        "fastapi-sso",
        "mysql-connector-python",
        "mysql-connector-python-rf",
        "portpicker"
    ],
    entry_points={
        'console_scripts': [
            'mailtunnel-forwarder=mailtunnel.sni_forwarder:main',
            'mailtunnel-api=mailtunnel.http_api:main',
            'mailtunnel-confdumper=mailtunnel.config_dumper:main',
        ],
    },
    author="not-lum",
    description="mailtunnel (tunnel.email)",
    python_requires='>=3.8',
)
