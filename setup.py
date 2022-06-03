from setuptools import setup

setup(
    name='moexapi',
    version='0.1.0',
    description='Moscow Exchange API',
    url='https://github.com/DmitryYenkov/moexapi',
    author='Dmitry Yenkov',
    author_email='',
    license='GPL',
    packages=['moexapi'],
    install_requires=['pandas',
                      'tabulate'],
)
