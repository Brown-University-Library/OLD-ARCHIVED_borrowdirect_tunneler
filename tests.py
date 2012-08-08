# -*- coding: utf-8 -*-

import pprint, unittest


class BdTunnelerTests( unittest.TestCase ):
  
  def test_settings_instantiation(self):
    '''
    Tests that module instantiation handles settings not-defined, or defined as dict, module, or path.
    '''
    import exceptions, imp
    ## no settings passed on instantiation
    bd = BD_Tunneler()  # no settings info
    assert isinstance(bd, BD_Tunneler), type(bd)
    ## dict settings    
    settings_dict = {}  ## test empty
    bd = BD_Tunneler( settings_dict )
    assert bd.PATRON_BARCODE == None, bd.PATRON_BARCODE
    settings_dict = { u'PATRON_BARCODE': u'123' }  ## test populated
    bd = BD_Tunneler( settings_dict )
    assert bd.PATRON_BARCODE == u'123', bd.PATRON_BARCODE
    ## module settings
    s = imp.new_module( u'settings' )  ## test empty
    bd = BD_Tunneler( s )
    assert bd.PATRON_BARCODE == None, bd.PATRON_BARCODE
    s = imp.new_module( u'settings' )  ## test populated
    s.PATRON_BARCODE = u'234'
    bd = BD_Tunneler( s )
    assert bd.PATRON_BARCODE == u'234', bd.PATRON_BARCODE
    ## TODO: test settings path
    # end def test_settings_instantiation()
    
  def test_login_production(self):
    '''
    Tests access & storage of authentication cookie info.
    '''
    settings = {
      u'BD_API_URL': module_settings.BD_API_URL,
      u'PATRON_BARCODE': module_settings.LEGIT_PATRON_BARCODE,
      u'UNIVERSITY_CODE': module_settings.LEGIT_UNIVERSITY_CODE }
    bd = BD_Tunneler( settings )
    assert bd.BD_API_URL == module_settings.BD_API_URL, bd.BD_API_URL
    assert bd.UNIVERSITY_CODE == module_settings.LEGIT_UNIVERSITY_CODE, bd.UNIVERSITY_CODE
    bd.login()
    assert bd.login_url == module_settings.TEST_BD_URL_AUTH_FULL, bd.login_url
    assert len(bd.login_response) > 100, bd.login_response  # html, which we don't care about
    assert type(bd.cookies_recent) == dict, type(bd.cookies_recent)
    assert bd.cookies_recent.keys() == [u'JSESSIONID'], bd.cookies_recent.keys()
            
  def test_initiateIsbnSearch(self):
    bd = BD_Tunneler()
    bd.BD_API_URL = module_settings.BD_API_URL
    bd.PATRON_BARCODE = module_settings.LEGIT_PATRON_BARCODE
    bd.UNIVERSITY_CODE = module_settings.LEGIT_UNIVERSITY_CODE
    bd.login()
    assert bd.cookies_recent.keys() == [u'JSESSIONID'], bd.cookies_recent.keys()
    bd.REQUESTED_ISBN = u'9780688002305'  # ZMM, http://www.worldcat.org/oclc/673595
    bd.initiateIsbnSearch()
    assert bd.initiate_search_status == True, bd.initiate_search_status
      
  def test_monitorIsbnSearch(self):
    settings = {
      u'BD_API_URL': module_settings.BD_API_URL,
      u'PATRON_BARCODE': module_settings.LEGIT_PATRON_BARCODE,
      u'UNIVERSITY_CODE': module_settings.LEGIT_UNIVERSITY_CODE,
      u'REQUESTED_ISBN': u'9780688002305' }  # ZMM, http://www.worldcat.org/oclc/673595
    bd = BD_Tunneler( settings )
    bd.login()
    assert bd.logged_in_status == True, bd.logged_in_status
    bd.initiateIsbnSearch()
    assert bd.initiate_search_status == True, bd.initiate_search_response
    ## test
    assert bd.monitor_search_recids_found == None
    bd.monitorIsbnSearch( interval=2, timeout=15 )
    assert len(bd.monitor_search_recids_found) > 0, bd.monitor_search_responses 
        
  def test_checkRecords(self):
    import json
    settings = {
      u'BD_API_URL': module_settings.BD_API_URL,
      u'PATRON_BARCODE': module_settings.LEGIT_PATRON_BARCODE,
      u'UNIVERSITY_CODE': module_settings.LEGIT_UNIVERSITY_CODE,
      u'REQUESTED_ISBN': u'9780688002305' }  # ZMM, http://www.worldcat.org/oclc/673595
    bd = BD_Tunneler( settings )
    bd.login()
    assert bd.logged_in_status == True, bd.logged_in_status
    bd.initiateIsbnSearch()
    assert bd.initiate_search_status == True, bd.initiate_search_response
    bd.monitorIsbnSearch()
    assert len(bd.monitor_search_recids_found) > 0, bd.monitor_search_responses
    ## test INITIATE
    assert bd.check_records_initiation_responses == [], bd.check_records_initiation_responses
    bd.checkRecords()
    assert len(bd.check_records_initiation_responses) > 0, bd.check_records_initiation_responses
    assert type(json.loads(bd.check_records_initiation_responses[0], strict=False)) == dict, type(json.loads(bd.check_records_initiation_responses[0], strict=False))    
    ## test MONITOR
    assert len(bd.check_records_monitor_responses) > 0, bd.check_records_monitor_responses
    assert type(json.loads(bd.check_records_monitor_responses[0], strict=False)) == dict, type(json.loads(bd.check_records_monitor_responses[0], strict=False))    
    ## test EVALUATE
    assert bd.is_requestable != None
    assert len(bd.check_records_evaluation_results) > 0
        
  def test_checkRecords_evaluateRecordCheckResult(self):
    ## failure: no 'interLibraryLoanInfo'
    bd = BD_Tunneler()
    bd.check_records_current_record = u'the record id text a'
    bd.check_records_monitor_responses = [ u'{"irrelevant_key_a": "val_a", "irrelevant_key_b": "val_b"}' ]
    bd.checkRecords_evaluateRecordCheckResult()
    assert sorted(bd.check_records_evaluation_results) == [{
      u'record_id': u'the record id text a', 
      u'interLibraryLoanInfo': u'no_info'}], sorted(bd.check_records_evaluation_results)
    assert bd.is_requestable == False, bd.is_requestable
    ## failure: 'interLibraryLoanInfo', but not requestable
    bd = BD_Tunneler()
    bd.check_records_current_record = u'the record id text b'
    bd.check_records_monitor_responses = [ u'{"interLibraryLoanInfo":[{"requestMessage":["Available at Brown. Go to Josiah."],"RelaisPickupLocation":["Rockefeller Library"],"buttonLink":["http:\\/\\/josiah.brown.edu"],"buttonLabel":["Josiah"],"anyAvailable":["true"]}],"md-date":["1974"],"many_irrelevant_keys": "and_values"}' ]
    bd.checkRecords_evaluateRecordCheckResult()
    assert sorted(bd.check_records_evaluation_results) == [{
      u'record_id': u'the record id text b', 
      u'interLibraryLoanInfo': [{u'anyAvailable': [u'true'], u'buttonLabel': [u'Josiah'], u'buttonLink': [u'http://josiah.brown.edu'], u'requestMessage': [u'Available at Brown. Go to Josiah.'], u'RelaisPickupLocation': [u'Rockefeller Library']}]}], sorted(bd.check_records_evaluation_results)
    assert bd.is_requestable == False, bd.is_requestable
    ## success
    bd = BD_Tunneler()
    bd.check_records_current_record = u'the record id text c'
    bd.check_records_monitor_responses = [ u'{"interLibraryLoanInfo":[{"requestMessage":["Request this through Borrow Direct."],"RelaisPickupLocation":["Rockefeller Library"],"buttonLink":["AddRequest"],"buttonLabel":["Request"],"anyAvailable":["true"]}],"md-date":["1974-1999"], "many_irrelevant_keys": "and_values"}' ]
    bd.checkRecords_evaluateRecordCheckResult()
    assert sorted(bd.check_records_evaluation_results) == [{
      u'record_id': u'the record id text c', 
      u'interLibraryLoanInfo': [{u'anyAvailable': [u'true'], u'buttonLabel': [u'Request'], u'buttonLink': [u'AddRequest'], u'requestMessage': [u'Request this through Borrow Direct.'], u'RelaisPickupLocation': [u'Rockefeller Library']}]}], sorted(bd.check_records_evaluation_results)
    assert bd.is_requestable == True, bd.is_requestable
    
  # def test_RequestInitiate(self):
  #   '''
  #   WARNING -- THIS WILL REALLY SUBMIT A REQUEST!
  #   '''
  #   import json
  #   settings = {
  #     u'BD_API_URL': module_settings.BD_API_URL,
  #     u'PATRON_BARCODE': module_settings.LEGIT_PATRON_BARCODE,
  #     u'UNIVERSITY_CODE': module_settings.LEGIT_UNIVERSITY_CODE,
  #     u'REQUESTED_ISBN': u'9780688002305',  # ZMM, http://www.worldcat.org/oclc/673595
  #     u'COMMAND': u'request',
  #     u'REQUEST_PICKUP_LOCATION': u'Rockefeller Library' }
  #   bd = BD_Tunneler( settings )
  #   bd.login()
  #   bd.initiateIsbnSearch()
  #   bd.monitorIsbnSearch()
  #   bd.checkRecords()
  #   assert bd.is_requestable != None
  #   bd.requestInitiate()
  #   # print u'\n- bd.__dict__:'; pprint.pprint(bd.__dict__)
  #   assert bd.request_transaction_num[0:3] == u'BRO', bd.request_transaction_num
      
  def test_RequestEvaluate(self):
    bd = BD_Tunneler()
    ## good info
    bd.request_response = u'<?xml version="1.0" encoding="UTF-8"?><addrequestresponse><confirmmsg>Your request has been submitted to Borrow Direct (Request Number: BRO-10374709)</confirmmsg></addrequestresponse>\n'
    bd.requestEvaluate()
    assert bd.request_transaction_num == u'BRO-10374709', bd.request_transaction_num
    ## bad info
    bd.request_response = u'blah'
    bd.requestEvaluate()
    assert bd.request_transaction_num == u'unknown', bd.request_transaction_num
    
  ## common-case convenience function tests
    
  def test_Search(self):
    '''
    Tests common-case wrapper function.
    '''
    settings = {
      u'BD_API_URL': module_settings.BD_API_URL,
      u'PATRON_BARCODE': module_settings.LEGIT_PATRON_BARCODE,
      u'UNIVERSITY_CODE': module_settings.LEGIT_UNIVERSITY_CODE,
      u'REQUESTED_ISBN': u'9780688002305',  # ZMM, http://www.worldcat.org/oclc/673595
      u'COMMAND': u'search' } 
    bd = BD_Tunneler( settings )
    assert bd.found == None, bd.found
    assert bd.is_requestable == None, bd.is_requestable
    bd.search()
    assert bd.found == True or bd.found == False, bd.found
    assert bd.is_requestable == True or bd.is_requestable == False, bd.is_requestable
        
  # def test_Request(self):
  #   '''
  #   Tests common-case wrapper function.
  #   WARNING -- THIS WILL REALLY SUBMIT A REQUEST!
  #   '''
  #   settings = {
  #     u'BD_API_URL': module_settings.BD_API_URL,
  #     u'PATRON_BARCODE': module_settings.LEGIT_PATRON_BARCODE,
  #     u'UNIVERSITY_CODE': module_settings.LEGIT_UNIVERSITY_CODE,
  #     u'REQUESTED_ISBN': u'9780688002305',  # ZMM, http://www.worldcat.org/oclc/673595
  #     u'COMMAND': u'request',
  #     u'REQUEST_PICKUP_LOCATION': u'Rockefeller Library' }
  #   bd = BD_Tunneler( settings )
  #   assert bd.found == None, bd.found
  #   assert bd.is_requestable == None, bd.is_requestable
  #   assert bd.request_transaction_num == None, bd.request_transaction_num
  #   bd.request()
  #   assert bd.found == True or bd.found == False, bd.found
  #   assert bd.is_requestable == True or bd.is_requestable == False, bd.is_requestable
  #   assert bd.request_transaction_num == u'unknown' or bd.request_transaction_num[0:3] == u'BRO', bd.request_transaction_num

  # end class BdTunnelerTests()
    
    
if __name__ == "__main__":
  from bd_tunneler import BD_Tunneler
  import bd_tunneler_module_local_settings as module_settings  # module_settings only needed for tests
  activate_this = module_settings.VIRTUALENV_PATH
  execfile( activate_this, dict(__file__=activate_this) )
  unittest.main()
  