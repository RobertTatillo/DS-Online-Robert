from setuptools import setup, find_packages

setup(
    name='toolbox_ml',
    version='1.0.0',
    description='Paquete de utilidades para EDA y Machine Learning',
    packages=find_packages(),
    python_requires='>=3.10',
    install_requires=open('requirements.txt').read().splitlines()
)
