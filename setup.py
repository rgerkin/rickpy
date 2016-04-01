try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
	name='rickpy',
	version='0.1.2',
	author='Rick Gerkin',
	author_email='rgerkin@asu.edu',
	packages=['rickpy',],
	url='http://github.com/rgerkin/rickpy',
	license='MIT',
	description='Useful utilties for python',
	long_description="",
	install_requires=['ipython','nbformat']
)
