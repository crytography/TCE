#coding:utf-8

from setuptools import setup, find_packages

setup(
        name = 'tmake',
        version = '1.0.5',
        packages = find_packages(),
        #package_dir = {'':'tmake'},
        author = 'scott',
        author_email = 'socketref@hotmail.com',
        url = 'http://github.com/adoggie/TCE',
        license = 'http://www.apache.org/licenses/LICENSE-2.0.html',
        description = 'TCE',
        package_data ={ '':[]},
        install_requires = ['ply'],
        scripts=[
                "tmake/lexparser.py",
                "tmake/mylex.py",
                "tmake/tce_util.py",
                "tmake/tce2as.py",
                "tmake/tce2cpp.py",
                "tmake/tce2csharp.py",
                "tmake/tce2java.py",
                "tmake/tce2js_requirejs.py",
                "tmake/tce2objc.py",
                "tmake/tce2py.py"
        ],
        long_description="",

        )