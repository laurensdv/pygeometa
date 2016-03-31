import rdflib
import os
import re
import json

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
            print(row['hierarchyLevel'])
            if "spatialdataservicetype" in row['hierarchyLevel'].lower():
                result += "spatialdataservicetype=%s\n" % row['hierarchyLevel'].lower()[row['hierarchyLevel'].rfind('/')+1:]
            elif not "hierarchyLevel" in result:
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
                  dc:title ?title .
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
           }""")

    result += "\n[identification]\n"

    for row in qres:
        if row['title'] is not None:
            result += "title_%s=%s\n" % (row['title'].language, row['title'])  # title_nl?

        if row['alternativeTitle'] is not None:
            result += "alternative_title_%s=%s\n" % (row['alternativeTitle'].language, row['alternativeTitle'])

        if row['abstract'] is not None:
            result += "abstract_%s=%s\n" % (row['abstract'].language, row['abstract'])

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
            result += "url_%s=%s\n" % (row['url'].language, row['url'])  # include language tag?

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
              OPTIONAL {
                  ?theme skos:inScheme ?scheme .
                  ?scheme a skos:ConceptScheme ;
                         dc:title ?scheme_title ;
                         dc:issued ?scheme_issued } .
              OPTIONAL { ?scheme dc:type ?scheme_type } .
           }""")

    keywords = {}
    keywords_noCategory = set()
    issued = {}
    language = {}

    for row in qres:
        if row['keywordNoCat'] is not None:
            keywords_noCategory.add(row['keywordNoCat'])

        if row['theme'] is not None:
            if row['scheme_title'] not in keywords.keys():
                keywords[row['scheme_title']] = []
            keywords[row['scheme_title']].append(row['keyword'])
            issued[row['scheme_title']] = row['scheme_issued']
            language[row['scheme_title']] = row['keyword'].language

    if len(keywords_noCategory) > 0:
        result += 'keywords_%s=%s\n' % (list(keywords_noCategory)[0].language, ','.join(keywords_noCategory))  # keywords_nl?

    if len(keywords.keys()) > 0:
        result += 'thesauri=%s\n' % '\/'.join(keywords.keys())

    for thesaurus in keywords.keys():
        result += '\n[%s]\n' % thesaurus
        result += 'keywords_%s=%s\n' % (language[thesaurus], ','.join(keywords[thesaurus]))  # keywords_nl?
        result += 'issued=%s\n' % issued[thesaurus]
        if row['scheme_type'] is not None:
            result += 'keywords_type=%s\n' % row['scheme_type']

    qres = g.query(
        PREFIXES +
        """SELECT DISTINCT *
           WHERE {
              OPTIONAL { ?md adms:representationTechnique ?datatype } .
              OPTIONAL {
                ?md dc:conformsTo ?crsr .
                ?crsr dc:type <http://inspire.ec.europa.eu/glossary/SpatialReferenceSystem> ;
                      skos:inScheme ?crss .
                ?crss dc:title ?crst .
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
    for row in qres:
        if row['datatype'] is not None:
            result += 'datatype=%s\n' % row['datatype'][row['datatype'].rfind('/')+1:]

        if "crs=" not in result:
            if row['crsl'] is not None:
                result += 'crs=%s\n' % row['crsl']
                if row['crst'] is not None:
                    result += 'crst=%s\n' % row['crst']

            elif row['crsu'] is not None:
                result += 'crs=%s\n' % row['crsu']

        if row['geometry'] is not None:
            geometries.add(row['geometry'])


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

    def extract_contact( role, category):
        res = ""

        qr = g.query(
            PREFIXES +
            """SELECT DISTINCT *
               WHERE {
                  ?agent dc:type <http://inspire.ec.europa.eu/metadata-codelist/ResponsiblePartyRole/%s> .
                  ?agent prov:agent ?pointOfContact .
                  ?pointOfContact ?vcard:organization-name ?organization .
                  ?pointOfContact ?vcard:hasEmail ?email .
                  OPTIONAL { ?pointOfContact ?vcard:hasUrl ?url } .
                  OPTIONAL { ?pointOfContact ?vcard:title ?title } .
                  OPTIONAL { ?pointOfContact ?vcard:fn ?name } .
                  OPTIONAL {
                    ?pointOfContact ?vcard:hasTelephone ?tel .
                    ?tel vcard:hasValue ?phone .
                    ?tel a vcard:Voice } .
                  OPTIONAL {
                    ?pointOfContact ?vcard:hasTelephone ?fax .
                    ?fax vcard:hasValue ?faxno .
                    ?fax a vcard:Fax } .
               } LIMIT 1""" % role)

        res += '\n[contact:%s]\n' % category

        for r in qr:
            if row['organization'] is not None:
                res += "organization_%s=%s\n" % (r['organization'].language, r['organization'])
            if row['e-mail'] is not None:
                res += "url=%s\n" % r['e-mail'][len('mailto:'):]
            if row['url'] is not None:
                res += "url=%s\n" % r['url']
            if row['title'] is not None:
                res += "positionname=%s\n" % r['title']
            if row['name'] is not None:
                res += "individualname=%s\n" % r['name']
            if row['phone'] is not None:
                res += "phone=%s\n" % r['phone'][len('tel:'):]
            if row['faxno'] is not None:
                res += "fax=%s\n" % r['faxno'][len('tel:'):]

        return res

    result += extract_contact('pointOfContact','main')

    return result





