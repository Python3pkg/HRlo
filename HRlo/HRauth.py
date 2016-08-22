#!/usr/bin/env python3
import re
import os
import sys
import requests

import getpass
import base64

try:
   from configparser import SafeConfigParser
except:
   from ConfigParser import SafeConfigParser

HRauth_default = {
    'config_file' : os.path.join( os.path.expanduser("~"), '.HRlo'),
    'password_encoding' : 'base64',
    'remove_config_file' : False,
    'save' : False,
    'required' : ['host', 'username', 'idemploy'],
}

class HRauth(dict):

   HRauth_config_option = 'HRauth'

   def __init__(self, **kwargs):

      dict.__init__(self, **HRauth_default)
      # update with arguments
      self.update(kwargs)

      if self['remove_config_file']:
          self._remove_config_file()

      # read from config_file
      self.update( self._read_config_file(kwargs['config_file']) )
      # read from args
      self.update( {k: kwargs[k] for k in self['required'] if kwargs.get(k, None)} )

      self._check_required()

      self._get_password()

      if self['save']:
          if self.login():
              self._write_config_file(self['config_file'])


   def _get_password(self):

      if self.get('password', False):
         self['password'] = self._password_decode()
      else:
         self['password'] = getpass.getpass()


   def _password_decode(self):
      """Decode password"""

      _enc  = self['password_encoding']
      _pass = self['password']

      if   _enc == 'clear':
         _pass = _pass
      elif _enc == 'base64':
         _pass = base64.b64decode(_pass)

      return _pass


   def _password_encode(self):
      """Encode password"""

      _enc  = self['password_encoding']
      _pass = self['password']


      if   _enc == 'clear':
         _pass = self['password']
      elif _enc == 'base64':
         if isinstance(_pass, bytes):
            _pass = base64.b64encode(_pass)
         else:
            _pass = base64.b64encode(_pass.encode('ascii'))

      if isinstance(_pass, bytes):
          _pass = _pass.decode()

      return _pass


   def _check_required(self):
      missing = []
      for k in self['required']:
         if not self.get(k, False):
            missing.append(k)
      if missing:
         raise Exception("[HRauth] *** ERROR *** missing required args: {}".format( ", ".join(missing) ))


   def _read_config_file(self, fname):
      """Read from config file"""

      if not os.path.isfile(fname):
         return {}

      parser = SafeConfigParser()
      parser.read(fname)

      return {k: parser.get(self.HRauth_config_option, k) for k in parser.options(self.HRauth_config_option)}


   def _write_config_file(self, fname):
       parser = SafeConfigParser()

       parser.add_section(self.HRauth_config_option)

       if self.get('host', None):
          parser.set(self.HRauth_config_option, 'host', self['host'])
       if self.get('username', None):
          parser.set(self.HRauth_config_option, 'username', self['username'])
       if self.get('idemploy', None):
          parser.set(self.HRauth_config_option, 'idemploy', str(self['idemploy']))

       if self['save_password']:
          _encoded = self._password_encode()
          parser.set(self.HRauth_config_option, 'password', _encoded)

       with open(fname, "w") as f:
          parser.write(f)


   def _remove_config_file(self):
       if os.path.isfile(self['config_file']):
         print("Removing config file :", self['config_file'])
         os.remove(self['config_file'])


   def login(self):

       auth = {'m_cUserName' : self['username'], 'm_cPassword' : self['password'], 'm_cAction' : 'login'}

       _login_url  = 'https://' + self['host'] + '/HRPortal/servlet/cp_login'

       _session = requests.Session()

       r = _session.post(_login_url, params=auth, allow_redirects=False)

       try:
          if 'jsp/home.jsp' in r.headers['location']:
             return True
       except:
          raise Exception("[HRauth] *** ERROR *** on HR authentication!")


   def host(self):
      return self['host']

   def username(self):
      return self['username']

   def idemploy(self):
      return self['idemploy']

   def password(self):
      return self['password']



def add_parser(parser):

   authparser = parser.add_argument_group('authentication options')

   authparser.add_argument('-u', '--username',
                           help='Username')

   authparser.add_argument('-i', '--idemploy',
                           help='ID employee')

   authparser.add_argument('-a', '--url',
                           dest='host',
                           help='HR url')

   authparser.add_argument('-c', '--config-file',
                           default=HRauth_default['config_file'],
                           help='Configuration file (default %(default)s)')

   authparser.add_argument('-s', '--save',
                           action='store_true',
                           help='Save HR authentication options in HRauth config file')

   authparser.add_argument('--save-password',
                           action='store_true',
                           help='Save HR authentication password in HRauth config file')

   authparser.add_argument('--password-encoding',
                           choices=['clear', 'base64'],
                           default=HRauth_default['password_encoding'],
                           help='Password encoding (default %(default)s)')

   authparser.add_argument('--remove-config-file',
                           action='store_true',
                           help='Remove HR config file')

   args = parser.parse_args()


def main ():

   import argparse

   parser = argparse.ArgumentParser(prog='HRauth',
                                    description='Module to authenticate on HR.',
                                    formatter_class=argparse.RawTextHelpFormatter)
   add_parser(parser)

   args = parser.parse_args()

   auth = HRauth(**vars(args))

   if auth.login():
       print("Successfully login with user: {}".format(auth.username()))


if __name__ == '__main__':
    main()
