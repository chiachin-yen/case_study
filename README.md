# Tools for case studying by web

A tool to collect cases from architectural websites for educational usage.

## Getting Started

Currently supporting website: ArchDaily.com

To start with instruction:
```bash
$python CaseStudy.py
```
To download with an ArchDaily Page ID(a 5 or 6 digit number in the URL from ArchDaily.com)
```bash
$python CaseStudy.py -AD_ID 000000
```
To download with an ArchDaily URL
```bash
$python CaseStudy.py -url https:/www.archdaily.com/000000
```

### Dependencies

Python
bs4
Pillow

### Installing

1. Clone the project to your local disc with Python 3.6 environment.
2. Install dependencies.
3. Double click 'run.bat' if you're running a Windows system.
4. Follow the instruction on your terminal.


## Versioning

I use [SemVer](http://semver.org/) for versioning.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* The copyright of downloaded images and text belongs to their respective owners.
