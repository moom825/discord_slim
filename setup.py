from setuptools import setup, find_packages

setup(
    name="discord_slim",
    version="1.0.1",
    author="moom825",
    maintainer="moom825",
    url='https://github.com/moom825/discord_slim',
    description='',
    keywords=[],
    install_requires=['aiohttp==3.7.4.post0','httpx==0.22.0','websockets==10.1'],
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    packages=['discord_slim/classes'],
    package_dir={'': 'src'},
)