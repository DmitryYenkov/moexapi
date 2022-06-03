import json
import urllib
from http.cookiejar import CookieJar
import pandas as pd
from datetime import datetime
from datetime import timedelta
from tabulate import tabulate


class Error(Exception):
    """Base class for other exceptions"""
    pass


class MOEXConnectionError(Error):
    pass


class CookieNotFoundError(Error):
    pass


class Config:
    def __init__(self, user='', password='', proxy_url=''):
        """ user: username in MOEX Passport to access real-time data and history
            password: password for this user
            proxy_url: proxy URL if any is used, specified as http://proxy:port
        """
        self.proxy_url = proxy_url
        self.user = user
        self.password = password
        self.auth_url = "https://passport.moex.com/login"


class MicexAuth:

    def __init__(self, config):
        self.config = config
        self.cookie_jar = CookieJar()
        self.passport = None
        self.auth()

    def auth(self):
        if self.config.proxy_url:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': self.config.proxy_url}),
                                                 urllib.request.HTTPCookieProcessor(self.cookie_jar),
                                                 urllib.request.HTTPHandler(debuglevel=0))
        else:
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar),
                                                 urllib.request.HTTPHandler(debuglevel=0))
        opener.addheaders = [('Authorization',
                              'Basic %s' % (self.config.user + ':' + self.config.password)[:-1])]
        opener.open(self.config.auth_url)

        # we only need a cookie with MOEX Passport (certificate)
        self.passport = None
        for cookie in self.cookie_jar:
            if cookie.name == '_passport_session':
                self.passport = cookie
                break
        else:
            raise CookieNotFoundError

    def is_real_time(self):
        if not self.passport or (self.passport and self.passport.is_expired()):
            self.auth()
        if self.passport and not self.passport.is_expired():
            return True
        return False


class MicexISSClient:

    def __init__(self, user='user', password='password', proxy=''):
        """ Create opener for a connection with authorization cookie.
            It's not possible to reuse the opener used to authenticate because
            there's no method in opener to remove auth data.
            config: instance of the Config class with configuration options
            auth: instance of the MicexAuth class with authentication info
            handler: user's handler class inherited from MicexISSDataHandler
            containet: user's container class
        """
        self.config = Config(user=user, password=password, proxy_url=proxy)
        self.auth = MicexAuth(self.config)

        if self.config.proxy_url:
            self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': self.config.proxy_url}),
                                                      urllib.request.HTTPCookieProcessor(self.auth.cookie_jar),
                                                      urllib.request.HTTPHandler(debuglevel=0))
        else:
            self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.auth.cookie_jar),
                                                      urllib.request.HTTPHandler(debuglevel=0))
        urllib.request.install_opener(self.opener)

        if not self.auth.is_real_time():
            raise MOEXConnectionError

    @staticmethod
    def get_index():
        """
        http://iss.moex.com/iss/reference/28
        """
        index_url = 'http://iss.moex.com/iss/index.json?iss.meta=off'
        response = urllib.request.urlopen(index_url)
        moex_index = json.loads(response.read())
        index_dict = {}
        for key in moex_index.keys():
            index_dict[key] = pd.DataFrame(data=moex_index[key]['data'], columns=moex_index[key]['columns'])
        return index_dict

    @staticmethod
    def get_securities_list():
        """
        http://iss.moex.com/iss/reference/5
        """
        y = input('Over 340k records! May take a long time. Do you really want to continue? Press (y)')
        if y != 'y':
            return None
        securities_url = 'https://iss.moex.com/iss/securities.json'
        start = 0
        results = []
        while True:
            print(start, end=',')
            response = urllib.request.urlopen(securities_url + '?start=' + str(start))
            securities = json.loads(response.read())
            securities = securities['securities']
            data = securities['data']
            cols = securities['columns']
            results.extend(data)
            start += len(data)
            if not len(data):
                break
        results = pd.DataFrame(results, columns=cols)
        return results

    def get_history_listing(self, engine='stock', market='shares', board='TQBR'):
        """
        http://iss.moex.com/iss/reference/119
        """
        url = (
            f'http://iss.moex.com/iss/history/'
            f'engines/{engine}/markets/{market}/boards/{board}/'
            f'listing.json'
        )
        # always remember about the 'start' argument to get long replies
        start = 0
        results = []
        while True:
            res = json.load(self.opener.open(url + '?start=' + str(start)))
            history = res['securities']
            data = history['data']
            cols = history['columns']
            results.extend(data)
            start += len(data)
            if not len(data):
                break
        df = pd.DataFrame(results, columns=cols)
        return df

    @staticmethod
    def get_security_description(security='IMOEX'):
        """
        http://iss.moex.com/iss/reference/13
        """
        security_desc_url = f'https://iss.moex.com/iss/securities/{security}.json'
        response = urllib.request.urlopen(security_desc_url)
        security_desc = json.loads(response.read())
        df = pd.DataFrame(data=security_desc['description']['data'],
                          columns=security_desc['description']['columns'])
        return df

    def get_correlations(self, engine='stock', market='shares', date=None):
        """
        http://iss.moex.com/iss/reference/172
        """
        url = (
            f'http://iss.moex.com/iss/statistics/'
            f'engines/{engine}/markets/{market}/'
            f'correlations.json'
        )
        # always remember about the 'start' argument to get long replies
        start = 0
        results = []
        while True:
            if date is None:
                date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            full_url = url + '?start=' + str(start) + '&date=' + date
            res = json.load(self.opener.open(full_url))
            statistics = res['coefficients']
            data = statistics['data']
            cols = statistics['columns']
            results.extend(data)
            start += len(data)
            if not len(data):
                break
        df = pd.DataFrame(results, columns=cols)
        return df

    @staticmethod
    def get_splits():
        """
        http://iss.moex.com/iss/reference/758
        """
        splits_url = 'http://iss.moex.com/iss/statistics/engines/stock/splits.json'
        response = urllib.request.urlopen(splits_url)
        splits = json.loads(response.read())
        df = pd.DataFrame(data=splits['splits']['data'],
                          columns=splits['splits']['columns'])
        return df

    def get_deviationcoeffs(self, engine='stock', date=None):
        """
        http://iss.moex.com/iss/reference/134
        """
        url = (
            f'http://iss.moex.com/iss/statistics/'
            f'engines/{engine}/'
            f'deviationcoeffs.json'
        )
        # always remember about the 'start' argument to get long replies
        start = 0
        results = []
        while True:
            if date is None:
                date = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            full_url = url + '?start=' + str(start) + '&date=' + date
            res = json.load(self.opener.open(full_url))
            deviationcoeffs = res['securities']
            data = deviationcoeffs['data']
            data = [d for d in data if d[-6:] != [0] * 6]
            cols = deviationcoeffs['columns']
            results.extend(data)
            start += len(data)
            if not len(data):
                break
        df = pd.DataFrame(results, columns=cols)
        return df

    def get_share_hist(self, security, start_date=None, end_date=None,
                       engine='stock', market='shares', board='TQBR'):
        """
        http://iss.moex.com/iss/reference/65
        """
        url = (
            f'http://iss.moex.com/iss/history/engines/'
            f'{engine}/markets/{market}/boards/{board}/securities/{security}.json'
        )
        # always remember about the 'start' argument to get long replies
        start = 0
        results = []
        while True:
            full_url = url + '?start=' + str(start)
            if start_date is not None:
                full_url += f'&from={start_date}'
            if end_date is not None:
                full_url += f'&till={end_date}'
            res = json.load(self.opener.open(full_url))
            history = res['history']
            data = history['data']
            cols = history['columns']
            results.extend(data)
            start += len(data)
            if not len(data):
                break
        df = pd.DataFrame(results, columns=cols)
        return df

    def get_board_hist_date(self, date, engine='stock', market='shares', board='TQBR'):
        """
        http://iss.moex.com/iss/reference/64
        """
        url = (
            f'http://iss.moex.com/iss/history/engines/'
            f'{engine}/markets/{market}/boards/{board}/securities.json'
        )
        # always remember about the 'start' argument to get long replies
        start = 0
        results = []
        while True:
            full_url = url + '?start=' + str(start) + '&date=' + date
            res = json.load(self.opener.open(full_url))
            history = res['history']
            data = history['data']
            cols = history['columns']
            results.extend(data)
            start += len(data)
            if not len(data):
                break
        df = pd.DataFrame(results, columns=cols)
        return df


if __name__ == '__main__':
    iss = MicexISSClient()
    index_dataframes = iss.get_index()
    for dfkey in index_dataframes.keys():
        print('===============\n', dfkey.upper(), '\n')
        print(index_dataframes[dfkey].columns.to_list())
        print(tabulate(index_dataframes[dfkey]))
