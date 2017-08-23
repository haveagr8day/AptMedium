from setuptools import setup

setup(name='aptmedium',
      version='1.0dev',
      description='Manages an APT installation medium for multiple, even disconnected or remote, machines.',
      long_description=open('README.txt').read(),
      url='http://github.com/haveagr8day/AptMedium',
      author='Riley Baxter',
      author_email='rbrileybaxter@gmail.com',
      license='GPLv2+',
      keywords='apt medium offline package manager',
      packages=['aptmedium'],
      scripts = ['apt-medium'],
      entry_points = {
          'console_scripts' : ['apt-medium=aptmedium.aptmedium:main'],
      },
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Topic :: System :: Installation/Setup',
          'Topic :: System :: Software Distribution',
          'Topic :: System :: Systems Administration',
          'Topic :: Utilities'])
