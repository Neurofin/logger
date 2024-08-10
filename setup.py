from setuptools import setup, find_packages

VERSION = '0.1.0'
DESCRIPTION = 'Logging middleware for Python applications'

# Setting up
setup(
    name="logger",
    version=VERSION,
    author="Neeraj Varma",
    author_email="neeraj@neurofin.com",
    description=DESCRIPTION,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/username/repository',  # Replace with your repo URL
    packages=find_packages(),
    install_requires=[
        'fastapi',      # FastAPI framework
        'starlette',    # ASGI toolkit that FastAPI is built on
        'httpx',        # For making asynchronous HTTP requests
    ],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    license='MIT',
)
