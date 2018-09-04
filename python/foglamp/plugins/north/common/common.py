# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Common code to the north facing plugins"""

__author__ = "Stefano Simonelli"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"


def convert_to_type(value):
    """Evaluates and converts to the type in relation to its actual value, for example "180.2" to float 180.2

          Args:
             value : value to evaluate and convert
          Returns:
              value_converted: converted value
          Raises:
    """
    value_type = evaluate_type(value)
    if value_type == "string":
        value_converted = value
    elif value_type == "number":
        value_converted = float(value)
    elif value_type == "integer":
        value_converted = int(value)
    else:
        value_converted = value
    return value_converted


def evaluate_type(value):
    """Evaluates the type in relation to its value

          Args:
             value : value to evaluate
          Returns:
              Evaluated type {integer,number,string}
          Raises:
    """
    try:
        float(value)
        try:
            # Evaluates if it is a int or a number
            if str(int(float(value))) == str(value):
                # Checks the case having .0 as 967.0
                int_str = str(int(float(value)))
                value_str = str(value)
                if int_str == value_str:
                    evaluated_type = "integer"
                else:
                    evaluated_type = "number"
            else:
                evaluated_type = "number"
        except ValueError:
            evaluated_type = "string"
    except ValueError:
        evaluated_type = "string"
    return evaluated_type


def identify_unique_asset_codes(raw_data):
    """Identify unique asset codes in the data block

         Args:
             raw_data : data block retrieved from the Storage layer that should be evaluated
         Returns:
             unique_asset_codes : list of unique codes

         Raises:
    """
    unique_asset_codes = []
    for row in raw_data:
        asset_code = row['asset_code']
        asset_data = row['reading']
        # Evaluates if the asset_code is already in the list
        if not any(item["asset_code"] == asset_code for item in unique_asset_codes):
            unique_asset_codes.append(
                {
                    "asset_code": asset_code,
                    "asset_data": asset_data
                }
            )
    return unique_asset_codes
