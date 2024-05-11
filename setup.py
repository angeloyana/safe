from setuptools import setup, find_packages

setup(
    name='safe',
    description='Command-line utility used to store and secure sensitive information.',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'click==8.1.7',
        'InquirerPy==0.3.4',
        'prompt_toolkit==3.0.43',
        'pycryptodome==3.20.0',
        'bcrypt==4.1.2',
        'SQLAlchemy==2.0.27'
    ],
    entry_points={
        'console_scripts': [
            'safe = safe.main:cli'
        ]
    }
)
