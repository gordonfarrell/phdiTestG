from pathlib import Path
import xmlschema

schema_p = Path(__file__).with_name("CDA_SDTC.xsd")
ecr_p = Path(__file__).with_name("ecr_sample_input.xml")
schema = xmlschema.XMLSchema(schema_p)
print(schema.validate(ecr_p))
