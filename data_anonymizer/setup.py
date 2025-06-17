from setuptools import setup, find_packages

setup(
    name='data_anonymizer',
    version='0.1.0',
    description='A simple and customizable PII anonymization library using Presidio.',
    author='Khushi Kumari',
    author_email='your-email@example.com',
    url='https://github.com/khushi-workbox/data_anonymizer',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pandas',
        'presidio-analyzer',
        'presidio-anonymizer',
        'openpyxl',
        'pdfplumber'
    ],

    entry_points={
        'console_scripts': [
            'data-anonymizer = data_anonymizer.__main__:main'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
