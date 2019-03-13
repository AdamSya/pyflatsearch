from setuptools import setup,find_packages

setup(
    name='pyflatsearch',
    version='1.0.1a1',
    description='A data mining and visualisation tool for obtaining current \
                information on property prices in different wards of London.',
    url='https://github.com/AdamSya/pyflatsearch',
    author='adamsya',
    author_email='adam.syanda@gmail.com',
    license='MIT',
    python_requires='>=3',
    classifiers=["Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.7",
    "Topic :: Internet :: WWW/HTTP :: Indexing/Search' filters"],
    packages=find_packages(exclude=['tests','docs','tests.*']),
    install_requires=[
        'numpy>=1.15.2',
        'Shapely>=1.6.4.post2',
        'geopandas>=0.4.0',
        'pandas>=0.23.4',
        'rightmove-webscraper>=0.3',
        'seaborn>=0.9.0',
        'matplotlib>=3.0.0',
        'descartes>=1.1.0',
        'matplotlib>=3.0.0',
        'setuptools>=40.8.0'])

