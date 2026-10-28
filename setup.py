import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="django-scoped-permissions",
    version="0.1.8",
    author="Tormod Haugland, Magnus Buvarp",
    author_email="tormod.haugland@gmail.com, magnus.buvarp@gmail.com",
    description="Scoped permission system for Django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Ur-Solutions/django_scoped_permissions",
    packages=setuptools.find_packages(),
    python_requires=">=3.12,<4",
    install_requires=[
        "django>=5.2,<7",
        "graphene-django>=3.2.3,<4",
        "graphene-django-cud>=0.13,<0.14",
        "pyjwt>=1.7.1,<2",
        "pydash>=4.7.6,<9",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ]
)
