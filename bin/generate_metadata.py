#!/usr/bin/env python
# =================================================================
#
# Terms and Conditions of Use
#
# Unless otherwise noted, computer program source code of this
# distribution # is covered under Crown Copyright, Government of
# Canada, and is distributed under the MIT License.
#
# The Canada wordmark and related graphics associated with this
# distribution are protected under trademark law and copyright law.
# No permission is granted to use them outside the parameters of
# the Government of Canada's corporate identity program. For
# more information, see
# http://www.tbs-sct.gc.ca/fip-pcim/index-eng.asp
#
# Copyright title to all 3rd party software distributed with this
# software is held by the respective copyright holders as noted in
# those files. Users are asked to read the 3rd Party Licenses
# referenced with those assets.
#
# Copyright (c) 2015 Government of Canada
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import click

from lxml import etree as ET

from pygeometa import get_supported_schemas, render_template, iso_to_dcat, dcat_to_iso, iso_to_html

SUPPORTED_SCHEMAS = get_supported_schemas()


@click.command()
@click.option('--mcf',
              type=click.Path(exists=True, resolve_path=True),
              help='Path to metadata control file (.mcf)')
@click.option('--rdf',
              type=click.Path(exists=True, resolve_path=True),
              help='Path to GeoDCAT-AP RDF file (.ttl/.rdf/.json/.jsonld/.nt/.nq/.n3)')
@click.option('--xml',
              type=click.Path(exists=True, resolve_path=True),
              help='Path to ISO-19139 metadata file (.xml)')
@click.option('--output', type=click.File('wb'),
              help='Name of output file')
@click.option('--html', is_flag=True)
@click.option('--schema',
              type=click.Choice(SUPPORTED_SCHEMAS),
              help='Metadata schema')
@click.option('--schema_local',
              type=click.Path(exists=True, resolve_path=True,
                              dir_okay=True, file_okay=False),
              help='Locally defined metadata schema')
def process_args(mcf, rdf, xml, html, schema, schema_local, output):
    if xml is not None and rdf is None:
        if html:
            t_output = iso_to_html(xml, schema=schema, schema_local=schema_local)
        else:
            t_output = iso_to_dcat(xml, schema=schema, schema_local=schema_local)

        if output is None:
            click.echo_via_pager(t_output)
        else:
            output.write(t_output)

    elif rdf is not None and xml is None:
        xml_output = dcat_to_iso(rdf, schema=schema, schema_local=schema_local)

        if output is None:
            click.echo_via_pager(ET.tostring(xml_output.getroot()))
        else:
            xml_output.write(output)

    elif (rdf is None or xml is None) and mcf is None:
        raise click.UsageError('Missing arguments')

    elif (mcf is None or (schema is None and schema_local is None)) and (rdf is None or xml is None):
        raise click.UsageError('Missing arguments')

    else:
        content = render_template(mcf, schema=schema,
                                  schema_local=schema_local)
        if output is None:
            click.echo_via_pager(content)
        else:
            output.write(content)


if __name__ == '__main__':
    process_args()
