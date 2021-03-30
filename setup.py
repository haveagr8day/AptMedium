from setuptools import setup

setup(name='apt-medium',
      version='0.4',
      description='Manages an installation medium for installing/updating packages on multiple (possibly disconnected and/or remote) systems.',
      long_description=open('README.md').read(),
      url='http://github.com/haveagr8day/AptMedium',
      author='Riley Baxter',
      author_email='rbrileybaxter@gmail.com',
      license='GPLv2+',
      keywords='apt medium offline package manager',
      packages=['apt_medium'],
      scripts = ['apt-medium'],
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
          'Topic :: Utilities'],
      zip_safe = True)
