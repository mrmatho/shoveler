from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("shoveler")
except PackageNotFoundError:
    # Running from source without being installed
    __version__ = "0.0.0.dev"
