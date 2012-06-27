# -*- coding: utf-8 -*-

'''  
Common usage
============

- searching...

        >>> from bd_tunneler import BD_Tunneler
        >>> settings = {
        ...   u'BD_API_URL': u'the-url',
        ...   u'PATRON_BARCODE': u'the-barcode',
        ...   u'UNIVERSITY_CODE': u'the-university-code',
        ...   u'REQUESTED_ISBN': u'the-isbn',
        ...   u'COMMAND': u'search' } 
        >>> bd = BD_Tunneler( settings )  # at this point bd.found & bd.is_requestable are None
        >>> bd.search()
        >>> bd.found
        True  # or False
        >>> bd.is_requestable
        True  # or False

- requesting...

        >>> from bd_tunneler import BD_Tunneler
        >>> settings = {
        ...   u'BD_API_URL': u'the-url',
        ...   u'PATRON_BARCODE': u'the-barcode',
        ...   u'UNIVERSITY_CODE': u'the-university-code',
        ...   u'REQUESTED_ISBN': u'the-isbn',
        ...   u'COMMAND': u'request',
        ...   u'REQUEST_PICKUP_LOCATION': u'the-pickup-location' } 
        >>> bd = BD_Tunneler( settings )
        >>> bd.request()
        ## if requestable...
        >>> bd.request_transaction_num
        u'BRO-123'  # bd.found & bd.requestable would be True
        ## if not requestable...
        >>> bd.request_transaction_num
        u'not_applicable'  # bd.found could be True or False; bd.is_requestable would be False

Notes
=====

- see [project README] for additional info

[project README]: https://github.com/Brown-University-Library/borrowdirect_tunneler#readme
'''


import datetime, imp, json, pprint, sys, time
import requests
from types import ModuleType, NoneType


class BD_Tunneler(object):
  
  
  def __init__( self, settings=None  ):
    '''
    - Allows a settings module to be passed in,
        or a settings path to be passed in,
        or a dictionary to be passed in.
    - Sets other attributes.
    - Attributes in caps are passed in; others are calculated.
    '''
    types = [ NoneType, dict, ModuleType, unicode ]
    assert type(settings) in types, Exception( u'Passing in settings is optional, but if used, must be either a dict, a unicode path to a settings module, or a module named settings; current type is: %s' % repr(type(settings)) )
    if isinstance(settings, dict):
      s = imp.new_module( u'settings' )
      for k, v in settings.items():
        setattr( s, k, v )
      settings = s
    elif isinstance(settings, ModuleType):
      pass
    elif isinstance(settings, unicode):  # path
      settings = imp.load_source( u'*', settings )
    ## general
    self.BD_API_URL = None if ( u'BD_API_URL' not in dir(settings) ) else settings.BD_API_URL
    self.BD_URL_AUTH_FORMAT = None if ( u'BD_URL_AUTH_FORMAT' not in dir(settings) ) else settings.BD_URL_AUTH_FORMAT  # login url
    self.COMMAND = u'search' if ( u'COMMAND' not in dir(settings) ) else settings.COMMAND  # u'search' or u'request'
    self.IDENTIFIER = None if ( u'IDENTIFIER' not in dir(settings) ) else settings.IDENTIFIER
    self.PATRON_BARCODE = None if ( u'PATRON_BARCODE' not in dir(settings) ) else settings.PATRON_BARCODE
    self.UNIVERSITY_CODE = None if ( u'UNIVERSITY_CODE' not in dir(settings) ) else settings.UNIVERSITY_CODE
    self.REQUESTED_ISBN = None if ( u'REQUESTED_ISBN' not in dir(settings) ) else settings.REQUESTED_ISBN
    self.log = [ u'- instantiated %s' % unicode(datetime.datetime.now())[0:10] ]
    self.cookies_recent = None  # dict with most recent cookie
    self.cookies_history = []
    ## login
    self.login_url = None
    self.login_history = None
    self.login_response = None
    self.logged_in_status = None  # may end up True or False
    ## isbn search ( ascertain a) if found & b) record-ids )
    self.initiate_search_url = None
    self.initiate_search_response = None
    self.initiate_search_status = None  # may end up True or False
    self.monitor_search_url = None
    self.MONITOR_SEARCH_INTERVAL = 2 if ( u'MONITOR_SEARCH_INTERVAL' not in dir(settings) ) else settings.MONITOR_SEARCH_INTERVAL
    self.MONITOR_SEARCH_TIMEOUT = 60 if ( u'MONITOR_SEARCH_TIMEOUT' not in dir(settings) ) else settings.MONITOR_SEARCH_TIMEOUT
    self.monitor_search_start_time = None
    self.monitor_search_end_time = None  # starttime + timeout
    self.monitor_search_time_taken = None
    self.monitor_search_responses = []
    self.monitor_search_recids_found = None
    self.found = None  # may end up True or False as result of monitor-search logic
    ## record-id search ( ascertain if requestable )
    self.check_records_current_record = None
    self.check_records_initiation_urls = []  # url same for record-check-monitoring
    self.check_records_initiation_responses = []
    self.CHECK_RECORDS_MONITOR_INTERVAL = 2 if ( u'RECORDS_CHECK_MONITOR_INTERVAL' not in dir(settings) ) else settings.RECORDS_CHECK_MONITOR_INTERVAL
    self.CHECK_RECORDS_MONITOR_TIMEOUT = 60 if ( u'RECORDS_CHECK_MONITOR_TIMEOUT' not in dir(settings) ) else settings.RECORDS_CHECK_MONITOR_TIMEOUT
    self.check_records_monitor_current_start_time = None
    self.check_records_monitor_current_end_time = None
    self.check_records_monitor_timetaken_results = []  # each: {u'entry_name': val, u'starttime': val, u'endtime': val, u'timetaken': val}
    self.check_records_monitor_responses = []
    self.check_records_evaluation_results = []
    self.is_requestable = None  # may end up True or False as result of check-records logic
    ## request
    self.request_url = None
    self.REQUEST_PICKUP_LOCATION = None if ( u'REQUEST_PICKUP_LOCATION' not in dir(settings) ) else settings.REQUEST_PICKUP_LOCATION  # required for request url
    self.request_response = None
    self.request_transaction_num = None
    return
    
    
  def login( self ):
    '''
    Purpose: To get and store authentication cookie info.
             Although response content is stored, it's not important.
       Note: BD_API_URL is inspected to determine if it's the production or development url,
             and the appropriate command parameter value is then set.
    '''
    assert len(self.BD_API_URL) > 0 and type(self.BD_API_URL) == unicode, Exception( u'self.BD_API_URL requires a unicode string; it is %s' % self.BD_API_URL )
    assert len(self.PATRON_BARCODE) > 0 and type(self.PATRON_BARCODE) == unicode, Exception( u'self.PATRON_BARCODE requires a unicode string; it is %s' % self.PATRON_BARCODE )
    assert len(self.UNIVERSITY_CODE) > 0 and type(self.UNIVERSITY_CODE) == unicode, Exception( u'self.UNIVERSITY_CODE requires a unicode string; it is %s' % self.UNIVERSITY_CODE )
    ## ascertain url type
    if u'borrow-direct' in self.BD_API_URL:  # production
      command_param_value = u'bdauth'
    elif u'bdtest' in self.BD_API_URL:  # development
      command_param_value = u'mkauth'
    else:
      raise Exception( u'unknown self.BD_API_URL' )
    ## build & send request
    payload = {
      u'command': command_param_value,
      u'LS': self.UNIVERSITY_CODE,
      u'PI': self.PATRON_BARCODE }
    r = requests.get( self.BD_API_URL, params=payload )
    self.login_url = r.history[0].url  # the initial assembled url before redirect
    self.cookies_recent = self.makeCookieDict( r )
    self.cookies_history.append( { u'login_new': self.cookies_recent } )
    self.login_history = r.history
    self.login_response = r.content.decode( u'utf-8', u'replace' )
    if u'JSESSIONID' in self.cookies_recent.keys():
      self.logged_in_status = True
    else:
      self.logged_in_status = False
    return
              
    
  def initiateIsbnSearch( self ):
    '''
    Purpose: starts BD search for ISBN.
    '''
    assert len(self.BD_API_URL) > 0 and type(self.BD_API_URL) == unicode, Exception( u'self.BD_API_URL requires a unicode string; it is %s' % self.BD_API_URL )
    assert len(self.REQUESTED_ISBN) > 0 and type(self.REQUESTED_ISBN) == unicode, Exception( u'self.REQUESTED_ISBN requires a unicode string; it is %s' % self.REQUESTED_ISBN )
    assert self.logged_in_status == True, Exception( u'self.logged_in_status must be True; it is: %s' % self.logged_in_status )
    payload = {
      u'command': u'search',
      u'query': u'isbn=%s' % self.REQUESTED_ISBN,
      u'torusquery': u'' }
    r = requests.get( self.BD_API_URL, cookies=self.cookies_recent, params=payload )
    self.initiate_search_url = r.url
    self.cookies_history.append( {u'initiate_isbn_search': self.cookies_recent} )
    self.initiate_search_history = r.history
    self.initiate_search_response = r.content.decode( u'utf-8', u'replace' )
    if u'<search><status>OK</status></search>' in self.initiate_search_response:
      self.initiate_search_status = True
    else:
      self.initiate_search_status = False
    return
    
    
  def monitorIsbnSearch( self, interval=None, timeout=None ):
    '''
    Purpose: monitors the isbn search every [interval] seconds for a maximum of [timeout] seconds,
             stores the results and updates the search status, and
             sets self.found, and if self.found is False, it sets self.is_requestable to False
    '''
    ## setup
    self.MONITOR_SEARCH_INTERVAL = self.MONITOR_SEARCH_INTERVAL if ( interval == None ) else interval
    self.MONITOR_SEARCH_TIMEOUT = self.MONITOR_SEARCH_TIMEOUT if ( timeout == None ) else timeout
    assert len(self.BD_API_URL) > 0 and type(self.BD_API_URL) == unicode, Exception( u'self.BD_API_URL requires a unicode string; it is %s' % self.BD_API_URL )
    assert self.initiate_search_status == True, Exception( u'self.initiate_search_status must be True; it is %s' % self.initiate_search_status )
    assert type(self.MONITOR_SEARCH_INTERVAL) == int, Exception( u'self.MONITOR_SEARCH_INTERVAL requires an int; the type is %s' % type(self.MONITOR_SEARCH_INTERVAL) )
    assert type(self.MONITOR_SEARCH_TIMEOUT) == int, Exception( u'self.MONITOR_SEARCH_TIMEOUT requires an int; the type is %s' % type(self.MONITOR_SEARCH_TIMEOUT) )
    if self.monitor_search_start_time == None:
      self.monitor_search_start_time = datetime.datetime.now()
      self.monitor_search_end_time = self.monitor_search_start_time + datetime.timedelta( seconds=self.MONITOR_SEARCH_TIMEOUT )
    payload = {
      u'command': u'show',
      u'start': u'0',
      u'num': u'20',
      u'sort': u'relevance',
      u'block': u'1',
      u'type': u'json', }
    ## start monitor requests
    while self.monitor_search_end_time > datetime.datetime.now():
      r = requests.get( self.BD_API_URL, cookies=self.cookies_recent, params=payload )
      if self.monitor_search_url == None:
        self.monitor_search_url = r.url
      self.cookies_recent = self.makeCookieDict(r)
      self.cookies_history.append( {u'monitor_isbn_search': self.cookies_recent} )
      json_string = r.content.decode( u'utf-8', u'replace' )
      self.monitor_search_responses.append( json_string )
      ## save any recid entries
      self.monitor_search_recids_found = self.updateRecordIdsFound( 
        self.monitor_search_responses[-1],  # the just-appended json response
        self.monitor_search_recids_found )
      ## sources done responding?
      if json.loads(json_string, strict=False)[u'activeclients'] == [u'0']:
        break
      else:
        time.sleep( self.MONITOR_SEARCH_INTERVAL )
    self.found = False if len(self.monitor_search_recids_found) == 0 else True
    if self.found == False:
      self.is_requestable = False
    self.monitor_search_time_taken = datetime.datetime.now() - self.monitor_search_start_time
    return
    
    
  def checkRecords( self ):
    '''
    Purpose: A wrapper function; for each self.monitor_search_recids_found entry, 
             - initiates the 'record' api search
             - calls the monitor-record-check function to see if there are still active clients
             - calls the evaluate-record-check function after above to see if the item is requestable
    '''
    import time
    assert self.found == True, Exception( u'self.found should be True; it is: %s' % self.found )
    assert len(self.monitor_search_recids_found) > 0 and type(self.monitor_search_recids_found) == list, Exception( u'self.monitor_search_recids_found must be a populated list; it is %s' % self.monitor_search_recids_found )
    for entry in self.monitor_search_recids_found:
      self.check_records_current_record = entry
      ## initiate record-check
      self.checkRecords_initiateRecordCheck()
      ## monitor record-check
      self.checkRecords_monitorRecordCheck()
      ## evaluate record-check result
      self.checkRecords_evaluateRecordCheckResult()
      if self.is_requestable == True:
        break
    return
    
    
  def checkRecords_initiateRecordCheck( self ):
    '''
    Purpose: Initiates record search.
    Called by: checkRecords()
    ''' 
    assert type(self.check_records_current_record) == unicode, Exception( u'self.check_records_current_record must be a unicode string; it is of type: %s' % type(check_records_current_record) )
    payload = {
      u'command': u'record',
      u'id': self.check_records_current_record,
      u'type': u'json' }
    r = requests.get( self.BD_API_URL, cookies=self.cookies_recent, params=payload )
    self.check_records_initiation_urls.append( r.url )
    self.cookies_recent = self.makeCookieDict( r )
    self.cookies_history.append( {u'check_records_initiation': self.cookies_recent} )
    self.check_records_initiation_responses.append( r.content.decode(u'utf-8', u'replace') )
    return
    
    
  def checkRecords_monitorRecordCheck( self ):
    '''
    Purpose: Execute a followup record-search query & monitor results until there are no more bd-active-clients or until timeout.
    Called by: checkRecords()
    '''
    assert isinstance(self.check_records_initiation_urls[-1], unicode), Exception( u'self.check_records_initiation_urls[-1] must be of type unicode; it is of type %s' % type(self.check_records_initiation_urls[-1]) )
    assert isinstance(self.CHECK_RECORDS_MONITOR_TIMEOUT, int), Exception( u'self.CHECK_RECORDS_MONITOR_TIMEOUT must be of type int; it is of type %s' % type(self.CHECK_RECORDS_MONITOR_TIMEOUT) )
    assert isinstance(self.CHECK_RECORDS_MONITOR_INTERVAL, int), Exception( u'self.CHECK_RECORDS_MONITOR_INTERVAL must be of type int; it is of type %s' % type(self.CHECK_RECORDS_MONITOR_INTERVAL) )
    ## check existing response
    jd = json_dict = json.loads( self.check_records_initiation_responses[-1], strict=False )
    if jd[u'activeclients'] == [u'0']:  # done; no need to monitor
      return
    ## get & monitor subsequent responses if necessary
    self.check_records_monitor_current_start_time = datetime.datetime.now()
    self.check_records_monitor_current_end_time = self.check_records_monitor_current_start_time + datetime.timedelta( seconds=self.CHECK_RECORDS_MONITOR_TIMEOUT )
    continue_flag = u'continue'
    while continue_flag == u'continue':
      r = requests.get( self.check_records_initiation_urls[-1], cookies=self.cookies_recent )  # url with parameters set in checkRecords_initiateRecordCheck()
      self.cookies_recent = self.makeCookieDict(r)
      self.cookies_history.append( {u'check_records_monitor': self.cookies_recent} )
      self.check_records_monitor_responses.append( r.content.decode(u'utf-8', u'replace') )
      jd = json_dict = json.loads( self.check_records_monitor_responses[-1], strict=False )
      if jd[u'activeclients'] == [u'0'] or datetime.datetime.now() > self.check_records_monitor_current_end_time:
        continue_flag = u'stop'
        self.check_records_monitor_timetaken_results.append( datetime.datetime.now() - self.check_records_monitor_current_start_time )
      else:
        time.sleep( self.CHECK_RECORDS_MONITOR_INTERVAL )
    return
    
    
  def checkRecords_evaluateRecordCheckResult( self ):
    '''
    Purpose: Examine the recent check_records_monitor_responses entry to see if the item is requestable.
    Called by: checkRecords()
    '''
    assert len(self.check_records_monitor_responses) > 0 and type(self.check_records_monitor_responses) == list, Exception( u'self.check_records_monitor_responses must a populated list; it is %s' % self.check_records_monitor_responses )
    jd = json_dict = json.loads( self.check_records_monitor_responses[-1], strict=False )
    if u'interLibraryLoanInfo' not in jd.keys():
      self.check_records_evaluation_results.append( { 
        u'record_id': self.check_records_current_record,
        u'interLibraryLoanInfo': u'no_info'
        } )
      self.is_requestable = False
    else:
      if jd[u'interLibraryLoanInfo'][0][u'buttonLabel'] == [u'Request'] and jd[u'interLibraryLoanInfo'][0][u'buttonLink'] == [u'AddRequest']:
        self.check_records_evaluation_results.append( { 
          u'record_id': self.check_records_current_record,
          u'interLibraryLoanInfo': jd[u'interLibraryLoanInfo']
          } )
        self.is_requestable = True
      else:
        self.check_records_evaluation_results.append( { 
          u'record_id': self.check_records_current_record,
          u'interLibraryLoanInfo': jd[u'interLibraryLoanInfo']  # log to gain sense of possibilities
          } )
        self.is_requestable = False
    return
    
    
  def requestInitiate( self ):
    '''
    Purpose: Submit request for item.
    Note: no item info submitted; thus must be tracked via session.
    '''
    assert self.COMMAND == u'request', Exception( u'self.COMMAND must be u"request"; it is %s' % self.COMMAND )
    assert self.is_requestable == True, Exception( u'self.is_requestable must be True; it is %s' % self.is_requestable )
    assert len(self.BD_API_URL) > 0 and type(self.BD_API_URL) == unicode, Exception( u'self.BD_API_URL requires a unicode string; it is of type %s' % type(self.BD_API_URL) )
    assert len(self.REQUEST_PICKUP_LOCATION) > 0 and type(self.REQUEST_PICKUP_LOCATION) == unicode, Exception( u'self.REQUEST_PICKUP_LOCATION requires a unicode string; it is of type %s' % type(self.REQUEST_PICKUP_LOCATION) )
    payload = {
      u'command': u'relaisaddrequest',
      u'arPickupLocation': self.REQUEST_PICKUP_LOCATION }
    r = requests.get( self.BD_API_URL, cookies=self.cookies_recent, params=payload )
    self.request_url = r.url
    self.cookies_recent = self.makeCookieDict(r)
    self.cookies_history.append( {u'request': self.cookies_recent} )
    self.request_response = r.content.decode(u'utf-8', u'replace')
    self.requestEvaluate()  # populates self.request_transaction_num
    
    
  def requestEvaluate( self ):
    '''
    Purpose: Extract transaction number.
    Called by: self.requestInitiate()
    '''
    assert len(self.request_response) > 0 and type(self.request_response) == unicode, Exception( u'self.request_response requires a unicode string; it is %s' % self.request_response )
    start_index = self.request_response.find( u'Number: ' ) + len( u'Number: ' )
    end_index = self.request_response.find( u')' )
    transaction_id = self.request_response[ start_index:end_index ]
    if len(transaction_id) > 0:
      self.request_transaction_num = transaction_id.strip()
    else:
      self.request_transaction_num = u'unknown'
      
      
  ## common-case wrapper functions
  
  
  def request( self ):
    '''
    Purpose: Convenience wrapper function which performs isbn search 
             and attempts to request item if it's requestable
    '''
    assert len(self.BD_API_URL) > 0 and type(self.BD_API_URL) == unicode, Exception( u'self.BD_API_URL requires a unicode string; it is %s' % self.BD_API_URL )
    assert len(self.PATRON_BARCODE) > 0 and type(self.PATRON_BARCODE) == unicode, Exception( u'self.PATRON_BARCODE requires a unicode string; it is %s' % self.PATRON_BARCODE )
    assert len(self.UNIVERSITY_CODE) > 0 and type(self.UNIVERSITY_CODE) == unicode, Exception( u'self.UNIVERSITY_CODE requires a unicode string; it is %s' % self.UNIVERSITY_CODE )
    assert len(self.REQUESTED_ISBN) > 0 and type(self.REQUESTED_ISBN) == unicode, Exception( u'self.REQUESTED_ISBN requires a unicode string; it is %s' % self.REQUESTED_ISBN )
    assert self.COMMAND == u'request', Exception( u'self.COMMAND must be u"request"; it is %s' % self.COMMAND )
    assert len(self.REQUEST_PICKUP_LOCATION) > 0 and type(self.REQUEST_PICKUP_LOCATION) == unicode, Exception( u'self.REQUEST_PICKUP_LOCATION requires a unicode string; it is of type %s' % type(self.REQUEST_PICKUP_LOCATION) )
    self.login()
    self.initiateIsbnSearch()
    self.monitorIsbnSearch()
    if self.found == True:
      self.checkRecords()  # sets self.is_requestable
    else:
      self.request_transaction_num = u'not_applicable'
    if self.is_requestable:
      self.requestInitiate()  # sets self.request_transaction_num
    return

  
  def search( self ):
    '''
    Purpose: Convenience wrapper function which performs isbn search 
             and sets self.found & self.is_requestable
    '''
    assert len(self.BD_API_URL) > 0 and type(self.BD_API_URL) == unicode, Exception( u'self.BD_API_URL requires a unicode string; it is %s' % self.BD_API_URL )
    assert len(self.PATRON_BARCODE) > 0 and type(self.PATRON_BARCODE) == unicode, Exception( u'self.PATRON_BARCODE requires a unicode string; it is %s' % self.PATRON_BARCODE )
    assert len(self.UNIVERSITY_CODE) > 0 and type(self.UNIVERSITY_CODE) == unicode, Exception( u'self.UNIVERSITY_CODE requires a unicode string; it is %s' % self.UNIVERSITY_CODE )
    assert len(self.REQUESTED_ISBN) > 0 and type(self.REQUESTED_ISBN) == unicode, Exception( u'self.REQUESTED_ISBN requires a unicode string; it is %s' % self.REQUESTED_ISBN )
    assert self.COMMAND == u'search', Exception( u'self.COMMAND must be u"search"; it is %s' % self.COMMAND )
    self.login()
    self.initiateIsbnSearch()
    self.monitorIsbnSearch()
    if self.found == True:
      self.checkRecords()  # sets self.is_requestable
    return
    

  ## helper functions ##
  
  
  def makeCookieDict( self, r ):
    '''
    Extracts cookie_dict from request object's cookies object.
    '''
    cookie_dict = {}
    for k, v in r.cookies.items():
      cookie_dict[k.decode(u'utf-8')] = v.decode(u'utf-8')
    return cookie_dict
    
    
  def updateRecordIdsFound( self, json_string, found_list ):
    '''
    - Updates found_list with new recid entries.
    '''
    assert type(json_string) == unicode, Exception( u'json_string must be of type unicode; it is %s' % type(json_string) )
    assert type(found_list) == NoneType or type(found_list) == list, Exception( u'found_list must be of type NoneType or list; it is %s' % type(found_list) )
    if found_list == None:
      found_list = []
    d = json.loads( json_string, strict=False )
    if u'hit' in d.keys():
      for entry in d[u'hit']:
        recid = entry[u'recid'][0]
        if recid not in found_list:
          found_list.append( recid )
    return sorted( found_list )
    