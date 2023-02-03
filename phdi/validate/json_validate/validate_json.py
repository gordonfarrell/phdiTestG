from jsonschema import validate
from pathlib import Path
import json


schema_p = Path(__file__).with_name("json_schema.json")
ecr_p = Path(__file__).with_name("ecr_sample_results.json")

rules = open(schema_p, "r")
xml_content = open(ecr_p, "r")


results = validate(json.load(xml_content), json.load(rules))

print(results)
