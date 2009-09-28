from __future__ import absolute_import
from __future__ import with_statement

from ..sail.allegrographserver import AllegroGraphServer
from ..repository.repository import Repository
from ...miniclient import repository
from ..query.query import QueryLanguage
from ..vocabulary.rdf import RDF
from ..vocabulary.rdfs import RDFS
from ..vocabulary.owl import OWL
from ..vocabulary.xmlschema import XMLSchema
from ..query.dataset import Dataset
from ..rio.rdfformat import RDFFormat
from ..rio.rdfwriter import  NTriplesWriter
from ..rio.rdfxmlwriter import RDFXMLWriter

import os, urllib, datetime, time

CURRENT_DIRECTORY = os.path.dirname(__file__)

LOCALHOST = 'localhost'
AG_HOST = os.environ.get('AGRAPH_HOST', LOCALHOST)
AG_PORT = int(os.environ.get('AGRAPH_PORT', '10035'))
AG_ONSERVER = AG_HOST == LOCALHOST

CATALOG = 'tests'
STORE = 'agraph_test'

RAISE_EXCEPTION_ON_VERIFY_FAILURE = False

def verify(expressionValue, targetValue, quotedExpression, testNum):
    """
    Verify that 'expressionValue' equals 'targetValue'.  If not,
    raise an exception, or print a message advertising the failure.
    """
    if not expressionValue == targetValue:
        message = ("Diagnostic failure in test %s.  Expression '%s' returns '%s' where '%s' expected." %
                    (testNum, quotedExpression, expressionValue, targetValue))
        if RAISE_EXCEPTION_ON_VERIFY_FAILURE:
            raise Exception(message)
        else:
            print "BWEEP BWEEP BWEEP BWEEP BWEEP BWEEP BWEEP BWEEP BWEEP BWEEP BWEEP BWEEP BWEEP BWEEP BWEEP \n   ", message

def test0():
    server = AllegroGraphServer(AG_HOST, AG_PORT, 'test', 'xyzzy')
    print "Available catalogs", server.listCatalogs()

def connect(accessMode=Repository.RENEW):
    """
    Connect is called by the other tests to startup the connection to the test database.
    """
    print "Default working directory is '%s'" % (CURRENT_DIRECTORY)
    server = AllegroGraphServer(AG_HOST, AG_PORT, 'test', 'xyzzy')
    print "Available catalogs", server.listCatalogs()
    catalog = server.openCatalog(CATALOG)
    catalogs = catalog.listRepositories()
    print "Available repositories in catalog '%s':  %s" % (catalog.getName(), catalog.listRepositories())    

    # Instead of renewing the database, clear it.
    if accessMode == Repository.RENEW:
        mode = Repository.CREATE if STORE not in catalogs else Repository.OPEN
    else:
        mode = accessMode

    myRepository = catalog.getRepository(STORE, mode)
    myRepository.initialize()
    connection = myRepository.getConnection()

    if accessMode == Repository.RENEW:
        connection.clear()
        
    print "Repository %s is up!  It contains %i statements." % (
                myRepository.getDatabaseName(), connection.size())
    return connection

def test1(accessMode=Repository.RENEW):
    """
    Tests getting the repository up.
    """
    return connect(accessMode)
    
def test2():
    conn = connect()
    ## create some resources and literals to make statements out of
    alice = conn.createURI("http://example.org/people/alice")
    bob = conn.createURI("http://example.org/people/bob")
    #bob = conn.createBNode()
    name = conn.createURI("http://example.org/ontology/name")
    person = conn.createURI("http://example.org/ontology/Person")
    bobsName = conn.createLiteral("Bob")
    alicesName = conn.createLiteral("Alice")
    print "Triple count before inserts: ", conn.size()
    for s in conn.getStatements(None, None, None, None): print s    
    ## alice is a person
    conn.add(alice, RDF.TYPE, person)
    ## alice's name is "Alice"
    conn.add(alice, name, alicesName)
    ## bob is a person
    conn.add(bob, RDF.TYPE, person)
    ## bob's name is "Bob":
    conn.add(bob, name, bobsName)
    print "Triple count: ", conn.size()
    verify(conn.size(), 4, 'conn.size()', 2)
    for s in conn.getStatements(None, None, None, None): print s    
    conn.remove(bob, name, bobsName)
    print "Triple count: ", conn.size()
    verify(conn.size(), 3, 'conn.size()', 2)
    conn.add(bob, name, bobsName)    
    return conn
    
def test3():    
    conn = test2()
    try:
        queryString = "SELECT ?s ?p ?o  WHERE {?s ?p ?o .}"
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
        result = tupleQuery.evaluate();
        verify(result.rowCount(), 4, 'len(result)', 3)
        try:
            for bindingSet in result:
                s = bindingSet.getValue("s")
                p = bindingSet.getValue("p")
                o = bindingSet.getValue("o")              
                print "%s %s %s" % (s, p, o)
        finally:
            result.close();
    finally:
        conn.close();
        
def test4():
    conn = test2()
    alice = conn.createURI("http://example.org/people/alice")
#    statements = conn.getStatements(alice, None, None, tripleIDs=True)
    print "Searching for Alice using getStatements():"
    statements = conn.getStatements(alice, None, None)
    statements.enableDuplicateFilter() ## there are no duplicates, but this exercises the code that checks
    verify(statements.rowCount(), 2, 'statements.rowCount()', 3)
    for s in statements:
        print s
    statements.close()
    print "Same thing using JDBC:"
#    resultSet = conn.getJDBCStatements(alice, None, None, tripleIDs=True)
    resultSet = conn.getJDBCStatements(alice, None, None)
    verify(resultSet.rowCount(), 2, 'resultSet.rowCount()', 3)    
    while resultSet.next():        
        print "   ", resultSet.getValue(2), "   ", resultSet.getString(2)  
               
def test5():
    """
    Typed Literals
    """
    conn = connect()
    exns = "http://example.org/people/"
    alice = conn.createURI("http://example.org/people/alice")
    age = conn.createURI(namespace=exns, localname="age")
    weight = conn.createURI(namespace=exns, localname="weight")    
    favoriteColor = conn.createURI(namespace=exns, localname="favoriteColor")
    birthdate = conn.createURI(namespace=exns, localname="birthdate")
    ted = conn.createURI(namespace=exns, localname="Ted")
    red = conn.createLiteral('Red')
    rouge = conn.createLiteral('Rouge', language="fr")
    fortyTwo = conn.createLiteral('42', datatype=XMLSchema.INT)
    fortyTwoInteger = conn.createLiteral('42', datatype=XMLSchema.LONG)     
    fortyTwoUntyped = conn.createLiteral('42')
    date = conn.createLiteral('1984-12-06', datatype=XMLSchema.DATE)     
    time = conn.createLiteral('1984-12-06T09:00:00', datatype=XMLSchema.DATETIME)   
    weightFloat = conn.createLiteral('20.5', datatype=XMLSchema.FLOAT)
    weightUntyped = conn.createLiteral('20.5')
    stmt1 = conn.createStatement(alice, age, fortyTwo)
    stmt2 = conn.createStatement(ted, age, fortyTwoUntyped)    
    conn.add(stmt1)
    conn.addStatement(stmt2)
    conn.addTriple(alice, weight, weightUntyped)
    conn.addTriple(ted, weight, weightFloat)
    conn.addTriples([(alice, favoriteColor, red),
                     (ted, favoriteColor, rouge),
                     (alice, birthdate, date),
                     (ted, birthdate, time)])
    for obj in [None, fortyTwo, fortyTwoUntyped, conn.createLiteral('20.5', datatype=XMLSchema.FLOAT), conn.createLiteral('20.5'),
                red, rouge]:
        print "Retrieve triples matching '%s'." % obj
        statements = conn.getStatements(None, None, obj)
        for s in statements:
            print s
    for obj in ['42', '"42"', '20.5', '"20.5"', '"20.5"^^xsd:float', '"Rouge"@fr', '"Rouge"', '"1984-12-06"^^xsd:date']:
        print "Query triples matching '%s'." % obj
        queryString = """PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
        SELECT ?s ?p ?o WHERE {?s ?p ?o . filter (?o = %s)}""" % obj
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
        result = tupleQuery.evaluate();    
        for bindingSet in result:
            s = bindingSet[0]
            p = bindingSet[1]
            o = bindingSet[2]
            print "%s %s %s" % (s, p, o)
    ## Search for date using date object in triple pattern.
    print "Retrieve triples matching DATE object."
    statements = conn.getStatements(None, None, date)
    for s in statements:
        print s
    ## Search for datetime using datetime object in triple pattern.
    print "Retrieve triples matching DATETIME object."
    statements = conn.getStatements(None, None, time)
    for s in statements:
        print s
    ## Search for specific date value.
    print "Match triples having specific DATE value."
    statements = conn.getStatements(None, None, '"1984-12-06"^^<http://www.w3.org/2001/XMLSchema#date>')
    for s in statements:
        print s
    ## Search for specific datetime value.
    print "Match triples having specific DATETIME value."
    statements = conn.getStatements(None, None, '"1984-12-06T09:00:00"^^<http://www.w3.org/2001/XMLSchema#dateTime>')
    for s in statements:
        print s
    ## Search for triples of type xsd:date using SPARQL query.
    print "Use SPARQL to find triples where the value matches a specific xsd:date."
    queryString = """SELECT ?s ?p WHERE {?s ?p "1984-12-06"^^<http://www.w3.org/2001/XMLSchema#date> }"""
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate();    
    for bindingSet in result:
        s = bindingSet[0]
        p = bindingSet[1]
        print "%s %s" % (s, p)
    ## Search for triples of type xsd:datetime using SPARQL query.
    print "Use SPARQL to find triples where the value matches a specific xsd:dateTime."
    queryString = """SELECT ?s ?p WHERE {?s ?p "1984-12-06T09:00:00"^^<http://www.w3.org/2001/XMLSchema#dateTime> }"""
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate();    
    for bindingSet in result:
        s = bindingSet[0]
        p = bindingSet[1]
        print "%s %s" % (s, p)


def test6(conn = None):
    if conn is None:
        conn = connect()
    else:
        conn.clear()   
    print "Starting example test6()."
    # The following paths are relative to os.getcwd(), the working directory.
    print "Default working directory is '%s'" % (CURRENT_DIRECTORY)
    # If you get a "file not found" error, use os.chdir("your directory path") to 
    # point to the location of the data files. For AG Free Edition on Windows:
    #os.chdir("C:\Program Files\AllegroGraphFJE32\python")
    print "Current working directory is '%s'" % (os.getcwd())
    path1 = os.path.join(CURRENT_DIRECTORY, "vc-db-1.rdf")
    path2 = os.path.join(CURRENT_DIRECTORY, "kennedy.ntriples")
    baseURI = "http://example.org/example/local"
    context = conn.createURI("http://example.org#vcards")
    conn.setNamespace("vcd", "http://www.w3.org/2001/vcard-rdf/3.0#");
    ## read kennedy triples into the null context:
    print "Load kennedy.ntriples."
    #conn.add(path2, base=baseURI, format=RDFFormat.NTRIPLES, contexts=None)
    conn.add(path2, base=baseURI, format=RDFFormat.NTRIPLES)
    ## read vcards triples into the context 'context':
    print "Load vcards triples."
    conn.addFile(path1, baseURI, format=RDFFormat.RDFXML, context=context);
    print "After loading, repository contains %i vcard triples in context '%s'\n    and   %i kennedy triples in context '%s'." % (
           conn.size(context), context, conn.size('null'), 'null')
    verify(conn.size(context), 16, 'conn.size(context)', 6)
    verify(conn.size('null'), 1214, "conn.size('null)", 6)    
    return conn
        
def test7():    
    conn = test6()
    print "Match all and print subjects and contexts"
    result = conn.getStatements(None, None, None, None, limit=25)
    for row in result: print row.getSubject(), row.getContext()
    print "\nSame thing with SPARQL query (can't retrieve triples in the null context)"
    queryString = "SELECT DISTINCT ?s ?c WHERE {graph ?c {?s ?p ?o .} }"
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate();
    for i, bindingSet in enumerate(result):
        print bindingSet[0], bindingSet[1]
    conn.close()

import urlparse

def test8():
    conn = test6()
    context = conn.createURI("http://example.org#vcards")
    outputFile = "/tmp/temp.nt"
    #outputFile = None
    if outputFile == None:
        print "Writing RDF to Standard Out instead of to a file"
    ntriplesWriter = NTriplesWriter(outputFile)
    conn.export(ntriplesWriter, context);
    outputFile2 = "/tmp/temp.rdf"
    #outputFile2 = None
    if outputFile2 == None:
        print "Writing NTriples to Standard Out instead of to a file"
    rdfxmlfWriter = RDFXMLWriter(outputFile2)    
    conn.export(rdfxmlfWriter, context)

def test9():
    conn = test6()
    conn.exportStatements(None, RDF.TYPE, None, False, RDFXMLWriter(None))

def test10():
    """
    Datasets and multiple contexts
    """
    conn = connect()
    exns = "http://example.org/people/"
    alice = conn.createURI(namespace=exns, localname="alice")
    bob = conn.createURI(namespace=exns, localname="bob")
    ted = conn.createURI(namespace=exns, localname="ted")
    person = conn.createURI(namespace=exns, localname="Person")
    name = conn.createURI(namespace=exns, localname="name")    
    alicesName = conn.createLiteral("Alice")    
    bobsName = conn.createLiteral("Bob")
    tedsName = conn.createLiteral("Ted")    
    context1 = conn.createURI(namespace=exns, localname="cxt1")      
    context2 = conn.createURI(namespace=exns, localname="cxt2")          
    conn.add(alice, RDF.TYPE, person, context1)
    conn.add(alice, name, alicesName, context1)
    conn.add(bob, RDF.TYPE, person, context2)
    conn.add(bob, name, bobsName, context2)
    conn.add(ted, RDF.TYPE, person)
    conn.add(ted, name, tedsName)
    statements = conn.getStatements(None, None, None)
    verify(statements.rowCount(), 6, 'statements.rowCount()', 10)
    print "All triples in all contexts:"
    for s in statements:
        print s
    statements = conn.getStatements(None, None, None, [context1, context2])
    verify(statements.rowCount(), 4, 'statements.rowCount()', 10)
    print "Triples in contexts 1 or 2:"
    for s in statements:
        print s
    statements = conn.getStatements(None, None, None, ['null', context2])
    verify(statements.rowCount(), 4, 'statements.rowCount()', 10)
    print "Triples in contexts null or 2:"
    for s in statements:
        print s
    ## testing named graph query:
    queryString = """
    SELECT ?s ?p ?o ?c
    WHERE { GRAPH ?c {?s ?p ?o . } } 
    """
    ds = Dataset()
    ds.addNamedGraph(context1)
    ds.addNamedGraph(context2)
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    tupleQuery.setDataset(ds)
    result = tupleQuery.evaluate(); 
    verify(result.rowCount(), 4, 'result.rowCount()', 10)   
    print "Query over contexts 1 and 2."
    for bindingSet in result:
        print bindingSet.getRow()
    ## testing default graph query:
    queryString = """
    SELECT ?s ?p ?o    
    WHERE {?s ?p ?o . } 
    """
    ds = Dataset()
    ds.addDefaultGraph('null')
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    tupleQuery.setDataset(ds)   
    result = tupleQuery.evaluate(); 
    verify(result.rowCount(), 2, 'result.rowCount()', 10)    
    print "Query over the null context."
    for bindingSet in result:
        print bindingSet.getRow()
    
def test11():
    """
    Namespaces
    """
    conn = connect()
    exns = "http://example.org/people/"
    alice = conn.createURI(namespace=exns, localname="alice")
    person = conn.createURI(namespace=exns, localname="Person")
    conn.add(alice, RDF.TYPE, person)
    conn.setNamespace('ex', exns)
    #conn.removeNamespace('ex')
    queryString = """
    SELECT ?s ?p ?o 
    WHERE { ?s ?p ?o . FILTER ((?p = rdf:type) && (?o = ex:Person) ) }
    """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate();  
    print    
    for bindingSet in result:
        print bindingSet[0], bindingSet[1], bindingSet[2]

def test12():
    """
    Text search
    """
    conn = connect()
    exns = "http://example.org/people/"
    conn.setNamespace('ex', exns)
    #myRepository.registerFreeTextPredicate("http://example.org/people/name")    
    conn.registerFreeTextPredicate(namespace=exns, localname='fullname')
    alice = conn.createURI(namespace=exns, localname="alice1")
    persontype = conn.createURI(namespace=exns, localname="Person")
    fullname = conn.createURI(namespace=exns, localname="fullname")    
    alicename = conn.createLiteral('Alice B. Toklas')
    book =  conn.createURI(namespace=exns, localname="book1")
    booktype = conn.createURI(namespace=exns, localname="Book")
    booktitle = conn.createURI(namespace=exns, localname="title")    
    wonderland = conn.createLiteral('Alice in Wonderland')
    conn.clear()    
    conn.add(alice, RDF.TYPE, persontype)
    conn.add(alice, fullname, alicename)
    conn.add(book, RDF.TYPE, booktype)    
    conn.add(book, booktitle, wonderland) 
    conn.setNamespace('ex', exns)
    print "Whole-word match for 'Alice'"
    queryString = """
    SELECT ?s ?p ?o
    WHERE { ?s ?p ?o . ?s fti:match 'Alice' . }
    """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate(); 
    print "Found %i query results" % len(result)
    count = 0
    for bindingSet in result:
        print bindingSet
        count += 1
        if count > 5: break
    print "Wildcard match for 'Ali*'"
    queryString = """
    SELECT ?s ?p ?o
    WHERE { ?s ?p ?o . ?s fti:match 'Ali*' . }
    """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate(); 
    print "Found %i query results" % len(result)
    count = 0
    for bindingSet in result:
        print bindingSet
        count += 1
        if count > 5: break
    print "Wildcard match for '?l?c?'"
    queryString = """
    SELECT ?s ?p ?o
    WHERE { ?s ?p ?o . ?s fti:match '?l?c?' . }
    """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate(); 
    print "Found %i query results" % len(result)
    count = 0
    for bindingSet in result:
        print bindingSet
        count += 1
        if count > 5: break
    print "Substring match for 'lic'"
    queryString = """
    SELECT ?s ?p ?o
    WHERE { ?s ?p ?o . FILTER regex(?o, "lic") }
    """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate(); 
    print "Found %i query results" % len(result)
    count = 0
    for bindingSet in result:
        print bindingSet
        count += 1
        if count > 5: break
#    queryString=""" 
#    SELECT ?s ?p ?o
#    WHERE { ?s ?p ?o . FILTER regex(?o, "Ali") }
#    """
def test13():
    """
    Ask, Construct, and Describe queries 
    """
    conn = test2()
    conn.setNamespace('ex', "http://example.org/people/")
    conn.setNamespace('ont', "http://example.org/ontology/")
    queryString = """select ?s ?p ?o where { ?s ?p ?o} """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate();
    print "SELECT result"
    for r in result: print r     
    queryString = """ask { ?s ont:name "Alice" } """
    booleanQuery = conn.prepareBooleanQuery(QueryLanguage.SPARQL, queryString)
    result = booleanQuery.evaluate(); 
    print "Boolean result", result
    queryString = """construct {?s ?p ?o} where { ?s ?p ?o . filter (?o = "Alice") } """
    constructQuery = conn.prepareGraphQuery(QueryLanguage.SPARQL, queryString)
    result = constructQuery.evaluate(); 
    for st in result:
        print "Construct result, S P O values in statement:", st.getSubject(), st.getPredicate(), st.getObject()
    #print "Construct result", [st for st in result]
    queryString = """describe ?s where { ?s ?p ?o . filter (?o = "Alice") } """
    describeQuery = conn.prepareGraphQuery(QueryLanguage.SPARQL, queryString)
    result = describeQuery.evaluate(); 
    print "Describe result"
    for st in result: print st 
    
def test14():
    """
    Parametric queries
    """
    conn = test2()
    alice = conn.createURI("http://example.org/people/alice")
    bob = conn.createURI("http://example.org/people/bob")
    queryString = """select ?s ?p ?o where { ?s ?p ?o} """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    tupleQuery.setBinding("s", alice)
    result = tupleQuery.evaluate()    
    print "Facts about Alice:"
    for r in result: print r  
    tupleQuery.setBinding("s", bob)
    print "Facts about Bob:"    
    result = tupleQuery.evaluate()
    for r in result: print r  
    
def test15():
    """
    Range matches
    """
    conn = connect()
    exns = "http://example.org/people/"
    conn.setNamespace('ex', exns)
    alice = conn.createURI(namespace=exns, localname="alice")
    bob = conn.createURI(namespace=exns, localname="bob")
    carol = conn.createURI(namespace=exns, localname="carol")    
    age = conn.createURI(namespace=exns, localname="age")    
    range = conn.createRange(30, 50)
    # range = conn.createRange(24, 42)  #this setting demonstrates that the limits are inclusive.
    if True: conn.registerDatatypeMapping(predicate=age, nativeType="int")
    if True: conn.registerDatatypeMapping(datatype=XMLSchema.INT, nativeType="int")  
    # True, True: Alice Age 42(int) AND Carol Age 39(int)  
    # True, False: Alice Age 42(int) AND Carol Age 39(int)
    # False, True: Alice Age 42(int)
    # False, False: Error
    conn.add(alice, age, 42)
    conn.add(bob, age, 24) 
    conn.add(carol, age, "39") 
    rows = conn.getStatements(None, age, range)
    for r in rows:
        print r 

def test16():
    """
    Federated triple stores.
    """
    return # Federation not supported yet
    def pt(kind, rows):
        print "\n%s Apples:\t" % kind.capitalize(),
        for r in rows: print r[0].getLocalName(),
    
    catalog = AllegroGraphServer(AG_HOST, port=AG_PORT).openCatalog(CATALOG) 
    ## create two ordinary stores, and one federated store: 
    redConn = catalog.getRepository("redthings", Repository.RENEW).initialize().getConnection()
    greenConn = greenRepository = catalog.getRepository("greenthings", Repository.RENEW).initialize().getConnection()
    #rainbowConn = (catalog.getRepository("rainbowthings", Repository.RENEW)
    #                     .addFederatedTripleStores(["redthings", "greenthings"]).initialize().getConnection())
    ex = "http://www.demo.com/example#"
    ## add a few triples to the red and green stores:
    redConn.add(redConn.createURI(ex+"mcintosh"), RDF.TYPE, redConn.createURI(ex+"Apple"))
    redConn.add(redConn.createURI(ex+"reddelicious"), RDF.TYPE, redConn.createURI(ex+"Apple"))    
    greenConn.add(greenConn.createURI(ex+"pippin"), RDF.TYPE, greenConn.createURI(ex+"Apple"))
    greenConn.add(greenConn.createURI(ex+"kermitthefrog"), RDF.TYPE, greenConn.createURI(ex+"Frog"))
    redConn.setNamespace('ex', ex)
    greenConn.setNamespace('ex', ex)
    #rainbowConn.setNamespace('ex', ex)        
    queryString = "select ?s where { ?s rdf:type ex:Apple }"
    ## query each of the stores; observe that the federated one is the union of the other two:
    pt("red", redConn.prepareTupleQuery(QueryLanguage.SPARQL, queryString).evaluate())
    pt("green", greenConn.prepareTupleQuery(QueryLanguage.SPARQL, queryString).evaluate())
    #pt("federated", rainbowConn.prepareTupleQuery(QueryLanguage.SPARQL, queryString).evaluate()) 

def kennedy_male_names(jdbc, conn=None):
    conn = test6(conn)
    conn.setNamespace("kdy", "http://www.franz.com/simple#")
    conn.setRuleLanguage(QueryLanguage.PROLOG)
    rules1 = """
    (<-- (woman ?person) ;; IF
         (q ?person !kdy:sex !kdy:female)
         (q ?person !rdf:type !kdy:person))
    (<-- (man ?person) ;; IF
         (q ?person !kdy:sex !kdy:male)
         (q ?person !rdf:type !kdy:person))"""
    conn.addRules(rules1)
    queryString2 = """
    (select (?first ?last)
            (man ?person)
            (q ?person !kdy:first-name ?first)
            (q ?person !kdy:last-name ?last)
            )"""
    tupleQuery2 = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString2)
    return tupleQuery2.evaluate(jdbc=jdbc)    
    

def test17():
    """
    Prolog queries
    """
    with connect().dedicated() as conn:
        result = kennedy_male_names(False, conn);     
        for bindingSet in result:
            f = bindingSet.getValue("first")
            l = bindingSet.getValue("last")
            print "%s %s" % (f, l)


def test18():
    """
    Loading Prolog rules
    """
#    def pq(queryString):
#        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
#        result = tupleQuery.evaluate();     
#        for row in result:
#            print row
    with connect().dedicated() as conn:        
        test6(conn)
        conn.setNamespace("kdy", "http://www.franz.com/simple#")
        conn.setNamespace("rltv", "http://www.franz.com/simple#")  
        conn.setRuleLanguage(QueryLanguage.PROLOG)
        path = os.path.join(CURRENT_DIRECTORY, "relative_rules.txt")
        conn.loadRules(path)
    #    pq("""(select ?x (string-concat ?x "a" "b" "c"))""")
    #    pq("""(select (?person ?uncle) (uncle ?y ?x)(name ?x ?person)(name ?y ?uncle))""")
        queryString = """(select (?person ?uncle) (uncle ?y ?x)(name ?x ?person)(name ?y ?uncle))"""
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();     
        for bindingSet in result:
            p = bindingSet.getValue("person")
            u = bindingSet.getValue("uncle")
            print "%s is the uncle of %s." % (u, p)
        
def test19():
    ## Examples of RDFS++ inference.  Was originally example 2A.
    conn = connect()
    print "Beginning test19()..."
    ## Create URIs for Bob and Robert (and kids) 
    robert = conn.createURI("http://example.org/people/robert")
    roberta = conn.createURI("http://example.org/people/roberta")
    bob = conn.createURI("http://example.org/people/bob")
    bobby = conn.createURI("http://example.org/people/bobby")
    ## create name and child predicates, and Person class.
    name = conn.createURI("http://example.org/ontology/name")
    fatherOf = conn.createURI("http://example.org/ontology/fatherOf")
    person = conn.createURI("http://example.org/ontology/Person")
    ## create literal values for names    
    bobsName = conn.createLiteral("Bob")
    bobbysName = conn.createLiteral("Bobby")
    robertsName = conn.createLiteral("Robert")
    robertasName = conn.createLiteral("Roberta")
    ## Bob is the same person as Robert
    conn.add(bob, OWL.SAMEAS, robert)
    ## Robert, Bob, and children are people
    conn.add(robert, RDF.TYPE, person)
    conn.add(roberta, RDF.TYPE, person)
    conn.add(bob, RDF.TYPE, person)
    conn.add(bobby, RDF.TYPE, person)
    ## They all have names.
    conn.add(robert, name, robertsName)
    conn.add(roberta, name, robertasName)
    conn.add(bob, name, bobsName)
    conn.add(bobby, name, bobbysName)
    ## robert has a child
    conn.add(robert, fatherOf, roberta)
    ## bob has a child
    conn.add(bob, fatherOf, bobby)
    ## List the children of Robert, with inference OFF.
    print "Children of Robert, inference OFF"
    for s in conn.getStatements(robert, fatherOf, None, None): print s    
    ## List the children of Robert with inference ON. The owl:sameAs
    ## link combines the children of Bob with those of Robert.
    print "Children of Robert, inference ON"
    for s in conn.getStatements(robert, fatherOf, None, None, True): print s  
    ## Remove the owl:sameAs link so we can try the next example. 
    conn.remove(bob, OWL.SAMEAS, robert)
    ## Define new predicate, hasFather, as the inverse of fatherOf.
    hasFather = conn.createURI("http://example.org/ontology/hasFather")
    conn.add(hasFather, OWL.INVERSEOF, fatherOf)
    ## Search for people who have fathers, even though there are no hasFather triples.
    ## With inference OFF.
    print "People with fathers, inference OFF"
    for s in conn.getStatements(None, hasFather, None, None): print s    
    ## With inference ON. The owl:inverseOf link allows AllegroGraph to 
    ## deduce the inverse links.
    print "People with fathers, inference ON"
    for s in conn.getStatements(None, hasFather, None, None, True): print s  
    ## Remove owl:inverseOf property.
    conn.remove(hasFather, OWL.INVERSEOF, fatherOf)
      ## Next 12 lines were for owl:inverseFunctionalProperty, but that isn't
      ## supported yet in AG.  Commenting them out. 
      ## Add fatherOf link from Robert to Bobby, giving Bobby two fathers. 
      #conn.add(robert, fatherOf, bobby)
      ## Now make fatherOf a 'reverse functional property'
      #conn.add(fatherOf, RDF.TYPE, OWL.INVERSEFUNCTIONALPROPERTY)
      ## Bob has how many children? 
      ## With inference OFF.
      #print "Who is Bob the father of, inference OFF"
      #for s in conn.getStatements(bob, fatherOf, None, None): print s    
      ## With inference ON. AllegroGraph knows that Bob and Robert must
      ## be the same person.
      #print "Who is Bob the father of, inference ON"
      #for s in conn.getStatements(bob, fatherOf, None, None, True): print s  
    ## Subproperty example.  We'll make fatherOf an rdfs:subpropertyOf parentOf.
    parentOf = conn.createURI("http://example.org/ontology/parentOf")
    conn.add(fatherOf, RDFS.SUBPROPERTYOF, parentOf)
    ## Now search for inferred parentOf links.
    ## Search for parentOf links, even though there are no parentOf triples.
    ## With inference OFF.
    print "People with parents, inference OFF"
    for s in conn.getStatements(None, parentOf, None, None): print s    
    ## With inference ON. The rdfs:subpropertyOf link allows AllegroGraph to 
    ## deduce that fatherOf links imply parentOf links.
    print "People with parents, inference ON"
    for s in conn.getStatements(None, parentOf, None, None, True): print s  
    conn.remove(fatherOf, RDFS.SUBPROPERTYOF, parentOf)
    ## The next example shows rdfs:range and rdfs:domain in action.
    ## We'll create two new rdf:type classes.  Note that classes are capitalized.
    parent = conn.createURI("http://example.org/ontology/Parent")
    child = conn.createURI("http://exmaple.org/ontology/Child")
    ## The following triples say that a fatherOf link points from a parent to a child.
    conn.add(fatherOf, RDFS.DOMAIN, parent)
    conn.add(fatherOf, RDFS.RANGE, child)
    ## Now we can search for rdf:type parent.
    print "Who are the parents?  Inference ON."
    for s in conn.getStatements(None, RDF.TYPE, parent, None, True): print s
    ## And we can search for rdf:type child.
    print "Who are the children?  Inference ON."
    for s in conn.getStatements(None, RDF.TYPE, child, None, True): print s
    
def test20():
    """
    GeoSpatial Reasoning
    """
    conn = connect();
    print "Starting example test20()."
    exns = "http://example.org/people/"
    conn.setNamespace('ex', exns)
    alice = conn.createURI(exns, "alice")
    bob = conn.createURI(exns, "bob")
    carol = conn.createURI(exns, "carol")
    conn.createRectangularSystem(scale=1, xMax=100, yMax=100)
    location = conn.createURI(exns, "location")
    #conn.registerDatatypeMapping(predicate=location, nativeType="int")   
    #conn.registerDatatypeMapping(predicate=location, nativeType="float")       
    conn.add(alice, location, conn.createCoordinate(30,30))
    conn.add(bob, location, conn.createCoordinate(40, 40))
    conn.add(carol, location, conn.createCoordinate(50, 50)) 
    box1 = conn.createBox(20, 40, 20, 40) 
    print box1
    print "Find people located within box1."
    for r in conn.getStatements(None, location, box1) : print r
    circle1 = conn.createCircle(35, 35, radius=10)  
    print circle1
    print "Find people located within circle1."
    for r in conn.getStatements(None, location, circle1) : print r 
    polygon1 = conn.createPolygon([(10,40), (50,10), (35,40), (50,70)])
    print polygon1
    print "Find people located within polygon1."
    for r in conn.getStatements(None, location, polygon1) : print r
    # now we switch to a LatLong (spherical) coordinate system
    #latLongGeoType = conn.createLatLongSystem(scale=5) #, unit='km')
    latLongGeoType = conn.createLatLongSystem(scale=5, unit='degree')
    amsterdam = conn.createURI(exns, "amsterdam")
    london = conn.createURI(exns, "london")
    sanfrancisto = conn.createURI(exns, "sanfrancisco")
    salvador = conn.createURI(exns, "salvador")    
    location = conn.createURI(exns, "geolocation")
#    conn.registerDatatypeMapping(predicate=location, nativeType="float")   
    conn.add(amsterdam, location, conn.createCoordinate(52.366665, 4.883333))
    conn.add(london, location, conn.createCoordinate(51.533333, -0.08333333))
    conn.add(sanfrancisto, location, conn.createCoordinate(37.783333, -122.433334)) 
    conn.add(salvador, location, conn.createCoordinate(13.783333, -88.45))   
    box2 = conn.createBox( 25.0, 50.0, -130.0, -70.0) 
    print box2
    print "Locate entities within box2."
    for r in conn.getStatements(None, location, box2) : print r    
    circle2 = conn.createCircle(19.3994, -99.08, 2000, unit='km')
    print circle2
    print "Locate entities within circle2."
    for r in conn.getStatements(None, location, circle2) : print r
    polygon2 = conn.createPolygon([(51.0, 2.00),(60.0, -5.0),(48.0,-12.5)])
    print polygon2
    print "Locate entities within polygon2."
    for r in conn.getStatements(None, location, polygon2) : print r
    # experiments in units for lat/long type
    print "km"
    latLongGeoType1 = conn.createLatLongSystem(scale=5, unit='km')
    print latLongGeoType1
    print "degree"
    latLongGeoType2 = conn.createLatLongSystem(scale=5, unit='degree')
    print latLongGeoType2
    print "mile"
    latLongGeoType3 = conn.createLatLongSystem(scale=5, unit='miles')
    print latLongGeoType3
    print "radian"
    latLongGeoType4 = conn.createLatLongSystem(scale=5, unit='radian')
    print latLongGeoType4
    print "megaton"
    latLongGeoType5 = conn.createLatLongSystem(scale=5, unit='megaton')
    print latLongGeoType5

def test21():
    """
    Social Network Analysis Reasoning
    """
    with connect().dedicated() as conn:
        print "Starting example test21()."
        print "Current working directory is '%s'" % (os.getcwd())
        path1 = os.path.join(CURRENT_DIRECTORY, "lesmis.rdf")
        print "Load Les Miserables triples."
        conn.addFile(path1, None, format=RDFFormat.RDFXML)
        print "After loading, repository contains %i Les Miserables triples in context '%s'." % (
               conn.size('null'), 'null')
        genName = "LesMiserables"
        lmns = "http://www.franz.com/lesmis#"
        conn.setNamespace('lm', lmns)
        knows = conn.createURI(lmns, "knows")
        # Create some generators
        conn.registerSNAGenerator("LesMiserables1", subjectOf=None, objectOf=None, undirected=knows.toNTriples(), generator_query=None)
        conn.registerSNAGenerator("LesMiserables2", subjectOf=None, objectOf=None, undirected=None, generator_query=None)
        valjean = conn.createURI(lmns, "character11")
        conn.registerNeighborMatrix("LM_Matrix1", "LesMiserables1", valjean.toNTriples(), max_depth=2)
        conn.registerNeighborMatrix("LM_Matrix2", "LesMiserables1", valjean.toNTriples(), max_depth=2)

        # To rebuild, just call registerNeighborMatrix again
        conn.registerNeighborMatrix("LM_Matrix1", "LesMiserables1", valjean.toNTriples(), max_depth=2)


def test22():
    """
    More Social Network Analysis Reasoning
    """

    with connect().dedicated() as conn:
        print "Starting example test21()."
        print "Current working directory is '%s'" % (os.getcwd())
        path1 = os.path.join(CURRENT_DIRECTORY, "lesmis.rdf")
        print "Load Les Miserables triples."
        conn.addFile(path1, None, format=RDFFormat.RDFXML)
        print "After loading, repository contains %i Les Miserables triples in context '%s'." % (
               conn.size('null'), 'null')

        # Create URIs for relationship predicates.
        lmns = "http://www.franz.com/lesmis#"
        conn.setNamespace('lm', lmns)
        knows = conn.createURI(lmns, "knows")
        barely_knows = conn.createURI(lmns, "barely_knows")
        knows_well = conn.createURI(lmns, "knows_well")

        # Create URIs for some characters.
        valjean = conn.createURI(lmns, "character11")
        bossuet = conn.createURI(lmns, "character64")

        conn.setRuleLanguage(QueryLanguage.PROLOG)

        # Create some generators
        #print "\nSNA generators known (should be none): '%s'" % (conn.listSNAGenerators())
        conn.registerSNAGenerator("intimates", subjectOf=None, objectOf=None, 
            undirected=knows_well, generator_query=None)
        conn.registerSNAGenerator("associates", subjectOf=None, objectOf=None, 
            undirected=[knows, knows_well], generator_query=None)
        conn.registerSNAGenerator("everyone", subjectOf=None, objectOf=None, 
            undirected=[knows, knows_well, barely_knows], 
            generator_query=None)
        conn.registerSNAGenerator("emptyGen", subjectOf=None, objectOf=None, undirected=None, 
            generator_query=None)
        print "Created four generators."
        #print "SNA generators known (should be four): '%s'" % (conn.listSNAGenerators())

        # Create neighbor matrix.
        conn.registerNeighborMatrix("matrix1", "intimates", valjean, max_depth=2)
        conn.registerNeighborMatrix("matrix2", "associates", valjean, max_depth=5)
        conn.registerNeighborMatrix("matrix3", "everyone", valjean, max_depth=2)
        conn.registerNeighborMatrix("emptyMat", "emptyGen", valjean, max_depth=2) 
        print "Created four matrices."

        conn.registerNeighborMatrix("matrix1", "intimates", valjean, max_depth=2)
        print "Rebuilt one matrix."

        # Explore Valjean's ego group.
        print "\nValjean's ego group members (using associates)."
        queryString = """
        (select (?member ?name)
          (ego-group-member !lm:character11 1 associates ?member)
          (q ?member !dc:title ?name))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        print "Found %i query results" % len(result)      
        for bindingSet in result:
            p = bindingSet.getValue("member")
            n = bindingSet.getValue("name")
            print "%s %s" % (p, n)

        # Valjean's ego group using neighbor matrix.
        print "\nValjean's ego group (using associates matrix)."
        queryString = """
        (select (?member ?name)
          (ego-group-member !lm:character11 1 matrix2 ?member)
          (q ?member !dc:title ?name))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        print "Found %i query results" % len(result)      
        for bindingSet in result:
            p = bindingSet.getValue("member")
            n = bindingSet.getValue("name")
            print "%s %s" % (p, n)

        print "\nValjean's ego group in one list depth 1 (using associates)."
        queryString = """
        (select ?group
          (ego-group !lm:character11 1 associates ?group))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        print "Found %i query results" % len(result)      
        for bindingSet in result:
            p = bindingSet.getValue("group")
            print "%s" % (p)

        print "\nValjean's ego group in one list depth 2 (using associates)."
        queryString = """
        (select ?group
          (ego-group !lm:character11 2 associates ?group))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        print "Found %i query results" % len(result)      
        for bindingSet in result:
            p = bindingSet.getValue("group")
            print "%s" % (p)

        print "\nValjean's ego group in one list depth 3 (using associates)."
        queryString = """
        (select ?group
          (ego-group !lm:character11 3 associates ?group))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        print "Found %i query results" % len(result)      
        for bindingSet in result:
            p = bindingSet.getValue("group")
            print "%s" % (p)


        print "\nShortest breadth-first path connecting Valjean to Bossuet using intimates."
        queryString = """
        (select ?path
          (breadth-first-search-paths !lm:character11 !lm:character64 intimates 10 ?path))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        print "Found %i query results" % len(result)      
        for bindingSet in result:
            p = bindingSet.getValue("path")
            print "%s" % (p)

        print "\nShortest breadth-first path connecting Valjean to Bossuet using associates."
        queryString = """
        (select ?path
          (breadth-first-search-paths !lm:character11 !lm:character64 associates 10 ?path))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        print "Found %i query results" % len(result)      
        for bindingSet in result:
            p = bindingSet.getValue("path")
            print "%s" % (p)

        print "\nShortest breadth-first path connecting Valjean to Bossuet using everyone."
        queryString = """
        (select ?path
          (breadth-first-search-paths !lm:character11 !lm:character64 everyone 10 ?path))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        print "Found %i query results" % len(result)      
        for bindingSet in result:
            p = bindingSet.getValue("path")
            print "%s" % (p)

        print "\nShortest breadth-first path connecting Valjean to Bossuet? with associates (should be two)."
        queryString = """
        (select ?path
          (breadth-first-search-paths !lm:character11 !lm:character64 associates ?path))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        print "Found %i query results" % len(result)      
        for bindingSet in result:
            p = bindingSet.getValue("path")
            print "%s" % (p)

        print "\nShortest depth-first paths connecting Valjean to Bossuet? with associates (should be two)."
        queryString = """
        (select ?path
          (depth-first-search-paths !lm:character11 !lm:character64 associates ?path))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            p = bindingSet.getValue("path")
            print "%s" % (p)

        print "\nShortest bidirectional paths connecting Valjean to Bossuet with associates (should be two)."
        queryString = """
        (select ?path
          (bidirectional-search-paths !lm:character11 !lm:character64 associates ?path))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            p = bindingSet.getValue("path")
            print "%s" % (p)

        print "\nNodal degree of Valjean (should be seven)."
        queryString = """
        (select ?degree
          (nodal-degree !lm:character11 associates ?degree))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            p = bindingSet.getValue("degree")
            print "%s" % (p)
            print "%s" % p.toPython()

        print "\nHow many neighbors are around Valjean? (should be 36)."
        queryString = """
        (select ?neighbors
          (nodal-degree !lm:character11 everyone ?neighbors))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            p = bindingSet.getValue("neighbors")
            print "%s" % (p)
            print "%s" % p.toPython()

        print "\nWho are Valjean's neighbors? (using everyone)."
        queryString = """
        (select (?name)
          (nodal-neighbors !lm:character11 everyone ?member)
          (q ?member !dc:title ?name))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            n = bindingSet.getValue("name")
            print "%s, " % (n),

        print "\nGraph density of Valjean's ego group? (using associates)."
        queryString = """
        (select ?density
          (ego-group !lm:character11 1 associates ?group)
          (graph-density ?group associates ?density))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            p = bindingSet.getValue("density")
            print "%s" % (p)
            print "%s" % (p.toPython())

        print "\nValjean's cliques? Should be two (using associates)."
        queryString = """
        (select ?clique
          (clique !lm:character11 associates ?clique))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        print "Number of cliques: %s" % len(result)
        for bindingSet in result:
            p = bindingSet.getValue("clique")
            print "%s" % (p)

        # Valjean's actor-degree-centrality using a depth of 1.
        print "\nValjean's actor-degree-centrality to his ego group at depth 1 (using associates)."
        queryString = """
        (select (?centrality)
          (ego-group !lm:character11 1 associates ?group)
          (actor-degree-centrality !lm:character11 ?group associates ?centrality))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            p = bindingSet.getValue("centrality")
            print "%s" % (p)
            print "%s" % (p.toPython())

        # Valjean's actor-degree-centrality using a depth of 2.
        print "\nValjean's actor-degree-centrality to his ego group at depth 2 (using associates)."
        queryString = """
        (select (?centrality)
          (ego-group !lm:character11 2 associates ?group)
          (actor-degree-centrality !lm:character11 ?group associates ?centrality))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            p = bindingSet.getValue("centrality")
            print "%s" % (p)
            print "%s" % (p.toPython())

        # Valjean's actor-closeness-centrality using a depth of 1.
        print "\nValjean's actor-closeness-centrality to his ego group at depth 1 (using associates)."
        queryString = """
        (select (?centrality)
          (ego-group !lm:character11 1 associates ?group)
          (actor-closeness-centrality !lm:character11 ?group associates ?centrality))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            p = bindingSet.getValue("centrality")
            print "%s" % (p)
            print "%s" % (p.toPython())

        # Valjean's actor-closeness-centrality using a depth of 2.
        print "\nValjean's actor-closeness-centrality to his ego group at depth 2 (using associates)."
        queryString = """
        (select (?centrality)
          (ego-group !lm:character11 2 associates ?group)
          (actor-closeness-centrality !lm:character11 ?group associates ?centrality))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            p = bindingSet.getValue("centrality")
            print "%s" % (p)
            print "%s" % (p.toPython())

        # Valjean's actor-betweenness-centrality using a depth of 2.
        print "\nValjean's actor-betweenness-centrality to his ego group at depth 2 (using associates)."
        queryString = """
        (select (?centrality)
          (ego-group !lm:character11 2 associates ?group)
          (actor-betweenness-centrality !lm:character11 ?group associates ?centrality))
          """
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.PROLOG, queryString)
        result = tupleQuery.evaluate();
        for bindingSet in result:
            p = bindingSet.getValue("centrality")
            print "%s" % (p)
            print "%s" % (p.toPython())

        
def test_jdbc_iter():
    """
    JDBC test with resultset as iterator.
    """
    with connect().dedicated() as conn:
        results = kennedy_male_names(True, conn)     
        for row in results:
            f = row.getValue("first")
            l = row.getValue("last")
            print "%s %s" % (f, l)

def test_jdbc_java():
    """
    JDBC test with resultset as java next.
    """
    with connect().dedicated() as conn:
        rows = kennedy_male_names(True, conn)     
        while rows.next():
            f = rows.getValue("first")
            l = rows.getValue("last")
            print "%s %s" % (f, l)
    
def test_getStatements():
    conn = test6()
    rows = conn.getStatements(None, None, None, tripleIDs=False)

    for row in rows:
        print '%s %s %s %s' % (row[0], row[1],
            row[2], row[3])

    rows = conn.getStatements(None, None, None, tripleIDs=True)

    for row in rows:
        print '%s %s %s %s %s' % (row[0], row[1],
            row[2], row[3], row.getTripleID())


def test_getJDBCStatements():
    conn = test6()
    rows = conn.getJDBCStatements(None, None, None, tripleIDs=False)

    for row in rows:
        print '%s %s %s %s' % (row.getValue(0), row.getValue(1),
            row.getValue(2), row.getValue(3))

    rows = conn.getJDBCStatements(None, None, None, tripleIDs=True)

    for row in rows:
        print '%s %s %s %s %s' % (row.getValue(0), row.getValue(1),
            row.getValue(2), row.getValue(3), row.getValue(4))

    rows = conn.getJDBCStatements(None, None, None, limit=10, tripleIDs=True)

    assert len(rows) <= 10

def test_dedicated():
    """
    Test of Dedicated Back End Commit/Rollback
    """
    server = AllegroGraphServer(AG_HOST, AG_PORT, 'test', 'xyzzy')
    catalog = server.openCatalog(CATALOG)  
    myRepository = catalog.getRepository(STORE, Repository.RENEW)
    myRepository.initialize()
    common = myRepository.getConnection()

    with myRepository.getConnection().dedicated() as dedicated:
        path1 = os.path.join(CURRENT_DIRECTORY, 'vc-db-1.rdf')
        path2 = os.path.join(CURRENT_DIRECTORY, 'kennedy.ntriples')
        path3 = os.path.join(CURRENT_DIRECTORY, 'lesmis.rdf')
        baseURI = "http://example.org/example/local"
        context = dedicated.createURI("http://example.org#vcards")
        dedicated.setNamespace("vcd", "http://www.w3.org/2001/vcard-rdf/3.0#");
        ## read vcards triples into the context 'context' of back end:
        # Load 16 vcards triples into named context in dedicated back end.
        dedicated.addFile(path1, baseURI, format=RDFFormat.RDFXML, context=context);
        ## read kennedy triples into the dedicated null context:
        # Load 1214 kennedy.ntriples into null context of dedicated back end.
        dedicated.add(path2, base=baseURI, format=RDFFormat.NTRIPLES, contexts=None)
        ## read lesmis triples into the null context of the common back end:
        # Load 916 lesmis triples into null context of common back end.
        common.addFile(path3, baseURI, format=RDFFormat.RDFXML, context=None);
        assert 16 == dedicated.size(context)
        assert 1214 == dedicated.size('null')
        assert 916 == common.size('null')
    