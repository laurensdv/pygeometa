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

import os
import unittest
from collections import OrderedDict

from six import text_type, binary_type
import tempfile
import codecs
import lxml.etree as ET
import re

from pygeometa import (read_mcf, pretty_print,
                       render_template, get_charstring, get_supported_schemas)

from pygeometa import (iso_to_dcat)
from pygeometa.dcatap2iso19139 import convert

import dateutil.parser as D

THISDIR = os.path.dirname(os.path.realpath(__file__))


def msg(test_id, test_description):
    """convenience function to print out test id and desc"""
    return '%s: %s' % (test_id, test_description)


def normalize_space(inp):
    if ',' in inp:  # sort arrays just in case
        arr = inp.split(',')
        arr.sort()
        inp = ','.join(arr)
    inp = inp.strip()
    inp = re.sub(r'\s+', ' ', inp)
    return inp


def get_values(mcf1):
    try:
        iteritems = dict.iteritems
    except AttributeError:
        iteritems = dict.items
    values = set()
    for k, v in iteritems(mcf1):
        if v and v is not None:
            if type(v) is dict or type(v) is OrderedDict:
                for t, c in iteritems(v):
                    if '__name__' not in t:
                        if c and c is not None:
                            try:
                                values.add(D.parse(c).strftime("%d-%m-%y"))  # convert timestamps to same format
                            except ValueError:
                                values.add(normalize_space(c))
                            except TypeError:
                                values.add(normalize_space(c))

            else:
                if '__name__' not in k:
                    try:
                        values.add(D.parse(v).strftime("%d-%m-%y"))
                    except ValueError:
                        values.add(normalize_space(v))
                    except TypeError:
                        values.add(normalize_space(v))
    return values


class PygeometaTest(unittest.TestCase):
    """Test suite for package pygeometa"""

    def setUp(self):
        """setup test fixtures, etc."""

        print(msg(self.id(), self.shortDescription()))

    def tearDown(self):
        """return to pristine state"""

        pass

    def test_read_mcf(self):
        """Test reading MCF files"""

        with self.assertRaises(IOError):
            mcf = read_mcf(get_abspath('../404.mcf'))

        mcf = read_mcf(get_abspath('../sample.mcf'))
        self.assertIsInstance(mcf, dict, 'Expected dict')

        self.assertTrue('metadata' in mcf, 'Expected metadata section')

    def test_pretty_print(self):
        """Test pretty-printing"""

        xml = render_template(get_abspath('../sample.mcf'), 'iso19139')
        xml2 = pretty_print(ET.tostring(xml.getroot()))

        self.assertIsInstance(xml2, text_type, 'Expected unicode string')
        self.assertEqual(xml2[-1], '>', 'Expected closing bracket')
        self.assertTrue(xml2.startswith('<?xml'), 'Expected XML declaration')

    def test_get_charstring(self):
        """Test support of unilingual or multilingual value(s)"""

        values = get_charstring('title', {'title': 'foo'}, 'en')
        self.assertEqual(values, ['foo', ''], 'Expected specific values')

        values = get_charstring('title',
                                {'title_en': 'foo', 'title_fr': 'bar'},
                                'en', 'fr')
        self.assertEqual(values, ['foo', 'bar'], 'Expected specific values')

        values = get_charstring('title',
                                {'title': 'foo', 'title_fr': 'bar'},
                                'en', 'fr')
        self.assertEqual(values, ['foo', 'bar'], 'Expected specific values')

        values = get_charstring('title',
                                {'title_fr': 'foo', 'title_en': 'bar'},
                                'fr', 'en')
        self.assertEqual(values, ['foo', 'bar'], 'Expected specific values')

        values = get_charstring('title',
                                {'title_fr': 'foo', 'title_en': 'bar'}, 'fr')
        self.assertEqual(values, ['foo', ''], 'Expected specific values')

        values = get_charstring('notfound',
                                {'title_fr': 'foo', 'title_en': 'bar'}, 'fr')
        self.assertEqual(values, ['', ''], 'Expected specific values')

    def test_get_supported_schemas(self):
        """Test supported schemas"""

        schemas = sorted(get_supported_schemas())
        schemas.remove('common')  # remove shared snippets
        self.assertIsInstance(schemas, list, 'Expected list')
        self.assertEqual(len(schemas), 3, 'Expected 3 supported schemas')
        self.assertEqual(schemas, sorted(['iso19139', 'iso19139-hnap', 'iso19139-flanders']),
                         'Expected exact list of supported schemas')

    def test_render_template(self):
        """test template rendering"""

        xml = render_template(get_abspath('../sample.mcf'), 'iso19139')
        self.assertIsInstance(ET.tostring(xml.getroot()), binary_type, 'Expected unicode string')

        # no schema provided
        # with self.assertRaises(RuntimeError):
        #   render_template(get_abspath('../sample.mcf'))

        # bad schema provided
        with self.assertRaises(RuntimeError):
            xml = render_template(get_abspath('../sample.mcf'), 'bad_schema')

        # bad schema_local provided
        with self.assertRaises(RuntimeError):
            xml = render_template(get_abspath('../sample.mcf'),
                                  schema_local='/bad_schema/path')

        # good schema_local provided
        xml = render_template(get_abspath('../sample.mcf'),
                              schema_local=get_abspath('sample_schema'))

    def test_nested_mcf(self):
        """test nested mcf support"""

        mcf = read_mcf(get_abspath('child.mcf'))

        self.assertEqual(mcf['metadata']['identifier'], '1234',
                         'Expected specific identifier')

        self.assertEqual(mcf['identification']['title_en'],
                         'title in English',
                         'Expected specific title')

        self.assertIsInstance(mcf, dict, 'Expected dict')

    # RDF -{1}> XML -> RDF -{2}> XML: {1} ?== {2}
    def test_rdf_lossless(self):
        """Test RDF2XML2RDF"""

        # RDF -{1}> XML
        rdf = get_abspath('./sample_conversions/afghanistan.ttl')
        result = convert(rdf)
        _, fp = tempfile.mkstemp()

        with codecs.open(fp, 'w', encoding='utf-8') as f:
            f.write(u'%s' % result)
        f.close()

        # {1}
        mcf1 = read_mcf(os.path.realpath(fp))

        xml = render_template(fp, schema='iso19139-flanders')

        _, xp = tempfile.mkstemp()
        f = open(xp, 'wb')
        xml.write(f)
        f.close()

        # XML -> RDF
        rdf_content = iso_to_dcat(get_abspath(xp))

        _, rp = tempfile.mkstemp()
        f = open(rp, 'wb')
        rdf_content.write(f)
        f.close()

        # RDF -{2}> XML
        rdf2 = os.path.realpath(rp)
        result = convert(rdf2)
        _, fp2 = tempfile.mkstemp()

        with codecs.open(fp2, 'w', encoding='utf-8') as f:
            f.write(u'%s' % result)
        f.close()

        # {2}
        mcf2 = read_mcf(os.path.realpath(fp2))

        # {1} ? == {2}
        mcf1 = get_values(mcf1)
        mcf2 = get_values(mcf2)
        self.assertSetEqual(mcf1, mcf2)

    # XML -> RDF -{1}> XML -> RDF -{2}> XML: {1} ?== {2}
    def test_xml_lossless(self):
        """Test XML2RDF2XML"""

        test_files = [
            './sample_conversions/ds_md_ispra-0001.xml',
            './sample_conversions/srv_md_ispra-0001.xml',
            './gent.xml'
        ]

        for t in test_files:
            # XML -> RDF
            rdf_content = iso_to_dcat(get_abspath(t))

            _, rp = tempfile.mkstemp()
            f = open(rp, 'wb')
            rdf_content.write(f)
            f.close()

            # RDF -{1}> XML
            rdf = os.path.realpath(rp)
            result = convert(rdf)
            _, fp = tempfile.mkstemp()

            with codecs.open(fp, 'w', encoding='utf-8') as f:
                f.write(u'%s' % result)
            f.close()

            # {1}
            mcf1 = read_mcf(os.path.realpath(fp))

            xml = render_template(fp, schema='iso19139-flanders')

            _, xp = tempfile.mkstemp()
            f = open(xp, 'wb')
            xml.write(f)
            f.close()

            # XML -> RDF
            rdf_content2 = iso_to_dcat(os.path.realpath(xp))

            _, rp2 = tempfile.mkstemp()
            f = open(rp2, 'wb')
            rdf_content2.write(f)
            f.close()

            # RDF -{2}> XML
            rdf2 = os.path.realpath(rp2)
            result = convert(rdf2)
            _, fp2 = tempfile.mkstemp()

            with codecs.open(fp2, 'w', encoding='utf-8') as f:
                f.write(u'%s' % result)
            f.close()

            # {2}
            mcf2 = read_mcf(os.path.realpath(fp2))

            # {1} ? == {2}
            mcf1 = get_values(mcf1)
            mcf2 = get_values(mcf2)
            self.assertSetEqual(mcf1, mcf2)


def get_abspath(filepath):
    """helper function absolute file access"""

    return os.path.join(THISDIR, filepath)


if __name__ == '__main__':
    unittest.main()
