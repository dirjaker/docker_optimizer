"""
py2app setup script for Docker Optimizer macOS application.
Build with: python packaging/py2app_setup.py py2app
"""
from setuptools import setup

APP = ['src/macos/app.py']
DATA_FILES = [
    ('src/web/static', ['src/web/static/index.html']),
]
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'Docker Optimizer',
        'CFBundleDisplayName': 'Docker Optimizer',
        'CFBundleIdentifier': 'com.dockeroptimizer.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'MIT License',
    },
    'packages': [
        'fastapi', 'uvicorn', 'pydantic', 'starlette',
        'yaml', 'rich',
    ],
    'includes': [
        'tkinter', 'json', 'threading', 'webbrowser',
        'src.web.app', 'image_analyzer', 'optimizer', 'reporter', 'models',
    ],
    'excludes': ['numpy', 'torch'],
}

setup(
    name='Docker Optimizer',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
