from lxml import isoschematron
from lxml import etree
from pathlib import Path


def run_schema(rules_file, xml_file):

    rules = open(rules_file, "r")
    xml_content = open(xml_file, "r")

    sct_doc = etree.parse(rules)
    schematron = isoschematron.Schematron(sct_doc, store_report=True)

    doc = etree.parse(xml_content)

    validation_result = schematron.validate(doc)
    report = schematron.validation_report

    if validation_result:
        print("passed")
    else:
        print("failed")
        print(report)

        reportFile = open("report.html", "wb")
        report.write(reportFile)


def main():
    schema_p = Path(__file__).with_name("schema.sch")
    ecr_p = Path(__file__).with_name("ecr_sample_input.xml")
    run_schema(schema_p, ecr_p)


main()
