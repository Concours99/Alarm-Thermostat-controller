# ecobee test
from wg_ecobee import authorize_app_with_ecobee
from wg_ecobee import ecobee_get_status
from wg_ecobee import TSTAT_SUCCESS
import json

if authorize_app_with_ecobee(True) == TSTAT_SUCCESS :
    data = ecobee_get_status(True)
    json_str = json.dumps(data, indent=4)
    print(json_str)