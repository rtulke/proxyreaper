from cx_Freeze import setup, Executable

setup(
    name="proxyreaper",
    version="2.2.0",
    description="Proxy Reaper Tool",
    executables=[Executable("proxyreaper.py")]
)
