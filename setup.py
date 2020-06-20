from setuptools import setup

setup(
    name='crowpy',
    version='0.1.3',
    author='Jason Capili',
    author_email='jcapili@alumni.scu.edu',
    packages=['crowpy'],
    include_package_data=True,
    install_requires=[
        'geopy'
        'lxml'
        'pandas'
        'requests'
        'tqdm'
        'xmltodict'
    ],
    url='https://github.com/jcapili/crowpy',
    license='MIT',
    description='Python code for calculating travel distance of USPS shipments',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: MacOS :: MacOS X',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        # 'Programming Language :: Python :: 3',
        # 'Programming Language :: Python :: 3.5',
        # 'Programming Language :: Python :: 3.6',
        # 'Programming Language :: Python :: 3.7',
        # 'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing',
    ],
    keywords='usps shipping carbon offsets miles',
    long_description=open('README.md', 'r').read(),
    long_description_content_type="text/markdown",
    zip_safe=False,
)