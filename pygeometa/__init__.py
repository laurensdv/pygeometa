# =================================================================
# Modifications Copyrighted 2016 by Laurens De Vocht - iMinds - UGent
# Released under the most strict MIT compatible license
# =================================================================

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

import codecs
import logging
import os
import re
from xml.dom import minidom
import lxml.etree as ET
import rdflib

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound

from six.moves.configparser import ConfigParser

__version__ = '0.1.0'

LOGGER = logging.getLogger(__name__)

TEMPLATES = '%s%stemplates' % (os.path.dirname(os.path.realpath(__file__)),
                               os.sep)

TRANSFORMATIONS = '%s%stransformations' % (os.path.dirname(os.path.realpath(__file__)),
                                           os.sep)

PREFIXES = """prefix foaf: <http://xmlns.com/foaf/0.1/>
prefix dc: <http://purl.org/dc/terms/>
prefix dcat: <http://www.w3.org/ns/dcat#>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
prefix vcard: <http://www.w3.org/2006/vcard/ns#>
prefix prov: <http://www.w3.org/ns/prov#>
prefix content: <http://www.w3.org/2011/content#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix skos: <http://www.w3.org/2004/02/skos/core#>
prefix locn: <http://www.w3.org/ns/locn#>
prefix gsp: <http://www.opengis.net/ont/geosparql#>
prefix geo: <https://www.iana.org/assignments/media-types/application/vnd.geo+>
prefix schema: <http://schema.org/>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix adms: <http://www.w3.org/ns/adms#>
prefix iso: <http://def.seegrid.csiro.au/isotc211/iso19115/2003/metadata#>

"""

def get_charstring(option, section_items, language,
                   language_alternate=None):
    """convenience function to return unilingual or multilingual value(s)"""

    section_items = dict(section_items)
    option_value1 = None
    option_value2 = None

    if 'language_alternate' is None:  # unilingual
        option_tmp = '{}_{}'.format(option, language)
        if option_tmp in section_items:
            option_value1 = section_items[option_tmp]
        else:
            try:
                option_value1 = section_items[option]
            except KeyError:
                pass  # default=None
    else:  # multilingual
        option_tmp = '{}_{}'.format(option, language)
        if option_tmp in section_items:
            option_value1 = section_items[option_tmp]
        else:
            try:
                option_value1 = section_items[option]
            except KeyError:
                pass  # default=None
        option_tmp2 = '{}_{}'.format(option, language_alternate)
        if option_tmp2 in section_items:
            option_value2 = section_items[option_tmp2]

    return [option_value1, option_value2]


def get_distribution_language(section):
    """derive language of a given distribution construct"""

    try:
        return section.split(':')[1].split('_')[1]
    except IndexError:
        return 'en'


def normalize_datestring(datestring, fmt='default'):
    """groks date string into ISO8601"""

    re1 = r'\$Date: (?P<year>\d{4})'
    re2 = r'\$Date: (?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})'
    re3 = r'(?P<start>.*)\$Date: (?P<year>\d{4}).*\$(?P<end>.*)'

    if datestring.startswith('$Date'):  # svn Date keyword
        if fmt == 'year':
            mo = re.match(re1, datestring)
            return mo.group('year')
        else:  # default
            mo = re.match(re2, datestring)
            return '%sT%s' % mo.group('date', 'time')
    elif datestring.find('$Date') != -1:  # svn Date keyword embedded
        if fmt == 'year':
            mo = re.match(re3, datestring)
            return '%s%s%s' % mo.group('start', 'year', 'end')
    return datestring


def read_mcf(mcf):
    """returns dict of ConfigParser object"""

    mcf_list = []

    def makelist(mcf2):
        """recursive function for MCF by reference inclusion"""
        c = ConfigParser()
        LOGGER.debug('reading {}'.format(mcf2))
        with codecs.open(mcf2, encoding='utf-8') as fh:
            c.readfp(fh)
            mcf_dict = c.__dict__['_sections']
            for section in mcf_dict.keys():
                if 'base_mcf' in mcf_dict[section]:
                    base_mcf_path = get_abspath(mcf,
                                                mcf_dict[section]['base_mcf'])
                    makelist(base_mcf_path)
                    mcf_list.append(mcf2)
                else:  # leaf
                    mcf_list.append(mcf2)

    makelist(mcf)

    c = ConfigParser()

    for mcf_file in mcf_list:
        LOGGER.debug('reading {}'.format(mcf))
        with codecs.open(mcf_file, encoding='utf-8') as fh:
            c.readfp(fh)
    mcf_dict = c.__dict__['_sections']
    return mcf_dict


def pretty_print(xml):
    """clean up indentation and spacing"""

    LOGGER.debug('pretty-printing XML')
    val = minidom.parseString(xml)
    return '\n'.join([l for l in
                      val.toprettyxml(indent=' ' * 2).split('\n') if l.strip()])


def render_template(mcf, schema=None, schema_local=None):
    """convenience function to render Jinja2 template"""

    LOGGER.debug('Evaluating schema path')
    if schema is None and schema_local is None:
        msg = 'schema or schema_local required'
        LOGGER.exception(msg)
        raise RuntimeError(msg)
    if schema_local is None:  # default templates dir
        abspath = '{}{}{}'.format(TEMPLATES, os.sep, schema)
    elif schema is None:  # user-defined
        abspath = schema_local

    LOGGER.debug('Setting up template environment {}'.format(abspath))
    env = Environment(loader=FileSystemLoader([abspath, TEMPLATES]))
    env.filters['normalize_datestring'] = normalize_datestring
    env.filters['get_distribution_language'] = get_distribution_language
    env.filters['get_charstring'] = get_charstring
    env.globals.update(zip=zip)
    env.globals.update(get_charstring=get_charstring)
    env.globals.update(normalize_datestring=normalize_datestring)

    try:
        LOGGER.debug('Loading template')
        template = env.get_template('main.j2')
    except TemplateNotFound:
        msg = 'Missing metadata template'
        LOGGER.exception(msg)
        raise RuntimeError(msg)

    LOGGER.debug('Processing template')
    xml = template.render(record=read_mcf(mcf),
                          software_version=__version__).encode('utf-8')
    return pretty_print(xml)


def iso_to_dcat(xml, schema=None, schema_local=None):
    if schema is None and schema_local is None:
        abspath = '{}{}{}'.format(TRANSFORMATIONS, os.sep, 'geodcat-ap/iso-19139-to-dcat-ap.xsl')
    elif schema_local is None:  # default transforamtions dir
        abspath = '{}{}{}'.format(TRANSFORMATIONS, os.sep, schema)
    elif schema is None:  # user-defined
        abspath = schema_local

    LOGGER.debug('Setting up transformations environment {}'.format(abspath))
    dom = ET.parse(os.path.realpath(xml))
    xslt_root = ET.parse(abspath)
    transform = ET.XSLT(xslt_root)
    newdom = transform(dom)

    return unicode(ET.tostring(newdom, pretty_print=True), "UTF-8")

def dcat_to_iso(rdf, schema=None, schema_local=None):
    g = rdflib.Graph()
    g.parse(os.path.realpath(rdf))

    result = ""
    qres = g.query(  # Mandatory -> required; Optional -> OPTIONAL
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              ?md foaf:isPrimaryTopicOf ?a .
              ?a a dcat:CatalogRecord ;
              dc:language ?language ;
              dc:identifier ?identifier ;
              dc:modified ?datestamp ;
              dc:source ?source .
              ?source content:characterEncoding ?charset .
              OPTIONAL { ?a dc:hasParent ?parent } .
              OPTIONAL { ?source dc:conformsTo ?c } .
              OPTIONAL { ?c dc:title ?metadatastandardname } .
              OPTIONAL { ?c owl:versionInfo ?metadatastandardversion } .
           } LIMIT 1""")

    result += "[metadata]\n"

    for row in qres:
        if row['language'] is not None:
            result += "language=%s\n" % (row['language'][-3:].lower())
        if row['identifier'] is not None:
            result += "identifier=%s\n" % row['identifier']
        if row['parent'] is not None:
            result += "parent=%s\n" % row['parent']
        if row['charset'] is not None:
            result += "charset=%s\n" % re.sub(r'\W+', '', row['charset'].lower())
        if row['datestamp'] is not None:
            result += "datestamp=%s\n" % row['datestamp']

    qres = g.query(
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              ?md dc:type ?hierarchyLevel .
              ?md foaf:isPrimaryTopicOf ?a .
           }""")

    for row in qres:
        if row['hierarchyLevel'] is not None:
            if "dataset" in row['hierarchyLevel'].lower():
                result += "hierarchylevel=dataset\n"
            elif "service" in row['hierarchyLevel'].lower():
                result += "hierarchylevel=service\n"
            elif "catalog" in row['hierarchyLevel'].lower():
                result += "hierarchylevel=discovery\n"
            elif "series" in row['hierarchyLevel'].lower():
                result += "hierarchylevel=series\n"

    qres = g.query(
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              ?md foaf:isPrimaryTopicOf ?a .
              ?a a dcat:CatalogRecord ;
              dc:source ?source .
              ?source dc:conformsTo ?c .
              OPTIONAL { ?c dc:title ?metadatastandardname } .
              OPTIONAL { ?c owl:versionInfo ?metadatastandardversion } .
           } LIMIT 1""")

    for row in qres:
        if row['metadatastandardname'] is not None:
            result += "metadatastandardname=%s\n" % row['metadatastandardname']
        if row['metadatastandardversion'] is not None:
            result += "metadatastandardversion=%s\n" % row['metadatastandardversion']

    qres = g.query(
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              ?md foaf:isPrimaryTopicOf ?a ;
                  dc:description ?abstract ;
                  dc:subject ?topicCategory ;
                  dc:title ?title .
              OPTIONAL {
                  ?md dc:temporal ?temporal .
                  ?temporal a dc:PeriodOfTime ;
                  schema:startDate ?temporal_begin ;
                  schema:endDate ?temporal_end } .
              OPTIONAL { ?md dc:alternative ?alternativeTitle } .
              OPTIONAL { ?md dc:created ?creation_date } .
              OPTIONAL { ?md dc:modified ?revision_date } .
              OPTIONAL { ?md dc:issued ?publication_date } .
              OPTIONAL { ?md adms:status ?status } .
              OPTIONAL { ?md dct:accrualPeriodicity ?maintenance_frequency } .
              OPTIONAL { ?md iso:supplementalInformation ?url } .
           } LIMIT 1""")

    result += "\n[identification]\n"

    for row in qres:
        if row['title'] is not None:
            result += "title=%s\n" % row['title']  # title_nl?

        if row['alternativeTitle'] is not None:
            result += "alternative_title=%s\n" % row['alternativeTitle']

        if row['abstract'] is not None:
            result += "abstract=%s\n" % row['abstract']

        if row['creation_date'] is not None:
            result += "creation_date=%s\n" % row['creation_date']

        if row['publication_date'] is not None:
            result += "publication_date=%s\n" % row['publication_date']

        if row['revision_date'] is not None:
            result += "revision_date=%s\n" % row['revision_date']

        if row['temporal_begin'] is not None:
            result += "temporal_begin=%s\n" % row['temporal_begin']

        if row['temporal_end'] is not None:
            result += "temporal_end=%s\n" % row['temporal_end']

        if row['topicCategory'] is not None:
            result += "topiccategory=%s\n" % row['topicCategory'][len("http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/"):]

        if row['status'] is not None:
            result += "status=%s\n" % row['status'][len("http://purl.org/adms/status/"):]

        if row['url'] is not None:
            result += "url=%s\n" % row['url']  # include language tag?

        if row['maintenance_frequency'] is not None:
            maintenance_frequency = row['maintenance_frequency'][len('http://inspire.ec.europa.eu/metadata-codelist/MaintenanceFrequencyCode/'):].lower()

            if maintenance_frequency == "continuous":
                maintenance_frequency = "continual"
            elif maintenance_frequency == "daily":
                maintenance_frequency = "daily"
            elif maintenance_frequency == "weekly":
                maintenance_frequency = "weekly"
            elif maintenance_frequency == "monthly":
                maintenance_frequency = "monthly"
            elif maintenance_frequency == "biweekly":
                maintenance_frequency = "fortnightly"
            elif maintenance_frequency == "semiannual":
                maintenance_frequency = "biannually"
            elif maintenance_frequency == "annual":
                maintenance_frequency = "annually"
            elif maintenance_frequency == "notplanned":
                maintenance_frequency = "notPlanned"
            elif maintenance_frequency == "asneeded":
                maintenance_frequency = "asNeeded"
            else:
                maintenance_frequency = "irregular"

            result += "maintenancefrequency=%s\n" % maintenance_frequency

    qres = g.query(
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              ?md dcat:theme ?theme .
              ?theme skos:prefLabel ?keyword .
              OPTIONAL {
                  ?theme skos:inScheme ?scheme .
                  ?scheme a skos:ConceptScheme ;
                         dc:title ?scheme_title ;
                         dc:issued ?scheme_issued } .
              OPTIONAL { ?scheme dc:type ?scheme_type }
           }""")

    keywords = {}
    issued = {}
    language = {}

    for row in qres:
        if row['theme'] is not None:
            if row['scheme_title'] not in keywords.keys():
                keywords[row['scheme_title']] = []
            keywords[row['scheme_title']].append(row['keyword'])
            issued[row['scheme_title']] = row['scheme_issued']
            language[row['scheme_title']] = row['keyword'].language
    print(keywords)

    result += 'thesauri=%s\n' % '\/'.join(keywords.keys())

    for thesaurus in keywords.keys():
        result += '\n[%s]\n' % thesaurus
        result += 'keywords_%s=%s\n' % (language[thesaurus], ','.join(keywords[thesaurus]))  # keywords_nl?
        result += 'issued=%s\n' % issued[thesaurus]
        if row['scheme_type'] is not None:
            result += 'keywords_type=%s\n' % row['scheme_type']

    print(result)
    return None

def get_supported_schemas():
    """returns a list of supported schemas"""

    LOGGER.debug('Generating list of supported schemas')
    return os.listdir(TEMPLATES)


def get_abspath(mcf, filepath):
    """helper function absolute file access"""

    abspath = os.path.dirname(os.path.realpath(mcf))
    return os.path.join(abspath, filepath)
