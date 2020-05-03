import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyDistrib",
    version="0.0.1",
    author="Rayan Hatout",
    author_email="rayan.hatout@gmail.com",
    description="A package to distribute Python computations across devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rayanht/pyDistrib",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
