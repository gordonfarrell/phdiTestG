import phonenumbers
import pycountry
from typing import Literal, List, Union


def standardize_country_code(
    raw_country: str, code_type: Literal["alpha_2", "alpha_3", "numeric"] = "alpha_2"
) -> str:
    """
    Given a string representation of a country (whether a full name
    such as "United States", or an abbreviation such as "US" or "USA"),
    first identify the country represented by the string, then
    generate the ISO 3611 standardized country identifier of the
    desired type. If the country cannot be determined, the function
    returns None.

    Example: If raw_country = "United States of America," then
      - alpha_2 would be "US"
      - alpha_3 would be "USA"
      - numeric would be "840"

    :param raw_country: String representation of the country to be
      put in ISO 3611 standardized form
    :param code_type: One of 'alpha_2', 'alpha_3', or 'numeric'; the
      desired identifier type to generate
    """

    # @TODO: Potentially do some minor restructuring around this logic
    # to make it shorter/clearer. A private helper was discussed, but
    # prevailing consensus was that this logic is a guiding nice-to-have
    # here, where it is, so we'll likely keep it. But this todo marks
    # a revisit later around whether the logic can be restructuerd.

    # First, identify what country the input is referencing
    standard = None
    raw_country = raw_country.strip().upper()
    if len(raw_country) == 2:
        standard = pycountry.countries.get(alpha_2=raw_country)
    elif len(raw_country) == 3:
        standard = pycountry.countries.get(alpha_3=raw_country)
        if standard is None:
            standard = pycountry.countries.get(numeric=raw_country)
    elif len(raw_country) >= 4:
        standard = pycountry.countries.get(name=raw_country)
        if standard is None:
            standard = pycountry.countries.get(official_name=raw_country)

    # Then, if we figured that out, convert it to desired form
    if standard is not None:
        if code_type == "alpha_2":
            standard = standard.alpha_2
        elif code_type == "alpha_3":
            standard = standard.alpha_3
        elif code_type == "numeric":
            standard = standard.numeric

    return standard


def standardize_phone(
    raw_phone: Union[str, List[str]], countries: List = [None, "US"]
) -> Union[str, List[str]]:
    """
    Given one or more phone numbers, and optionally a list of countries
    associated with those phone numbers, parse each phone number and
    generate its standardized ISO E.164 international format. If an
    input phone number can't be parsed, that number will return the
    empty string. The function attempts to parse the inputs using
    the first successful strategy out of the following:

    1. parse the phone number on its own
    2. parse the phone number using the provided list of possible
       associated countries
    3. parse the phone number using the US as country

    :param raw_phone: One or more raw phone number(s) to standardize
    :param countries: An optional list containing 2 letter ISO codes
      associated with the phone numbers, signifying to which countries
      the phone numbers might belong
    :return: Either a string representing the cleaned phone numbers,
      or a list of strings of cleaned numbers; if one phone number in
      the input list couldn't be standardized, the index in the returned
      list for that phone number will be the empty string
    """

    # Base cases: we always want to try the phone # on its own first;
    # we also want to try the phone # with the US if all else fails
    if None not in countries:
        countries.insert(0, None)
    if "US" not in countries:
        countries.append("US")

    phones_to_clean = raw_phone
    if isinstance(raw_phone, str):
        phones_to_clean = [raw_phone]
    outputs = []

    for phone in phones_to_clean:
        standardized = ""
        for country in countries:

            # We were able to pull the phone # and corresponding country
            try:
                standardized = phonenumbers.parse(phone, country)
                break

            # This combo of given phone # and country isn't valid
            except phonenumbers.phonenumberutil.NumberParseException:
                continue

        # If we got a match, format it according to ISO standards
        if standardized != "" and phonenumbers.is_possible_number(standardized):
            standardized = str(
                phonenumbers.format_number(
                    standardized, phonenumbers.PhoneNumberFormat.E164
                )
            )
            outputs.append(standardized)
        else:
            outputs.append("")

    if isinstance(raw_phone, str):
        return outputs[0]
    return outputs


def standardize_name(
    raw_name: Union[str, List[str]],
    trim: bool = True,
    case: Literal["upper", "lower", "title"] = "upper",
    remove_numbers: bool = True,
) -> Union[str, List[str]]:
    """
    Given one or more names, perform some basic standardization on each
    of them. All given input strings have punctuation characters removed,
    and then a variety of additional cleaning operations can be toggled
    on or off using the relevant parameter. The options include:

    - trim: stripping leading and trailing whitespace
    - remove_numbers: remove all numeric characters from the input
    - case: enforce the name to follow a specific casing convention

    All options specified will be applied uniformly to each input name,
    i.e. specifying case = "lower" will make all given names lower case.

    :param raw_name: Either a single string name or a list of strings,
      each representing a name
    :param trim: Whether to strip leading/trailing whitespace
    :param case: What case to enforce on each name; the default is to
      convert all inputs to upper case
    :remove_numbers: Whether to remove numeric characters from the inputs
    :return: Either a string or a list of strings, depending on the
      input of raw_name, holding the cleaned name(s)

    """
    names_to_clean = raw_name
    if isinstance(raw_name, str):
        names_to_clean = [raw_name]
    outputs = []

    for name in names_to_clean:
        # Remove all punctuation
        cleaned_name = "".join([ltr for ltr in name if ltr.isalnum() or ltr == " "])
        if remove_numbers:
            cleaned_name = "".join([ltr for ltr in cleaned_name if not ltr.isnumeric()])
        if trim:
            cleaned_name = cleaned_name.strip()
        if case == "upper":
            cleaned_name = cleaned_name.upper()
        if case == "lower":
            cleaned_name = cleaned_name.lower()
        if case == "title":
            cleaned_name = cleaned_name.title()
        outputs.append(cleaned_name)

    if isinstance(raw_name, str):
        return outputs[0]
    return outputs