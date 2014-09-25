_( formatted in [markdown](http://daringfireball.net/projects/markdown/) )_

About
=====

'bd_tunneler' faciliates programmatic access to 'BorrowDirect', an accademic book-borrowing consortium.

---


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
        ...   # or u'REQUESTED_TITLE': u'the title', u'REQUESTED_AUTHOR': u'last first', u'REQUESTED_DATE': u'1234',
        ...   u'COMMAND': u'search' } 
        >>> bd = BD_Tunneler( settings )  # at this point bd.found & bd.is_requestable are None
        >>> bd.searchIsbn()  # or bd.SearchString()
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
        ...   # or u'REQUESTED_TITLE': u'the title', u'REQUESTED_AUTHOR': u'last first', u'REQUESTED_DATE': u'1234',
        ...   u'COMMAND': u'request',
        ...   u'REQUEST_PICKUP_LOCATION': u'the-pickup-location' } 
        >>> bd = BD_Tunneler( settings )
        >>> bd.requestIsbn()  # or bd.RequestString()
        ## if requestable...
        >>> bd.request_transaction_num
        u'BRO-123'  # bd.found & bd.requestable would be True
        ## if not requestable...
        >>> bd.request_transaction_num
        u'not_applicable'  # bd.found could be True or False; bd.is_requestable would be False
        

---


Notes
=====

- BorrowDirect api flow for isbn-search:
    - login
    - initiate isbn search
    - monitor isbn search results to get record-ids
    - loop through record-ids
        - initiate record-id search
        - monitor record-id search results to determine if item is requestable
    - request item
    
- BorrowDirect api flow for string-search:
    - login
    - initiate record-id search
    - monitor record-id search results to determine if item is requestable
    - request item

- \_\_init\_\_() attributes, and module functions, are ordered via above api flow.

- attributes in caps can be passed; others are populated by program-flow.

- settings-handling is flexible, a dict (shown in example) or module or module-path or nothing can be passed in.

  - "nothing?" Sure...

            >>> bd = BD_Tunneler()
            >>> bd.BD_API_URL = u'a'; bd.PATRON_BARCODE = u'b'; bd.UNIVERSITY_CODE = u'c'; etc...
            >>> bd.requestIsbn()
            
  - ...or settings & attribute-assignments can be mixed & matched.

- __asserts__ at beginning of functions document expected context.

- given above api flow, _both_ the monitor-isbn-search and monitor-record-id-search functions allow
  optional specification of TIMEOUT and check-INTERVAL values.

- using strict=False for json.loads() because without it, multiple api-hits returned:
 
        ValueError: Invalid control character at: line x column y (char z)
  
- rich information about the search/request process can be gleaned via pprint( bd.\_\_dict\_\_ )

- dependencies: the wonderful [requests](http://docs.python-requests.org/en/latest/index.html) module.

- searching by string:

  - title and author must be lowercase, and contain no punctuation
  - author must be: last first (and middle initial if it's in the worldcat openurl)
  - date must be four characters
  
- milestones

  - 2012-08 -- updated for 2012-08 BorrowDirect upgrade.
  - 2012-09 -- added limited title/author/date string searching.

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
