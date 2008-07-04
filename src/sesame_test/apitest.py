
from franz.openrdf.sail.sail import SailRepository
from franz.openrdf.sail.allegrographstore import AllegroGraphStore
from franz.openrdf.query.query import QueryLanguage
from franz.openrdf.vocabulary.rdf import RDF
from franz.openrdf.vocabulary.xmlschema import XMLSchema
from franz.openrdf.query.dataset import Dataset
from franz.openrdf.rio.rdfformat import RDFFormat
from franz.openrdf.rio.rdfwriter import RDFXMLWriter, NTriplesWriter


import os, urllib, datetime

CURRENT_DIRECTORY = os.getcwd() 

def test0():
    """
    Test to see if you have the module settings correctly set.
    """
    print "Welcome to the PythonAPI"
    file1 = open("./vc-db-1.rdf")
    print file1.name, os.path.abspath(file1.name)
    file2 = open(CURRENT_DIRECTORY + "/vc-db-1.rdf")
    print file2.name 
    
    try:
        fname, headers = urllib.urlretrieve("http://www.co-ode.org/ontologies/amino-acid/2005/10/11/amino-acid.owl", "/tmp/myfile")
        file3 = open(fname) 
    except Exception, e:
        print "Failed ", e
    for line in file3:
        print line
    print "MADE IT"
    

def test1():
    """
    Tests getting the repository up.  Is called by most of the other tests to do the startup.
    """
    sesameDir = "/Users/bmacgregor/Desktop/SesameFolder"
    store = AllegroGraphStore(AllegroGraphStore.RENEW, "192.168.1.102", "testP",
                              sesameDir, port=4567)
    myRepository = SailRepository(store)
    myRepository.initialize()
    ## TEMPORARY:
    #store.internal_ag_store.serverTrace(True)
    ## END TEMPORARY
    print "Repository is up!"
    return myRepository
    
def test2():
    myRepository = test1()
    f = myRepository.getValueFactory()
    ## create some resources and literals to make statements out of
    alice = f.createURI("http://example.org/people/alice")
    bob = f.createURI("http://example.org/people/bob")
    name = f.createURI("http://example.org/ontology/name")
    person = f.createURI("http://example.org/ontology/Person")
    bobsName = f.createLiteral("Bob")
    alicesName = f.createLiteral("Alice")

    conn = myRepository.getConnection()
    ## alice is a person
    conn.add(alice, RDF.TYPE, person)
    ## alice's name is "Alice"
    conn.add(alice, name, alicesName)
    ## bob is a person
    conn.add(bob, RDF.TYPE, person)
    ## bob's name is "Bob":
    conn.add(bob, name, bobsName)
    return myRepository

def test3():    
    conn = test2().getConnection()
    try:
        queryString = "SELECT ?s ?p ?o WHERE {?s ?p ?o .}"
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
        result = tupleQuery.evaluate();
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
    myRepository = test2()
    conn = myRepository.getConnection()
    alice = myRepository.getValueFactory().createURI("http://example.org/people/alice")
    statements = conn.getStatements(alice, None, None, True, [])
    for s in statements:
        print s
    print "Same thing using JDBC:"
    resultSet = conn.getJDBCStatements(alice, None, None, True, [])
    while resultSet.next():
        #print resultSet.getRow()
        print "   ", resultSet.getValue(3), "   ", resultSet.getString(3)  
               
import dircache, os

def test5():
    print "ABSPATH ", os.path.abspath(".")
    for f in dircache.listdir("."):
        print f
        
    myRepository = test1()       
    print "CURDIR ", os.getcwd() 
    file = open("/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/sesame_test/vc-db-1.rdf")        
    file = open("./vc-db-1.rdf")            
    #file = open("./agraph-python/src/sesame_test/vc-db-1.rdf")                
    baseURI = "http://example.org/example/local"
    baseURI = None
    try:
        conn = myRepository.getConnection();
        conn.add("./vc-db-1.rdf", base=baseURI, format=RDFFormat.RDFXML); 
        print "After loading, repository contains %s triples." % conn.size(None)
        try:
            for s in conn.getStatements(None, None, None, True, []):
                print s
             
#            print "\n\nAnd here it is JDBC-style"
#            resultSet = conn.getJDBCStatements(None, None, None, False, [])
#            while resultSet.next():
#                print resultSet.getRow()
                
            print "\n\nAnd here it is without the objects"
            resultSet = conn.getJDBCStatements(None, None, None, True, [])
            while resultSet.next():
                print resultSet.getString(1), resultSet.getString(2), resultSet.getString(3)

        finally:
            pass
    finally:
        conn.close()

def test6():
    myRepository = test1() 
    file = open("/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/sesame_test/vc-db-1.rdf")        
    baseURI = "http://example.org/example/local"
    try:
        conn = myRepository.getConnection();
        conn.add(file, base=baseURI, format=RDFFormat.RDFXML);
        print "After loading, repository contains %s triples." % conn.size(None)         
        queryString = "SELECT ?s ?p ?o WHERE {?s ?p ?o .}"
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
        result = tupleQuery.evaluate();
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
        
def test7():
    myRepository = test1() 
    file = open("/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/sesame_test/vc-db-1.rdf")        
    baseURI = "http://example.org/example/local"
    try:
        conn = myRepository.getConnection();
        conn.add(file, base=baseURI, format=RDFFormat.RDFXML);
        print "After loading, repository contains %s triples." % conn.size(None)         
        queryString = "CONSTRUCT { ?s ?p ?o } WHERE {?s ?p ?o .}"
        graphQuery = conn.prepareGraphQuery(QueryLanguage.SPARQL, queryString)
        result = graphQuery.evaluate();
        for s in result:          
            print s
    finally:
        conn.close();

import urlparse

def test8():
    """
    Asserting into a context and matching against it.
    """
    location = "/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/test/vc_db_1_rdf"      
    url = "/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/sesame_test/vc-db-1.rdf"      
    url = "/Users/bmacgregor/Documents/eclipse-franz-python/agraph-python/src/sesame_test/sample-bad.rdf"
    baseURI = location
    myRepository = test1() 
    context = myRepository.getValueFactory().createURI(location)
    ## TEMPORARY:  
    print "NULLIFYING CONTEXT TEMPORARILY"
    context = None
    ## END TEMPORARY  
    conn = myRepository.getConnection();
    ## read the contents of a file into the context:
    conn.add(url, baseURI, format=RDFFormat.RDFXML, contexts=context);
    print "RDF store contains %s triples" % conn.size()
    ## Get all statements in the context
    statements = conn.getStatements(None, None, None, False, context)    
    try:
        for s in statements:
            print s
    finally:
        statements.close()
    ## Export all statements in the context to System.out, in NTriples format
    outputFile = "/users/bmacgregor/Desktop/temp.nt"
    outputFile = None
    if outputFile == None:
        print "Writing to Standard Out instead of to a file"
    ntriplesWriter = NTriplesWriter(outputFile)
    conn.export(ntriplesWriter, context);    
    ## Remove all statements in the context from the repository
    conn.clear(context)
    ## Verify that the statements have been removed:
    statements = conn.getStatements(None, None, None, False, context)    
    try:
        for s in statements:
            print s
    finally:
        statements.close()
   
def test9():
    test2()
    sesameDir = "/Users/bmacgregor/Desktop/SesameFolder"
    store = AllegroGraphStore(AllegroGraphStore.OPEN, "localhost", "testP",
                              sesameDir, port=4567)
    myRepository = SailRepository(store)
    myRepository.initialize()
    ## TEMPORARY:
    #store.internal_ag_store.serverTrace(True)
    ## END TEMPORARY
    print "Repository is up!"
    conn = myRepository.getConnection()
    statements = conn.getStatements(None, None, None, False, None)    
    try:
        for s in statements:
            print s
    finally:
        statements.close()
    return myRepository

def test10():
    myRepository = test1()
    conn = myRepository.getConnection()
    aminoFile = "amino.owl"
    #aminoFile = "/Users/bmacgregor/Desktop/rdf/ciafactbook.nt"
    print "Begin loading triples from ", aminoFile, " into AG ..."
    conn.add(aminoFile)
    print "Loaded ", conn.size(None), " triples."
#    f = myRepository.getValueFactory()
#    rdfsLabel = f.createURI("http://www.w3.org/2000/01/rdf-schema#label")
#    glutamine = f.createLiteral("Glutamine")
    ##
    count = 0         
    ##statements = conn.getStatements(None, None, glutamine, True, None)
    print "Begin retrieval ", datetime.datetime.now()
    beginTime = datetime.datetime.now()    
    statements = conn.getStatements(None, None, None, False, None)
    elapsed = datetime.datetime.now() - beginTime
    print "Retrieval took %s milliseconds" % elapsed
    print "Begin counting statements ... ", datetime.datetime.now()
    for s in statements:
        #print s
        count += 1
        if (count % 50) == 0:  print '.',
        if (count % 1000) == 0: print
    elapsed = datetime.datetime.now() - beginTime
    print "Counted %i statements in time %s" % (count, elapsed)
    print "End retrieval ", datetime.datetime.now(), " elapsed ", elapsed
    
    print "Begin JDBC retrieval ", datetime.datetime.now()
    beginTime = datetime.datetime.now()    
    resultSet = conn.getJDBCStatements(None, None, None, False, [])
    count = 0
    while resultSet.next():
        #print s
        count += 1
        if (count % 50) == 0:  print '.',
        if (count % 1000) == 0: print
    elapsed = datetime.datetime.now() - beginTime
    print "Counted %i JDBC statements in time %s " % (count, elapsed)
    print "End retrieval ", datetime.datetime.now(), " elapsed ", elapsed

def test11():
    ## Test query performance
    myRepository = test1()
    conn = myRepository.getConnection()
    aminoFile = "amino.owl"
    #aminoFile = "/Users/bmacgregor/Desktop/rdf/ciafactbook.nt"
    print "Begin loading triples from ", aminoFile, " into AG ..."
    conn.add(aminoFile)
    print "Loaded ", conn.size(None), " triples."
    count = 0         
    print "Begin retrieval ", datetime.datetime.now()
    beginTime = datetime.datetime.now()    
    queryString = "SELECT ?s ?p ?o WHERE {?s ?p ?o .}"
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    #tupleQuery.setIncludeInferred(True)    ## Works, but is very slow, infers additional 44 statements
    result = tupleQuery.evaluate();
    elapsed = datetime.datetime.now() - beginTime
    print "\nQuery evaluated, begin generating bindings; elapsed time ", elapsed
    for bindingSet in result:
#        s = bindingSet.getValue("s")
#        p = bindingSet.getValue("p")
#        o = bindingSet.getValue("o")              
#        print "%s %s %s" % (s, p, o)
        count += 1
    elapsed = datetime.datetime.now() - beginTime
    print "Counted %i statements; elapsed time %s" % (count, elapsed)
    print "End retrieval ", datetime.datetime.now(), " elapsed ", elapsed


def test12():
    """
    Reading from a URL
    """
    myRepository = test1()
    conn = myRepository.getConnection()
    tempAminoFile = "/tmp/myfile.rdf"
    try:
        websource = "http://www.co-ode.org/ontologies/amino-acid/2005/10/11/amino-acid.owl"
        websource = "http://www.ontoknowledge.org/oil/case-studies/CIA-facts.rdf"        
        print "Begin downloading ", websource, " triples ..."
        fname, headers = urllib.urlretrieve(websource, tempAminoFile)
        print "Triples in temp file"
        tempAminoFile = open(fname) 
    except Exception, e:
        print "Failed ", e
    print "Begin loading triples into AG ..."
    conn.add(tempAminoFile)
    print "Loaded ", conn.size(None), " triples."
    if True:
        outputFile = "/users/bmacgregor/Desktop/ciafactbook.nt"
        print "Saving to ", outputFile 
        ntriplesWriter = NTriplesWriter(outputFile)
        conn.export(ntriplesWriter, None);   
    count = 0
    print "Retrieving statements ..."
    statements = conn.getStatements(None, None, None, False, None)
    print "Counting statements ..."
    for s in statements:
        count += 1
        if (count % 50) == 0:  print '.',
    print "Counted %i statements" % count
    
   
def test13():
    """
    Typed Literals
    """
    myRepository = test1()
    conn = myRepository.getConnection()
    f = myRepository.getValueFactory()
    exns = "http://example.org/people/"
    alice = f.createURI("http://example.org/people/alice")
    age = f.createURI(namespace=exns, localname="age")
    weight = f.createURI(namespace=exns, localname="weight")    
    favoriteColor = f.createURI(namespace=exns, localname="favoriteColor")
    birthdate = f.createURI(namespace=exns, localname="birthdate")
    ted = f.createURI(namespace=exns, localname="Ted")
    red = f.createLiteral('Red')
    rouge = f.createLiteral('Rouge', language="fr")
    fortyTwo = f.createLiteral('42', datatype=XMLSchema.INT)
    fortyTwoInteger = f.createLiteral('42', datatype=XMLSchema.LONG)    
    fortyTwoUntyped = f.createLiteral('42')
    date = f.createLiteral('1984-12-06', datatype=XMLSchema.DATE)     
    time = f.createLiteral('1984-12-06', datatype=XMLSchema.DATETIME)         
    stmt1 = f.createStatement(alice, age, fortyTwo)
    stmt2 = f.createStatement(ted, age, fortyTwoUntyped)    
    conn.add(stmt1)
    conn.add(stmt2)
    conn.add(alice, weight, f.createLiteral('20.5'))
    conn.add(ted, weight, f.createLiteral('20.5', datatype=XMLSchema.FLOAT))
    conn.add(alice, favoriteColor, red)
    conn.add(ted, favoriteColor, rouge)
    conn.add(alice, birthdate, date)
    conn.add(ted, birthdate, time)    
    for obj in [None, fortyTwo, fortyTwoUntyped, f.createLiteral('20.5', datatype=XMLSchema.FLOAT), f.createLiteral('20.5'),
                red, rouge]:
        print "Retrieve triples matching '%s'." % obj
        statements = conn.getStatements(None, None, obj, False, None)
        for s in statements:
            print s
    for obj in ['42', '"42"', '20.5', '"20.5"', '"20.5"^^xsd:float', '"Rouge"@fr', '"1984-12-06"^^xsd:date']:
        print "Query triples matching '%s'." % obj
        queryString = """PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> 
        SELECT ?s ?p ?o WHERE {?s ?p ?o . filter (?o = %s)}
        """ % obj
        tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
        result = tupleQuery.evaluate();    
        for bindingSet in result:
            s = bindingSet.getValue("s")
            p = bindingSet.getValue("p")
            o = bindingSet.getValue("o")              
            print "%s %s %s" % (s, p, o)

def test14():
    """
    Datasets and multiple contexts
    """
    myRepository = test1();
    conn = myRepository.getConnection()
    f = myRepository.getValueFactory()
    exns = "http://example.org/people/"
    alice = f.createURI(namespace=exns, localname="alice")
    bob = f.createURI(namespace=exns, localname="bob")
    person = f.createURI(namespace=exns, localname="Person")
    name = f.createURI(namespace=exns, localname="name")    
    alicesName = f.createLiteral("Alice")    
    bobsName = f.createLiteral("Bob")
    context1 = f.createURI(namespace=exns, localname="cxt1")      
    context2 = f.createURI(namespace=exns, localname="cxt2")          
    conn.add(alice, RDF.TYPE, person, context1)
    conn.add(alice, name, alicesName, context1)
    conn.add(bob, RDF.TYPE, person, context2)
    conn.add(bob, name, bobsName, context2)
    ##
    statements = conn.getStatements(None, None, None, False, [context1, context2])
    print "getStatements:"
    for s in statements:
        print s
    resultSet = conn.getJDBCStatements(None, None, None, False, [context1, context2])
    print "getJDBCStatements:"
    while resultSet.next():
        print resultSet.getString(1), resultSet.getString(2), resultSet.getString(3), resultSet.getString(4)
    ## first, retrieve all four quads
    queryString = """
    SELECT ?s ?p ?o ?c
    `+ WHERE { { GRAPH ?c {?s ?p ?o . } } UNION  {?s ?p ?o } }
    """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate();    
    for bindingSet in result:
        s = bindingSet['s']
        p = bindingSet['p']
        o = bindingSet['o']
        c = bindingSet['c']            
        print "%s %s %s %s" % (s, p, o, c)
    ## first, retrieve all four quads        
    ds = Dataset()
    ds.addDefaultGraph(context1)
    ds.addNamedGraph(context2)
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    tupleQuery.setDataset(ds)
    result = tupleQuery.evaluate();    
    print "Query with dataset:"
    for bindingSet in result:
        s = bindingSet['s']
        p = bindingSet['p']
        o = bindingSet['o']
        c = bindingSet['c']            
        print "%s %s %s %s" % (s, p, o, c)
    
def test15():
    """
    Namespaces
    """
    myRepository = test1();
    conn = myRepository.getConnection()
    f = myRepository.getValueFactory()
    exns = "http://example.org/people/"
    alice = f.createURI(namespace=exns, localname="alice")
    person = f.createURI(namespace=exns, localname="Person")
    conn.add(alice, RDF.TYPE, person)
    myRepository.indexTriples()
    conn.setNamespace('ex', exns)
    queryString = """
    SELECT ?s ?p ?o 
    WHERE { ?s ?p ?o . FILTER ((?p = rdf:type) && (?o = ex:Person) ) }
    """
    tupleQuery = conn.prepareTupleQuery(QueryLanguage.SPARQL, queryString)
    result = tupleQuery.evaluate();  
    print  
    for bindingSet in result:
        s = bindingSet.getValue("s")
        s = bindingSet.get("s")
        p = bindingSet['z']
        o = bindingSet[2]
        print "%s %s %s " % (s, p, o)




if __name__ == '__main__':
    choices = [i for i in range(9)]
    choices = [15]
    for choice in choices:
        print "\n==========================================================================="
        print "Test Run Number ", choice, "\n"
        if choice == 0: test0()
        elif choice == 1: test1()
        elif choice == 2: test2()
        elif choice == 3: test3()
        elif choice == 4: test4()    
        elif choice == 5: test5()        
        elif choice == 6: test6()            
        elif choice == 7: test7()                
        elif choice == 8: test8()                
        elif choice == 9: test9()                        
        elif choice == 10: test10()                            
        elif choice == 11: test11()
        elif choice == 12: test12()        
        elif choice == 13: test13() 
        elif choice == 14: test14()        
        elif choice == 15: test15()        
        elif choice == 16: test16()        
        elif choice == 17: test17()                               
        else:
            print "No such test exists."
    