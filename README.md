[![Build Status](https://travis-ci.org/laurensdv/pygeometa.png)](https://travis-ci.org/geopython/pygeometa)

# pygeometa [geodcat-ap mod]

pygeometa is a Python package to generate metadata for geospatial datasets.

## Table of Contents
* [Overview](#overview)
* [Features](#features)
* [Quickstart](#quickstart)
* [Installation](#installation)
  * [Requirements](#requirements)
  * [Dependencies](#dependencies)
  * [Installing the Package](#installing-the-package)
* [Running](#running)
  * [From the command line](#from-the-command-line)
  * [Using the API from Python](#using-the-api-from-python)
* [Development](#development)
  * [Setting up a Development Environment](#setting-up-a-development-environment)
  * [Adding Another Metadata Schema to the Core](#adding-another-metadata-schema-to-the-core)
  * [Running Tests](#running-tests)
  * [Code Conventions](#code-conventions)
  * [Bugs and Issues](#bugs-and-issues)
* [History](#history)
* [Contact](#contact)


## Overview

pygeometa is a Python package to generate metadata for geospatial datasets. Metadata content is managed by pygeometa in simple Metadata Control Files (MCF) which consist of 'parameter = value' pairs. pygeometa generates metadata records from MCF files based on the schema specified by the user, such as ISO-19139. pygeometa supports nesting MCF files, which reduces duplication of metadata content common to multiple records and ease maintenance.

## Features

* simple configuration: inspired by Python's ConfigParser
* extensible: template architecture allows for easy addition of new metadata formats
* flexible: use as a command-line tool or integrate as a library

## Installation

pygeometa is best installed and used within a Python virtualenv.

### Requirements

* Python 2.7 and above.  Works with Python 3 (but not tested)
* Python [virtualenv](https://virtualenv.pypa.io/) package

### Dependencies

Dependencies are listed in [requirements.txt](requirements.txt). Dependencies are automatically installed during pygeometa's installation.

### Installing the Package

```bash
virtualenv my-env
cd my-env
. bin/activate
git clone https://github.com/laurensdv/pygeometa.git
cd pygeometa
pip install -r requirements.txt
python setup.py build
python setup.py install
```

## Running GeoDCAT-AP/ISO19139

### From the command line

```bash
# iso19139 (XML) -> geodcat-ap (RDF)
generate_metadata.py --xml=path/to/file.xml # to stdout
generate_metadata.py --xml=path/to/file.xml --output=some_file.rdf # to file

# geodcat-ap (RDF) -> iso19139 (XML)
generate_metadata.py --rdf=path/to/file.xml # to stdout
generate_metadata.py --rdf=path/to/file.rdf --output=some_file.xml # to file
```

With xml source files you can choose to include a:

* `--html` flag, you can choose to convert the xml to HTML
instead of GeoDCAT-AP RDF.
```bash
generate_metadata.py --xml=path/to/file.xml --html # to stdout
generate_metadata.py --xml=path/to/file.xml --html --output=some_file.html # to file
```
* `--validate` flag to
check if the xml is valid against the latest iso19139. If you include a
schema parameter you can define another supported schema against which the
xml should be validated. The file will not be converted to GeoDCAT-AP RDF.
```bash
generate_metadata.py --xml=path/to/file.xml --validate # to stdout
generate_metadata.py --xml=path/to/file.xml --validate --output=some_file # to file
```

### Supported schemas
Schemas supported by this pygeometa branch:
* iso-19139-to-dcat-ap, tweaked version of the EU ISO19139->GeoDCAT-AP conversion
* iso191139-flanders, updated iso19139 to be compatible with open data in the Belgian/EU region Flanders.
* Local schema, specified with ```--schema_local=/path/to/my-schema```

### Use of local schemas

| Action                             | Schema Type   |
|------------------------------------|---------------|
| iso19139 (XML) -> geodcat-ap (RDF) | xslt          |
| geodcat-ap (RDF) -> iso19139 (XML) | pygeometadata |

### Using the API from Python

```python
from pygeometa import iso_to_dcat, dcat_to_iso

# default schemas
rdf_output = iso_to_dcat('/path/to/file.xml')
xml_output = dcat_to_iso('/path/to/file.rdf')

# user-defined schemas
rdf_output = iso_to_dcat('/path/to/file.xml', schema_local='/path/to/new-schema.xsl')
xml_output = dcat_to_iso('/path/to/file.rdf', schema_local='/path/to/new-schema')

# validation
from pygeometa.validation.validation import Validators
from lxml import etree

profiles = ["iso19139latest"] # or another profile
xml = '/path/to/file.xml'
v = Validators(profiles)
v_results = v.is_valid(etree.parse(open(xml)))
```

## Running MCF/ISO19139 transformations

## Quickstart

Workflow to generate metadata XML:

1. Install pygeometa
2. Create a 'metadata control file' .mcf file that contains metadata information
  1. Modify the [sample.mcf](https://github.com/geopython/pygeometa/blob/master/sample.mcf) example
  2. pygeometa supports nesting MCF files together, allowing providing a single MCF file for common metadata parameters (e.g. common contact information)
  3. Refer to the [Metadata Control File Reference documentation](https://github.com/geopython/pygeometa/blob/master/doc/MCF_Reference.md)
3. Run pygeometa for the .mcf file with a specified target metadata schema

### From the command line

```bash
generate_metadata.py --mcf=path/to/file.mcf --schema=iso19139  # to stdout
generate_metadata.py --mcf=path/to/file.mcf --schema=iso19139 --output some_file.xml  # to file
# to use your own defined schema:
generate_metadata.py --mcf=path/to/file.mcf --schema_local=/path/to/my-schema --output some_file.xml  # to file
```

### Supported schemas
Schemas supported by pygeometa:
* iso19139, [reference](http://www.iso.org/iso/catalogue_detail.htm?csnumber=32557)
* iso19139-hnap, [reference](http://www.gcpedia.gc.ca/wiki/Federal_Geospatial_Platform/Policies_and_Standards/Catalogue/Release/Appendix_B_Guidelines_and_Best_Practices/Guide_to_Harmonized_ISO_19115:2003_NAP)
* iso19139-flanders, updated iso19139 to be compatible with open data in the Belgian/EU region Flanders.
* Local schema, specified with ```--schema_local=/path/to/my-schema```

### Using the API from Python

```python
from pygeometa import render_template
# default schema
xml_string = render_template('/path/to/file.mcf', schema='iso19139')
# user-defined schema
xml_string = render_template('/path/to/file.mcf', schema_local='/path/to/new-schema')
with open('output.xml', 'w') as ff:
    ff.write(xml_string)
```

## Development

### Setting up a Development Environment

Same as installing a package.  Use a virtualenv.  Also install developer requirements:

```bash
pip install -r requirements-dev.txt
```

### Adding Another Metadata Schema to the Core

List of supported metadata schemas in `pygeometa/templates/`

To add support to new metadata schemas:
```bash
cp -r pygeometa/templates/iso19139 pygeometa/templates/new-schema
```
Then modify `*.j2` files in the new `pygeometa/templates/new-schema` directory to comply to new metadata schema.

### Running Tests

```bash
# via distutils
python setup.py test
# manually
cd tests
python run_tests.py
```

### Bugs and Issues

All bugs, enhancements and issues are managed on [GitHub](https://github.com/laurensdv/pygeometa/issues).

## History

This pygeometadata branch intends to make it possible to transform iso19139 ->
geodcat-ap and vise versa (maximizing losslessness and validity).

pygeometa originated within an internal project called pygdm, which provided generic geospatial data management functions.  pygdm (now at end of life) was used for generating MSC/CMC geospatial metadata.  pygeometa was pulled out of pygdm to focus on the core requirement of generating geospatial metadata within a real-time environment.

In 2015 pygeometa was made publically available in support of the
Canadian Treasury Board [Policy on Acceptable Network and Device Use](http://www.tbs-sct.gc.ca/pol/doc-eng.aspx?id=27122).

## Contact (this branch only)

* [Laurens De Vocht](mailto:laurens.devocht@ugent.be)
