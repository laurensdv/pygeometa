#!/usr/bin/env python
# =================================================================
# Modifications and Extensions Copyrighted 2016 
# by Laurens De Vocht - iMinds - UGent
# All rights reserved
# For more information about licensing please contact us.
# =================================================================
# Original sources covered under Crown Copyright, Government of
# Canada, and distributed under the MIT License.
# Copyright (c) 2015 Government of Canada
# =================================================================

import click

from lxml import etree as ET

from pygeometa import get_supported_schemas, render_template, iso_to_dcat, dcat_to_iso, iso_to_html
from pygeometa.validation.validator import Validators

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
@click.option('--html', is_flag=True, help='Output HTML')
@click.option('--validate', is_flag=True, help='Validate XML')
@click.option('--schema',
              type=click.Choice(SUPPORTED_SCHEMAS),
              help='Metadata schema')
@click.option('--schema_local',
              type=click.Path(exists=True, resolve_path=True,
                              dir_okay=True, file_okay=False),
              help='Locally defined metadata schema')
def process_args(mcf, rdf, xml, html, validate, schema, schema_local, output):
    if xml is not None and rdf is None:
        if validate:
                if schema is not None:
                    profiles = schema.split(',')
                else:
                    profiles = ["iso19139latest"]
                v = Validators(profiles)
                t_output = v.is_valid(ET.parse(open(xml)))

        elif html:
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
