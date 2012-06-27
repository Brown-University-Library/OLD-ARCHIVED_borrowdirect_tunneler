_( formatted in [markdown](http://daringfireball.net/projects/markdown/) )_

On this page...
===============

- Common usage
- Notes
- License

---
  
  
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

---


Notes
=====

- BorrowDirect api flow:
    - login
    - initiate isbn search
    - monitor isbn search results to get record-ids
    - loop through record-ids
        - initiate record-id search
        - monitor record-id search results to determine if item is requestable
    - request item

- \_\_init\_\_() attributes, and module functions, are ordered via above api flow.

- attributes in caps can be passed in via settings.

- __asserts__ at beginning of functions document expected context.

- given above api flow, _both_ the monitor-isbn-search and monitor-record-id-search functions below allow
  optional specification of TIMEOUT and check-INTERVAL values.

- using strict=False for json.loads() because without it, multiple api-hits returned:
 
        ValueError: Invalid control character at: line x column y (char z)
  
- rich information about the search/request process can be gleaned via pprint( bd.\_\_dict\_\_ )

- dependencies: [requests](http://docs.python-requests.org/en/latest/index.html) 

- contact info: 
    - borrowdirect/library info: bonnie_buzzell@brown.edu, knowledge-systems librarian
    - code: birkin_diana@brown.edu, programmer

---


License
=======

[BorrowDirect Tunneler] [BDT] by [Brown University Library] [BUL]
is licensed under a [Creative Commons Attribution-ShareAlike 3.0 Unported License] [CC BY-SA 3.0]

[BDT]: https://github.com/Brown-University-Library/borrowdirect_tunneler
[BUL]: http://library.brown.edu/its/software/
[CC BY-SA 3.0]: http://creativecommons.org/licenses/by-sa/3.0/

Human readable summary:

    You are free:
    - to Share — to copy, distribute and transmit the work
    - to Remix — to adapt the work
    - to make commercial use of the work

    Under the following conditions:
    - Attribution — You must attribute the work to:
      Brown University Library - http://library.brown.edu/its/software/
    - Share Alike — If you alter, transform, or build upon this work, 
      you may distribute the resulting work only under the same 
      or similar license to this one.  

---
