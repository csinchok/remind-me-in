#!/usr/bin/env python

from distutils.core import setup

setup(
    name='remind-me-in',
    version='0.0.1',
    description='A Twitter bot to remind people of their promises',
    author='Chris Sinchok',
    author_email='chris@sinchok.com',
    url='https://twitter.com/HereToRemindU',
    packages=['remindmein',],
    install_requires=[
        'pytz==2015.4',
        'aiohttp==0.17.2'
    ],
    entry_points={
        'console_scripts': [
            'remindmein = remindmein.app:main',
        ],
    }
)
