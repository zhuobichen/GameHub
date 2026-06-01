from setuptools import setup, find_packages

setup(
    name="gamehub-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["click>=8.1", "rich>=13.0", "httpx>=0.27", "anthropic>=0.39"],
    entry_points={
        "console_scripts": [
            "gamehub=main:cli",
        ],
    },
)
