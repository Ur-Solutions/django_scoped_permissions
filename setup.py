import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-scoped-permissions",
    version="0.1.3",
    author="Tormod Haugland, Magnus Buvarp",
    author_email="tormod.haugland@gmail.com, magnus.buvarp@gmail.com",
    description="Scoped permission system for Django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ur-Solutions/django_scoped_permissions",
    packages=setuptools.find_packages(),
    install_requires=[
        "django>=2.0.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ]
)
