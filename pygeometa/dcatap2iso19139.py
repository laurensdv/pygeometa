# =================================================================
# Copyrighted 2016 by Laurens De Vocht - iMinds - UGent
# All rights reserved
# =================================================================

import rdflib
import os
import re
import json
import datetime

PREFIXES = """prefix foaf: <http://xmlns.com/foaf/0.1/>
prefix dc: <http://purl.org/dc/terms/>
prefix dc11: <http://purl.org/dc/elements/1.1/>
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


def convert(rdf):
    g = rdflib.Graph()
    g.parse(os.path.realpath(rdf), format=rdflib.util.guess_format(os.path.realpath(rdf)))

    result = ""
    qres = g.query(  # Mandatory -> required; Optional -> OPTIONAL
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              ?md foaf:isPrimaryTopicOf ?a .
              ?a a dcat:CatalogRecord .
              OPTIONAL { ?a dc:language ?language } .
              OPTIONAL { ?a dc:identifier ?identifier } .
              OPTIONAL { ?a dc:modified ?datestamp } .
              OPTIONAL { ?a dc:source ?source } .
              OPTIONAL { ?source content:characterEncoding ?charset } .
              OPTIONAL { ?source dc:isPartOf ?parent } .
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
            result += "parentidentifier=%s\n" % row['parent']
        if row['charset'] is not None:
            result += "charset=%s\n" % re.sub(r'\W+', '', row['charset'].lower())

        if row['datestamp'] is not None:
            result += "datestamp=%s\n" % row['datestamp']

    # if no metadata provided create new metadata:
    if len(qres) == 0 or qres is None:
        qres = g.query(
            PREFIXES +
            """SELECT DISTINCT *
               WHERE {
                  { ?uri a dcat:Dataset } UNION { ?uri a dc:Service } .
                  OPTIONAL { ?uri dct:identifier ?identifier } .
                  OPTIONAL { ?uri dct:issued ?issued } .
               } LIMIT 1""")

        for row in qres:
            if row['uri'] is not None:
                if row['identifier'] is not None:
                    result += "identifier=%s\n" % row['identifier']
                else:
                    result += "identifier=%s\n" % row['uri']

                if row['issued'] is not None:
                    result += "datestamp=%s\n" % row['issued']
                else:
                    result += "datestamp=%s\n" % datetime.datetime.now().isoformat()

        result += "charset=%s\n" % 'utf8'

    qres = g.query(
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              { ?md a ?hierarchyLevel } UNION { ?md dc:type ?hierarchyLevel } .
              ?md foaf:isPrimaryTopicOf ?a .
           }""")

    for row in qres:
        if row['hierarchyLevel'] is not None:
            if "spatialdataservicetype" in row['hierarchyLevel'].lower():
                result += "spatialdataservicetype=%s\n" % row['hierarchyLevel'].lower()[row['hierarchyLevel'].rfind('/')+1:]
            elif "hierarchylevel" not in result:
                if "dataset" in row['hierarchyLevel'].lower():
                    result += "hierarchylevel=dataset\n"
                elif "service" in row['hierarchyLevel'].lower():
                    result += "hierarchylevel=service\n"
                elif "catalog" in row['hierarchyLevel'].lower():
                    result += "hierarchylevel=discovery\n"
                elif "series" in row['hierarchyLevel'].lower():
                    result += "hierarchylevel=series\n"

    if len(qres) == 0 or qres is None:
        qres = g.query(
            PREFIXES +
            """SELECT DISTINCT *
               WHERE {
                  ?md a ?hierarchyLevel .
                  FILTER (?hierarchyLevel = dcat:Catalog || ?hierarchyLevel = dcat:Dataset || ?something = dc:Service) .
               }""")

        for row in qres:
            if row['hierarchyLevel'] is not None:
                if "spatialdataservicetype" in row['hierarchyLevel'].lower():
                    result += "spatialdataservicetype=%s\n" % row['hierarchyLevel'].lower()[
                                                              row['hierarchyLevel'].rfind('/') + 1:]
                elif "hierarchylevel" not in result:
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
              { ?md foaf:isPrimaryTopicOf ?a }
              UNION { { ?md a dcat:Dataset } UNION { ?md a dc:Service } } .
              ?md dc:description ?abstract .
              ?md dc:title ?title .
              OPTIONAL { ?md dc:language ?language } .
              OPTIONAL { ?md dc:subject ?topicCategory } .
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
              OPTIONAL {
                ?md dc:accessRights ?rightsStatement .
                ?rightsStatement rdfs:label ?other_constraints } .
              OPTIONAL {
                ?md dc:license ?license .
                ?license rdfs:label ?limitation } .
              OPTIONAL {
                ?md dc:license ?licenseUrl .
                FILTER (!isBlank(?licenseUrl)).
                FILTER (isUri(?licenseUrl)) } .
           } LIMIT 1""")

    result += "\n[identification]\n"

    for row in qres:
        if row['title'] is not None:
            result += "title=%s\n" % row['title']  # title_nl?  row['title'].language

        if row['alternativeTitle'] is not None:
            result += "alternative_title=%s\n" % row['alternativeTitle']  # row['alternativeTitle'].language

        if row['abstract'] is not None:
            result += "abstract=%s\n" % row['abstract'].replace('\n', ' ').replace('\r', '')  # row['abstract'].language

        if row['language'] is not None:
            result += "language=%s\n" % (row['language'][-3:].lower())

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
            result += "topiccategory=%s\n" % row['topicCategory'][
                                             len("http://inspire.ec.europa.eu/metadata-codelist/TopicCategory/"):]

        if row['status'] is not None:
            result += "status=%s\n" % row['status'][len("http://purl.org/adms/status/"):]

        if row['url'] is not None:
            result += "url=%s\n" % row['url']  # include language tag? row['url'].language

        if row['limitation'] is not None:
            result += "limitation=%s\n" % row['limitation']  # include language tag?

        if row['licenseUrl'] is not None:
            result += "license=%s\n" % row['licenseUrl']

        if row['other_constraints'] is not None:
            result += "otherconstraints=%s\n" % row['other_constraints']  # include language tag?

        if row['maintenance_frequency'] is not None:
            maintenance_frequency = row['maintenance_frequency'][len(
                'http://inspire.ec.europa.eu/metadata-codelist/MaintenanceFrequencyCode/'):].lower()

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
              OPTIONAL {
                  ?md dcat:theme ?theme .
                  ?theme skos:prefLabel ?keyword } .
              OPTIONAL { ?md dc11:subject ?keywordNoCat } .
              OPTIONAL { ?md dcat:keyword ?keywordNoCat } .
              OPTIONAL {
                  ?theme skos:inScheme ?scheme .
                  ?scheme a skos:ConceptScheme ;
                         dc:title ?scheme_title ;
                         dc:issued ?scheme_issued } .
              OPTIONAL { ?scheme dc:type ?scheme_type .
                         ?scheme a skos:ConceptScheme } .
           }""")

    keywords = {}
    keywords_no_category = set()
    issued = {}
    language = {}

    for row in qres:
        if row['keywordNoCat'] is not None:
            keywords_no_category.add(row['keywordNoCat'])

        if row['scheme_title'] is None:
            if row['keyword'] is not None:
                keywords_no_category.add(row['keyword'])

        elif row['theme'] is not None:
            if row['scheme_title'] not in keywords.keys():
                keywords[row['scheme_title']] = []
            if row['keyword'] is not None:
                keywords[row['scheme_title']].append(row['keyword'])
                language[row['scheme_title']] = row['keyword'].language
            if row['scheme_issued'] is not None:
                issued[row['scheme_title']] = row['scheme_issued']

    if len(keywords_no_category) > 0:
        result += 'keywords=%s\n' % ','.join(keywords_no_category) # keywords_nl? (list(keywords_no_category)[0].language,

    if len(keywords.keys()) > 0:
        result += 'thesauri=%s\n' % '\/'.join(keywords.keys())

    for thesaurus in keywords.keys():
        result += '\n[%s]\n' % thesaurus
        result += 'keywords=%s\n' % ','.join(keywords[thesaurus]) # keywords_nl? language[thesaurus]
        result += 'issued=%s\n' % issued[thesaurus]
        if row['scheme_type'] is not None:
            result += 'keywords_type=%s\n' % row['scheme_type']

    qres = g.query(
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              OPTIONAL { ?md rdfs:comment ?comment } .
              OPTIONAL { ?d adms:representationTechnique ?datatype } .
              OPTIONAL {
                ?md dc:conformsTo ?crsr .
                ?crsr dc:type <http://inspire.ec.europa.eu/glossary/SpatialReferenceSystem> ;
                      skos:inScheme ?crss .
                OPTIONAL { ?crss dc:title ?crst } .
              } .
              OPTIONAL {
                ?md dc:conformsTo ?crsr .
                { ?crsr skos:prefLabel ?crsl } UNION { ?crsr dc:identifier ?crsl } .
              } .
              OPTIONAL { ?md dc:conformsTo ?crsu . FILTER(isURI(?crsu)) } .
              OPTIONAL {
                ?md dc:spatial ?spatial .
                ?spatial locn:geometry ?geometry } .
           }""")

    result += '\n[spatial]\n'

    geometries = set()
    comments = set()

    for row in qres:
        if row['datatype'] is not None and 'datatype' not in result:
            result += 'datatype=%s\n' % row['datatype'][row['datatype'].rfind('/')+1:]  # What if there are multiple datatypes: i.e. multiple distributions - different datatypes?

        if "crs=" not in result:
            if row['crsl'] is not None:
                result += 'crs=%s\n' % row['crsl']
                if row['crst'] is not None:
                    result += 'crst=%s\n' % row['crst']
                elif row['crss'] is not None:
                    result += 'crst=%s\n' % row['crss']

            elif row['crsu'] is not None:
                result += 'crs=%s\n' % row['crsu']

        if row['geometry'] is not None:
            geometries.add(row['geometry'])

        if row['comment'] is not None:
            comments.add(row['comment'])

    for comment in comments:
        p = re.compile(r'1:[0-9]+')
        match = re.search(p, comment)
        if match:
            result += 'resolution=%s\n' % comment[match.start()+2:match.end()]
        else:
            p = re.compile(r'[0-9.,]+')
            match = re.search(p, comment)
            if match:
                result += 'resolution_d=%s\n' % comment[match.start():match.end()]
                result += 'resolution_d_m=%s\n' % comment[match.end():]


    for geometry in geometries:
        if "JSON" in geometry.datatype.upper():  # TODO: support for other formats as well
            geometry_json = str(geometry)
            geometry_obj = json.loads(geometry_json)
            x = set()
            y = set()
            for coordinate in geometry_obj['coordinates'][0]:
                x.add(coordinate[0])
                y.add(coordinate[1])
            result += "bbox=%s\n" % ",".join([str(min(x)), str(min(y)), str(max(x)), str(max(y))])

    def extract_contact(g, role, category):
        res = ""

        qr = g.query(
            PREFIXES +
            """SELECT DISTINCT *
               WHERE {
                  ?agent dc:type <http://inspire.ec.europa.eu/metadata-codelist/ResponsiblePartyRole/%s> .
                  ?agent prov:agent ?pointOfContact .
                  ?pointOfContact vcard:organization-name ?organization .
                  ?pointOfContact vcard:hasEmail ?email .
                  OPTIONAL { ?pointOfContact vcard:hasUrl ?url } .
                  OPTIONAL { ?pointOfContact vcard:title ?title } .
                  OPTIONAL { ?pointOfContact vcard:fn ?name } .
                  OPTIONAL {
                    ?pointOfContact vcard:hasTelephone ?tel .
                    ?tel vcard:hasValue ?phone .
                    ?tel a vcard:Voice } .
                  OPTIONAL {
                    ?pointOfContact vcard:hasTelephone ?fax .
                    ?fax vcard:hasValue ?faxno .
                    ?fax a vcard:Fax } .
                  OPTIONAL {
                    ?pointOfContact vcard:hasAddress ?address .
                    ?address vcard:street-address ?street .
                    ?address vcard:locality ?city .
                    ?address vcard:postal-code ?postalcode .
                    ?address vcard:country-name ?country .
                  } .
               } LIMIT 1""" % role)

        res += '\n[contact:%s]\n' % category

        for r in qr:
            if r['organization'] is not None:
                res += "organization=%s\n" % r['organization']  # r['organization'].language
            if r['email'] is not None:
                res += "email=%s\n" % r['email'][len('mailto:'):]
            if r['url'] is not None:
                res += "url=%s\n" % r['url']
            if r['title'] is not None:
                res += "positionname=%s\n" % r['title']
            if r['name'] is not None:
                res += "individualname=%s\n" % r['name']
            if r['phone'] is not None:
                res += "phone=%s\n" % r['phone'][len('tel:'):]
            if r['faxno'] is not None:
                res += "fax=%s\n" % r['faxno'][len('tel:'):]
            if r['address'] is not None:
                res += "address=%s\n" % r['street']
                res += "city=%s\n" % r['city']
                res += "postalcode=%s\n" % r['postalcode']
                res += "country=%s\n" % r['country']

        return res

    result += extract_contact(g, 'pointOfContact', 'main')

    result += extract_contact(g, 'distributor', 'distribution')

    qres = g.query(
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              { ?md foaf:homepage ?url } UNION { ?md dcat:landingPage ?url } .
              OPTIONAL { ?url a foaf:Document } .
              OPTIONAL { ?url dc:title ?title } .
              OPTIONAL { ?url dc:description ?description } .
           }""")

    landing_pages = {}

    for row in qres:
        if row['url'] is not None:
            landing_pages[row['url']] = {'title': row['title'], 'description': row['description']}

    i = 0
    for landing_page in landing_pages.keys():
        i += 1
        result += "\n[distribution:url%s]\n" % str(i)
        result += "url=%s\n" % landing_page
        if landing_pages[landing_page]['title'] is not None:
            result += "name=%s\n" % landing_pages[landing_page]['title']  # landing_pages[landing_page]['title'].language
        if landing_pages[landing_page]['description'] is not None:
            result += "description=%s\n" % landing_pages[landing_page]['description']  # landing_pages[landing_page]['description'].language

    qres = g.query(
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              ?distribution a dcat:Distribution .
              OPTIONAL { ?distribution dc:title ?title } .
              OPTIONAL { ?distribution dc:description ?description } .
              OPTIONAL { ?distribution dc:format ?format } .
              OPTIONAL { ?distribution dcat:accessURL ?accessURL } .
              OPTIONAL { ?distribution foaf:page ?page } .
           }""")

    distributions = {}

    for row in qres:
        distributions[row['distribution']] = {'title': row['title'], 'format': row['format'], 'description': row['description'], 'url': row['accessURL'], 'page': row['page']}

    for distribution in distributions.keys():
        i += 1
        result += "\n[distribution:%s]\n" % distribution
        if distributions[distribution]['url'] is not None:
            result += "url=%s\n" % distributions[distribution]['url']
            result += "function=%s\n" % 'download'
        elif distributions[distribution]['page'] is not None:
            result += "url=%s\n" % distributions[distribution]['page']
            result += "function=%s\n" % 'information'

        if distributions[distribution]['format'] is not None:
            result += "format=%s\n" % distributions[distribution]['format']
        if distributions[distribution]['title'] is not None:
            result += "name=%s\n" % distributions[distribution]['title']  # languages?
        if distributions[distribution]['description'] is not None:
            result += "description=%s\n" % distributions[distribution]['description']  # languages?

    return result
