# Hook to prevent importing SQLAlchemy with PyInstaller
# This is a workaround for Python 3.13 compatibility issues
excludedimports = ['sqlalchemy', 'sqlalchemy.sql', 'sqlalchemy.engine']
