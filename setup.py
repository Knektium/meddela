import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="meddela",
    version="0.0.1",
    author="Jack Engqvist Johansson",
    author_email="jack@codile.se",
    description="Handle CAN message configuration in JSON",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CodileAB/meddela",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
