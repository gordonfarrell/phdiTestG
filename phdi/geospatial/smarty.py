from typing import List, Union
from smartystreets_python_sdk import StaticCredentials, ClientBuilder
from smartystreets_python_sdk import us_street
from smartystreets_python_sdk.us_street.lookup import Lookup

from phdi.geospatial.core import BaseGeocodeClient, GeocodeResult


class SmartyGeocodeClient(BaseGeocodeClient):
    """
    Implementation of a geocoding client using the SmartyStreets API.
    Requires an authorization ID as well as an authentication token
    in order to build a street lookup client.
    """

    def __init__(
        self, auth_id: str, auth_token: str, licenses: List[str] = ["us-standard-cloud"]
    ):
        self.auth_id = auth_id
        self.auth_token = auth_token
        creds = StaticCredentials(auth_id, auth_token)
        self.__client = (
            ClientBuilder(creds).with_licenses(licenses).build_us_street_api_client()
        )

    @property
    def client(self) -> us_street.Client:
        """
        This property:
          1. defines a private instance variable __client
          2. makes it accessible through the use of .client()

        This property holds a SmartyStreets-specific connection client
        allows a user to geocode without directly referencing the
        underlying vendor service client.
        """
        return self.__client

    def geocode_from_str(self, address: str) -> Union[GeocodeResult, None]:
        """
        Geocodes a string-formatted address using SmartyStreets. If the result
        comes back valid, output is stored in a GeocodeResult object. If the
        result could not be latitude- or longitude-located, then Smarty failed
        to precisely geocode the address, so no result is returned. Raises
        an error if the provided address is empty.

        :param address: The address to geocode, given as a string.
        :raises ValueError: If address does not include street number and name.
        :return: A standardized address enriched with lat, lon, and more. Returns None
            if no valid result.
        """

        # The smarty Lookup class will parse a BadRequestError but retry
        # 5 times if the lookup address is blank, so catch that here
        if address == "":
            raise ValueError("Address must include street number and name at a minimum")

        lookup = Lookup(street=address)
        self.__client.send_lookup(lookup)
        return self._parse_smarty_result(lookup)

    def geocode_from_dict(self, address: dict) -> Union[GeocodeResult, None]:
        """
        Geocodes a dictionary-formatted address using SmartyStreets.
        If a result is found, encodes as a GeocodeResult object and
        return, otherwise the return None.

        :param address: A dictionary with fields outlined above.
        :raises ValueError: If address does not include street number and name.
        :return: A standardized address enriched with lat, lon, and more. Returns None
            if no valid result.
        """

        # Smarty geocode requests must include a street level
        # field in the payload, otherwise generates BadRequestError
        if address.get("street", "") == "":
            raise ValueError("Address must include street number and name at a minimum")

        # Configure the lookup with whatever provided address values
        # were in the user-given dictionary
        lookup = Lookup()
        lookup.street = address.get("street", "")
        lookup.street2 = address.get("street2", "")
        lookup.secondary = address.get("apartment", "")
        lookup.city = address.get("city", "")
        lookup.state = address.get("state", "")
        lookup.zipcode = address.get("postal_code", "")
        lookup.urbanization = address.get("urbanization", "")
        lookup.match = "strict"

        self.__client.send_lookup(lookup)
        return self._parse_smarty_result(lookup)

    @staticmethod
    def _parse_smarty_result(lookup) -> Union[GeocodeResult, None]:
        """
        Private helper function to parse a returned Smarty geocoding result into
        our standardized GeocodeResult class. If the Smarty lookup is null or
        doesn't include latitude and longitude information, returns None
        instead.

        :param lookup: The us_street.lookup client instantiated for geocoding
        :return: A parsed and standardized address enriched with lat, lon, and more.
            Returns None if no valid result.
        """
        # Valid responses have results with lat/long
        if lookup.result and lookup.result[0].metadata.latitude:
            smartystreets_result = lookup.result[0]
            street_address = [smartystreets_result.delivery_line_1]
            if smartystreets_result.delivery_line_2:
                street_address.append(smartystreets_result.delivery_line_2)

            # Format the Smarty result into our standard dataclass object
            return GeocodeResult(
                line=street_address,
                city=smartystreets_result.components.city_name,
                state=smartystreets_result.components.state_abbreviation,
                postal_code=smartystreets_result.components.zipcode,
                county_fips=smartystreets_result.metadata.county_fips,
                county_name=smartystreets_result.metadata.county_name,
                lat=smartystreets_result.metadata.latitude,
                lng=smartystreets_result.metadata.longitude,
                precision=smartystreets_result.metadata.precision,
            )

        return
