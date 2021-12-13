import json, os, pickle, requests, shelve, sys, time

#############################################################################
#                                                                           #
# API calls to obtain taxonomic information. Used in case of name changes.  #
#                                                                           #
# See documention at https://api.inaturalist.org/v1/docs/#/Taxa             #
#                                                                           #
# We throttle the number of calls to less than 60 per minute. We also       #
# implement a cache to avoid repeated lookups of the same taxa across runs. #
# Cache entries include time stamps and they expire after two weeks.        #
#                                                                           #
#############################################################################

API_HOST                 = "https://api.inaturalist.org/v1"
CACHE_EXPIRATION         = 14 * 24 * 3600  # cache expires after 2 weeks
TOO_MANY_API_CALLS_DELAY = 60              # wait this long after error 429

# The cache stores the json responses.

if sys.platform == 'win32':
    DATA_DIR  = os.path.join(os.path.expanduser('~'),
                             'AppData', 'Local', 'inat_api')
else:
    DATA_DIR  = os.path.join(os.path.expanduser('~'), '.cache', 'inat_api')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

cache = shelve.open(os.path.join(DATA_DIR, 'api.cache'))

# API call throttling.

class Throttle:

    API_MAX_CALLS = 60   # max 60 calls per minute
    API_INTERVAL  = 60   # 1 minute

    def __init__(self):
        self.callTimes = []   # times of api calls

    # wait if necessary to avoid more than API_MAX_CALLS in API_INTERVAL
    def wait(self):
        while len(self.callTimes) >= self.API_MAX_CALLS:
            waitTime = self.callTimes[0] - (time.time() - self.API_INTERVAL)
            if waitTime > 0:
                print('Throttling API calls, '
                      f'sleeping for {waitTime:.1f} seconds.')
                time.sleep(waitTime)
                continue
            self.callTimes = self.callTimes[1:]
        self.callTimes.append(time.time())

api_call_throttle = Throttle()

# argument is an id or a list of id's
def get_taxa_by_id(id):
    if type(id) is list:
        url = API_HOST + '/taxa/' + '%2C'.join([str(i) for i in id])
    else:
        url = API_HOST + f'/taxa/{id}'
    tim = time.time()
    if not url in cache or cache[url][0] < tim - CACHE_EXPIRATION:
        delay = TOO_MANY_API_CALLS_DELAY
        headers = {'Content-type' : 'application/json' }
        while True:
            api_call_throttle.wait()
            response = requests.get(url, headers=headers)
            if response.status_code == requests.codes.too_many:
                time.sleep(delay)
                delay *= 2
            else:
                break
        if response.status_code == requests.codes.ok:
            cache[url] = (tim, response.json())
        else:
            print(response.text)
            return None
    return cache[url][1]

# returns taxa by name
def get_taxa(params):
    url = API_HOST + '/taxa'
    for key, val in params.items():
        if type(val) == bool:
            params[key] = 'true' if val else 'false'
    key = pickle.dumps((url, params)).hex()
    tim = time.time()
    if not key in cache or cache[key][0] < tim - CACHE_EXPIRATION:
        delay = TOO_MANY_API_CALLS_DELAY
        headers = {'Content-type' : 'application/json' }
        while True:
            api_call_throttle.wait()
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == requests.codes.too_many:
                time.sleep(delay)
                delay *= 2
            else:
                break
        if response.status_code == requests.codes.ok:
            cache[key] = (tim, response.json())
        else:
            print(response.text)
            return None
    return cache[key][1]


if __name__ == '__main__':

    assert not 'Not a top-level Python module!'
