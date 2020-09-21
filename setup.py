from setuptools import setup

setup(
    name='acs_kmz_processor',
    version='0.1',
    py_modules=['kmz_processor'],
    install_requires=[
        'Arrow',
        'Click',
        'Fastkml',
        'Shapely',
    ],
    entry_points='''
        [console_scripts]
        kmz_processor=kmz_processor:generate_kmz
    ''',
)