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
from io import BytesIO
from xml.dom import minidom
import lxml.etree as ET
from pygeometa.dcatap2iso19139 import convert
import tempfile

from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound

from six.moves.configparser import ConfigParser

__version__ = '0.1.1'

LOGGER = logging.getLogger(__name__)

TEMPLATES = '%s%stemplates' % (os.path.dirname(os.path.realpath(__file__)),
                               os.sep)

TRANSFORMATIONS = '%s%stransformations' % (
os.path.dirname(os.path.realpath(__file__)),
os.sep)


def get_charstring(option, section_items, language,
                   language_alternate=None):
    """convenience function to return unilingual or multilingual value(s)"""

    section_items = dict(section_items)
    option_value1 = ""
    option_value2 = ""

    if language_alternate is None or not language_alternate:  # unilingual
        option_tmp = '{}_{}'.format(option, language)
        if option_tmp in section_items:
            option_value1 = section_items[option_tmp]
        else:
            try:
                option_value1 = section_items[option]
            except KeyError:
                pass  # default=None

        i = 0
        while i < len(re.findall(',', option_value1)):
            i += 1
            option_value2 += ','

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
                      val.toprettyxml(indent=' ' * 2).split('\n') if
                      l.strip()])


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

    def debug(text):
        print(text)

    LOGGER.debug('Setting up template environment {}'.format(abspath))
    env = Environment(loader=FileSystemLoader([abspath, TEMPLATES]))
    env.filters['normalize_datestring'] = normalize_datestring
    env.filters['get_distribution_language'] = get_distribution_language
    env.filters['get_charstring'] = get_charstring
    env.filters['debug'] = debug
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

    return ET.parse(BytesIO(xml))


def iso_to_dcat(xml, schema=None, schema_local=None):
    if schema is None and schema_local is None:
        abspath = '{}{}{}'.format(TRANSFORMATIONS, os.sep,
                                  'geodcat-ap/iso-19139-to-dcat-ap.xsl')
    elif schema_local is None:  # default transforamtions dir
        abspath = '{}{}{}'.format(TRANSFORMATIONS, os.sep, schema)
    elif schema is None:  # user-defined
        abspath = schema_local

    LOGGER.debug('Setting up transformations environment {}'.format(abspath))
    ac = ET.XSLTAccessControl(read_network=True)
    dom = ET.parse(os.path.realpath(xml))
    xslt_root = ET.parse(abspath)
    transform = ET.XSLT(xslt_root, access_control=ac)

    return transform(dom)


def iso_to_html(iso, schema=None, schema_local=None):
    if schema is None and schema_local is None:
        abspath = '{}{}{}'.format(TRANSFORMATIONS, os.sep,
                                  'html/iso2html/xml-to-html-ISO.xsl')
        # Defaults to: https://github.com/geoblacklight/geoblacklight-schema
        # Alternative (included):
        # https://github.com/sul-dlss/geohydra/tree/master/scripts/iso2html
    elif schema_local is None:  # default transformations dir
        abspath = '{}{}{}'.format(TRANSFORMATIONS, os.sep, schema)
    elif schema is None:  # user-defined
        abspath = schema_local

    LOGGER.debug('Setting up transformations environment {}'.format(abspath))
    dom = ET.parse(os.path.realpath(iso))
    xslt_root = ET.parse(abspath)
    ac = ET.XSLTAccessControl(read_network=False)
    transform = ET.XSLT(xslt_root, access_control=ac)

    return transform(dom)


def dcat_to_iso(rdf, schema=None, schema_local=None):
    result = convert(rdf)
    _, fp = tempfile.mkstemp()

    with codecs.open(fp, 'w', encoding='utf-8') as f:
        f.write(u'%s' % result)
    f.close()

    if schema is None:
        schema = 'iso19139-flanders'  # Flanders schema by default

    return render_template(fp, schema, schema_local)


def get_supported_schemas():
    """returns a list of supported schemas"""

    LOGGER.debug('Generating list of supported schemas')
    return os.listdir(TEMPLATES)


def get_abspath(mcf, filepath):
    """helper function absolute file access"""

    abspath = os.path.dirname(os.path.realpath(mcf))
    return os.path.join(abspath, filepath)
