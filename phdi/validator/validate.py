from lxml import etree
from pathlib import Path
import re

namespaces = {
    "hl7": "urn:hl7-org:v3",
    "xsi": "http://www.w3.org/2005/Atom",
    "cda": "urn:hl7-org:v3",
    "sdtc": "urn:hl7-org:sdtc",
    "voc": "http://www.lantanagroup.com/voc",
}


def get_parsed_file(file_path):
    file = open(file_path, "r")
    return etree.parse(file)


def validate(file_path, config):
    tree = get_parsed_file(Path(__file__).parent / file_path)
    error_messages = []
    for field in config.get("requiredFields"):
        print(field)
        path = field.get("cdaPath")
        matched_nodes = tree.xpath(path, namespaces=namespaces)
        for node in matched_nodes:
            # attributes check
            error_messages.append(validate_attribute(field, node))
            # text check
            error_messages.append(validate_text(field, node))
    if error_messages:
        return False, error_messages
    return True, error_messages


def validate_attribute(field, node):
    """
    Validates a node by checking if attribute exists or matches regex pattern.
    If the node does not pass a test as described in the config, an error message is
    appended. All fields are valid if the error message list is blank

    :param field: A dictionary entry that describes what fields need to be
        validated and how
    :param node: A dictionary entry that includes the attribute name key and
        value.
    """
    attribute_value = ""
    error_messages = []
    for attribute in field.get("attributes"):
        if "attributeName" in attribute:
            attribute_name = attribute.get("attributeName")
            attribute_value = node.get(attribute_name)
            if not attribute_value:
                error_messages.append(
                    f"Could not find attribute {attribute_name} for tag {field.get('fieldName')}"
                )
        if "regEx" in attribute:
            pattern = re.compile(attribute.get("regEx"))
            if not pattern.match(attribute_value):
                error_messages.append(
                    f"Attribute '{attribute_name}' not in expected format"
                )
    return error_messages


def _print_nodes(nodes):
    for node in nodes:
        print(node)


def validate_text(field, node):
    """
    Validates a node text by checking if it has a parent that matches the schema.
    Then it validates that the text of the node matches is there or matches the
    regEx listed in the schema

    :param field: A dictionary entry that describes what fields need to be
        validated and how
    :param node: A dictionary entry that includes the attribute name key and
        value.
    """
    if field.get("textRequired"):
        found = False
        parent_found = False
        parent_node = node.getparent() if field.get("parent") else None
        # If there is no parent, just set parent found to true
        if parent_node is None:
            parent_found, error_messages_parents = (True, [])
        else:
            parent_found, error_messages_parents = field_matches(
                {
                    "fieldName": field.get("parent"),
                    "attributes": field.get("parent_attributes"),
                },
                parent_node,
            )
        found, error_messages = field_matches(field, node)
        error_messages += error_messages_parents
        if found is not True or parent_found is not True:
            return (False, error_messages)
        if error_messages:
            return (True, error_messages)
        else:
            return (True, [])


def field_matches(field, node):
    # If it has the wrong parent, go to the next one
    fieldName = (
        field.get("nodeName") if field.get("nodeName") else field.get("fieldName")
    )
    if fieldName.lower() not in node.tag.lower():
        return (False, [])
    # Check if it has the right attributes
    if field.get("attributes"):
        attributes_dont_match = []
        field_attributes = field.get("attributes")
        if field_attributes:
            for attribute in field_attributes:
                # For each attribute see if it has a regEx and match it
                if attribute.get("regEx"):
                    pattern = re.compile(attribute.get("regEx"))
                    text = node.get(attribute.get("attributeName"))
                    text = text if text is not None else ""
                    if not pattern.match(text):
                        attributes_dont_match.append(
                            "Attribute: "
                            + attribute.get("attributeName")
                            + " does not match regex"
                        )
                else:
                    if not field.get(attribute.get("attributeName")):
                        attributes_dont_match.append(
                            "Attribute: "
                            + attribute.get("attributeName")
                            + " not found"
                        )
            if attributes_dont_match:
                return (False, [])
    else:
        if node.attrib:
            return (False, [])
    if field.get("textRequired") is not None:
        text = "".join(node.itertext())
        regEx = field.get("regEx")
        if regEx is not None:
            pattern = re.compile(regEx)
            if pattern.match(text) is None:
                return (
                    True,
                    [
                        "Field: "
                        + field.get("fieldName")
                        + " does not match regEx: "
                        + field.get("regEx")
                    ],
                )
            else:
                return (True, [])
        else:
            if text is not None:
                return (True, [])
            else:
                return (
                    True,
                    ["Field: " + field.get("fieldName") + " does not have text"],
                )
    return (True, [])
