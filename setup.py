import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='OBM',
    version='0.0.0',
    author='Kunind Sharma',
    author_email='Kunind@hotmail.com',
    description='Testing installation of Package',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/NEU-ABLE-LAB/Build_OBM',
    project_urls = {
        "Bug Tracker": "https://github.com/NEU-ABLE-LAB/Build_OBM/issues"
    },
    license='MIT',
    packages=['src'],
    install_requires=['requests'],
)