import requests,json
import logging
from datetime import datetime,timedelta
import copy
from common_utilities import get_location_details
import pandas as pd
from pymemcache.client.hash import HashClient
from pymemcache.client.base import Client
from pymemcache import fallback
from fake_useragent import UserAgent
from random import randint
LOG = logging.getLogger('Cowin_App')


class COWIN(object):
    """
    Information about memcached:=
    https://commaster.net/posts/installing-memcached-windows/
    Type the command “c:\memcached\memcached.exe -d start” to start the service
    Type the command “c:\memcached\memcached.exe -d stop” to stop the service
    To change the memory pool size, type “c:\memcached\memcached.exe -m 512” for 512MB
    """

    def __init__(self):
        self.current_user_location = get_location_details()
        #TODO:For testing
        #self.current_user_location = {'state': 'Maharashtra', 'district': 'Thane', 'city': 'Ambernath'}
        self.hdr = {'Content-Type': 'application/json','Accept': 'application/json','User-Agent':UserAgent().random}
        self.base_url = {'generate_otp':'https://cdn-api.co-vin.in/api/v2/auth/public/generateOTP',
                         'find_by_pincode':'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByPin',
                         'get_india_states':'https://cdn-api.co-vin.in/api/v2/admin/location/states',
                         'get_all_dist_by_states':'https://cdn-api.co-vin.in/api/v2/admin/location/districts',
                         'find_by_district':'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict'
                        }

        #self.client = HashClient(['127.0.0.1:11211','127.0.0.1:11212',])
        self.client = Client('127.0.0.1:11211')

    def extract_data_from_memached(self,key,data):
        LOG.info('store_data_in_memached for {0}'.format(key))
        if self.client.get(key) is None:
            self.client.set(key,data,expire=600)
        result = json.loads(self.client.get(key).decode().replace("'",'"')) #str(self.client.get(key),'utf-8')
        LOG.debug(result)
        data_key = list(data.keys())[0]
        return result.get(data_key)

    def extract_data_from_api(self,input_date='01-06-2021',user_pincode=None):
        LOG.info('extract_data_from_api')
        if user_pincode is not None and len(user_pincode) == 6:
            session_data = self.find_session_by_pincode(pincode=user_pincode,session_date=input_date)
        else:
            state_num = self.get_all_india_states()
            district_num = self.get_all_dist_by_states(state_code=state_num)
            session_data = self.find_session_by_district(district=district_num,session_date=input_date)
            if isinstance(session_data,pd.DataFrame):
                session_data = session_data.drop(['center_id','from','to','lat','long','session_id','available_capacity','slots'],axis=1)
        self.flush_memcached_data()
        return session_data

    def flush_memcached_data(self):
        LOG.info('flush_memcached_data')
        self.client.flush_all()
        self.client.close()
        print(self.client.close())

    def generate_otp_token(self):
        LOG.info('generate_otp_token')
        url_for_otp = self.base_url['generate_otp']
        mobile_number= randint(10**(10-1), (10**10)-1)
        try:
            r = requests.post(url_for_otp,json={"mobile":mobile_number},headers=self.hdr) # dummy mobile number to generate txn ID = 9876543210
            if r.ok:
                LOG.debug(r.text)
                return json.loads(r.text)
            else:
                print(r.status_code)
                return r.text
        except requests.exceptions.HTTPError as httpErr:
            print("Http Error:",httpErr)
            return httpErr
        except requests.exceptions.ConnectionError as connErr:
            print("Error Connecting:",connErr)
            return connErr
        except requests.exceptions.Timeout as timeOutErr:
            print("Timeout Error:",timeOutErr)
            return timeOutErr
        except requests.exceptions.RequestException as reqErr:
            print("Something Else:",reqErr)
            return reqErr

    def authorize_api(self):
        LOG.info('authorize_api')
        otp_token = self.generate_otp_token()
        if not isinstance(otp_token,dict):
            return None
        auth_token = otp_token['txnId']
        LOG.debug('otp_token=, {0}'.format(otp_token))
        #self.hdr.update({'Authorization': 'Bearer ' + auth_token})
        #self.extract_data_from_memached('authorize_api', {'Authorization':{'Authorization': 'Bearer ' + auth_token}})
        return {'Authorization': 'Bearer ' + auth_token}

    def get_all_india_states(self):
        LOG.info('get_all_india_states')
        auth_token = self.authorize_api()
        header = copy.deepcopy(self.hdr)
        header.update(auth_token)
        #print('header=, {0}'.format(header))
        url = self.base_url['get_india_states']

        try:
            r = requests.get(url,headers=header)
            if r.ok:
                LOG.debug(r.text)
                data = json.loads(r.text)

                self.client.set('list_of_states',data,expire=600)
                results = self.extract_data_from_memached('list_of_states',data)
                df = result_df = pd.DataFrame(results)
                LOG.debug(result_df)
                filter_df = df[df.state_name == self.current_user_location['state']]

                return filter_df.iloc[0]['state_id']
            else:
                print(r.status_code)
                return r.text
        except requests.exceptions.HTTPError as httpErr:
            print("Http Error:",httpErr)
            return httpErr
        except requests.exceptions.ConnectionError as connErr:
            print("Error Connecting:",connErr)
            return connErr
        except requests.exceptions.Timeout as timeOutErr:
            print("Timeout Error:",timeOutErr)
            return timeOutErr
        except requests.exceptions.RequestException as reqErr:
            print("Something Else:",reqErr)
            return reqErr

    def get_all_dist_by_states(self,state_code='21'):
        LOG.info('get_all_dist_by_states')
        auth_token = self.authorize_api()
        header = copy.deepcopy(self.hdr)
        header.update(auth_token)

        url = self.base_url['get_all_dist_by_states'] + '/'+str(state_code)

        try:
            r = requests.get(url, headers=header)
            if r.ok:
                LOG.debug(r.text)
                data = json.loads(r.text)

                self.client.set('list_of_districts',data,expire=600)
                results = self.extract_data_from_memached('list_of_districts',data)
                df = result_df = pd.DataFrame(results)
                LOG.debug(result_df)
                filter_df = df[df.district_name == self.current_user_location['district']]

                return filter_df.iloc[0]['district_id']
            else:
                print(r.status_code)
                return r.text
        except requests.exceptions.HTTPError as httpErr:
            print("Http Error:",httpErr)
            return httpErr
        except requests.exceptions.ConnectionError as connErr:
            print("Error Connecting:",connErr)
            return connErr
        except requests.exceptions.Timeout as timeOutErr:
            print("Timeout Error:",timeOutErr)
            return timeOutErr
        except requests.exceptions.RequestException as reqErr:
            print("Something Else:",reqErr)
            return reqErr

    def find_session_by_district(self,district='392',session_date=(datetime.today()+timedelta(days=1)).strftime('%d-%m-%Y')):
        LOG.info('find_session_by_district')

        auth_token = self.authorize_api()
        header = copy.deepcopy(self.hdr)
        header.update(auth_token)
        LOG.debug('header=, {0}'.format(header))
        url = self.base_url['find_by_district']
        params = {'Accept-Language': 'hi_IN','district_id':district,'date':session_date}

        try:
            r = requests.get(url, params=params,headers=header)
            if r.ok:
                LOG.debug(r.text)
                data= json.loads(r.text)
                df = pd.DataFrame(data['sessions']) if data['sessions'] else 'No Sessions available right now for given location'
                if isinstance(df,pd.DataFrame):

                    filter_df = df.loc[df.block_name == self.current_user_location['city']]
                    print('filter_df By City =\n ',filter_df)
                    return filter_df if not filter_df.empty else 'No Sessions available right now for given location'
                return df
            else:
                LOG.debug('status_code = '.format(r.status_code))
                return r.text
        except requests.exceptions.HTTPError as httpErr:
            print("Http Error:",httpErr)
            return httpErr
        except requests.exceptions.ConnectionError as connErr:
            print("Error Connecting:",connErr)
            return connErr
        except requests.exceptions.Timeout as timeOutErr:
            print("Timeout Error:",timeOutErr)
            return timeOutErr
        except requests.exceptions.RequestException as reqErr:
            print("Something Else:",reqErr)
            return reqErr

    def find_session_by_pincode(self,pincode='421501',session_date=(datetime.today()+timedelta(days=1)).strftime('%d-%m-%Y')):
        LOG.info('find_session_by_pincode')

        auth_token = self.authorize_api()
        header = copy.deepcopy(self.hdr)
        header.update(auth_token)
        #print('header=, {0}'.format(header))
        url = self.base_url['find_by_pincode']
        params = {'Accept-Language': 'hi_IN','pincode':pincode,'date': session_date}

        try:
            r = requests.get(url, params=params,headers=header)
            if r.ok:
                LOG.debug(r.text)
                data= json.loads(r.text)
                df = pd.DataFrame(data['sessions']) if data['sessions'] else 'No Sessions available right now for given location'
                return df
            else:
                print(r.status_code)
                return r.text
        except requests.exceptions.HTTPError as httpErr:
            print("Http Error:",httpErr)
            return httpErr
        except requests.exceptions.ConnectionError as connErr:
            print("Error Connecting:",connErr)
            return connErr
        except requests.exceptions.Timeout as timeOutErr:
            print("Timeout Error:",timeOutErr)
            return timeOutErr
        except requests.exceptions.RequestException as reqErr:
            print("Something Else:",reqErr)
            return reqErr

if __name__ == '__main__':
    """ 
    #session_data = COWIN().find_session_by_pincode()
    state_num = COWIN().get_all_india_states()
    print('state_num = ',state_num)
    #Dist code thane- 392 & Mumbai-395
    district_num = COWIN().get_all_dist_by_states(state_code=state_num)
    print('district_num =',district_num)
    """
    session_data = COWIN().extract_data_from_api(input_date='05-06-2021',user_pincode=None)
    print(session_data)