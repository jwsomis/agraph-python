# TODO creating stores, streaming cursors for queries

import time, cjson
from request import *

class AllegroGraphServer:
    def __init__(self, url):
        self.url = url
        self.curl = pycurl.Curl()

    def listTripleStores(self):
        """Returns the names of open stores on the server."""
        return jsonRequest(self.curl, "GET", self.url + "/repositories")

    def openTripleStore(self, name, fileName, readOnly=False):
        """Ask the server to open a given triple store."""
        pass # TODO

    def createTripleStore(self, name, fileName):
        """Ask the server to create a new triple store."""
        pass # TODO

    def closeTripleStore(self, name):
        """Close a server-side triple store."""
        pass # TODO

    def getRepository(self, name):
        """Create an access object for a triple store."""
        return Repository(self.curl, self.url + "/repositories/" + name)


class Repository:
    def __init__(self, curl, url):
        # TODO verify existence of repository?
        self.url = url
        self.curl = curl

    def getSize(self):
        """Returns the amount of triples in the repository."""
        return jsonRequest(self.curl, "GET", self.url + "/size")

    def listContexts(self):
        """Lists the contexts (named graphs) that are present in this repository."""
        return jsonRequest(self.curl, "GET", self.url + "/contexts")

    def isWriteable(self):
        return jsonRequest(self.curl, "GET", self.url + "/writeable")

    def evalSparqlQuery(self, query, infer=False, context=None):
        """Execute a SPARQL query. Context can be None or a list of
        contexts -- strings in "http://foo.com" form or "null" for
        the default context. Return type depends on the query type.
        ASK gives a boolean, SELECT a {names, values} object
        containing arrays of arrays of terms. CONSTRUCT and DESCRIBE
        return an array of arrays representing statements."""
        return jsonRequest(self.curl, "POST", self.url, urlenc(query=query, infer=infer, context=context))

    def evalPrologQuery(self, query, infer=False):
        """Execute a Prolog query. Returns a {names, values} object."""
        return jsonRequest(self.curl, "POST", self.url, urlenc(query=query, infer=infer, queryLn="prolog"))

    def getStatements(self, subj=None, pred=None, obj=None, context=None, infer=False):
        """Retrieve all statements matching the given contstaints.
        Context can be None or a list of contexts, as in
        evalSparqlQuery."""
        return jsonRequest(self.curl, "GET", self.url + "/statements",
                           urlenc(subj=subj, pred=pred, obj=obj, context=context, infer=infer))

    def addStatement(self, subj, pred, obj, context=None):
        """Add a single statement to the repository."""
        nullRequest(self.curl, "POST", self.url + "/statements",
                    urlenc(subj=subj, pred=pred, obj=obj, context=context))

    def delStatements(self, subj=None, pred=None, obj=None, context=None):
        """Delete all statements matching the constaints from the
        repository. Context can be None or a single graph name."""
        nullRequest(self.curl, "DELETE", self.url + "/statements",
                    urlenc(subj=subj, pred=pred, obj=obj, context=context))

    def addStatements(self, quads):
        """Add a collection of statements to the repository. Quads
        should be an array of four-element arrays, where the fourth
        element, the graph name, may be None."""
        nullRequest(self.curl, "POST", self.url + "/statements/json", cjson.encode(quads));

    def delStatements(self, quads):
        """Delete a collection of statments from the repository."""
        nullRequest(self.curl, "POST", self.url + "/statements/json/delete", cjson.encode(quads));

    def listIndices(self):
        """List the SPOGI-indices that are active in the repository."""
        return jsonRequest(self.curl, "GET", self.url + "/indices")

    def addIndex(self, type):
        """Register a SPOGI index."""
        nullRequest(self.curl, "POST", self.url + "/indices", urlenc(type=type))

    def delIndex(self, type):
        """Drop a SPOGI index."""
        nullRequest(self.curl, "DELETE", self.url + "/indices", urlenc(type=type))

    def getIndexCoverage(self):
        """Returns the proportion (0-1) of the repository that is indexed."""
        return jsonRequest(self.curl, "GET", self.url + "/index");

    def indexStatements(self, all=False):
        """Index any unindexed statements in the repository. If all is
        True, the whole repository is re-indexed."""
        nullRequest(self.curl, "POST", self.url + "/index", urlenc(all=all))

    def evalFreeTextSearch(self, pattern, infer=False):
        """Use free-text indices to search for the given pattern.
        Returns an array of statements."""
        return jsonRequest(self.curl, "GET", self.url + "/freetext", urlenc(pattern=pattern, infer=infer))

    def listFreeTextPrecicates(self):
        """List the precicates that are used for free-text indexing."""
        return jsonRequest(self.curl, "GET", self.url + "/freetextindices")

    def registerFreeTextPredicate(self, predicate):
        """Add a predicate for free-text indexing."""
        nullRequest(self.curl, "POST", self.url + "/freetextindices", urlenc(predicate=predicate))

# Testing stuff

def timeQuery(rep, n, size):
    t = time.time()
    for i in range(n):
        rep.evalSparqlQuery("select ?x ?y ?z {?x ?y ?z} limit %d" % size)
    print "Did %d %d-row queries in %f seconds." % (n, size, time.time() - t)
    
def test():
    server = AllegroGraphServer("http://localhost:8080")
    storeNames = server.listTripleStores()
    if len(storeNames) > 0:
        print "Found repositories " + repr(storeNames) + ", opening " + storeNames[0]
        rep = server.getRepository(storeNames[0])
        print "Repository size = %d" % rep.getSize()
        print "Repository writable = %d" % rep.isWriteable()
        timeQuery(rep, 500, 2)
        timeQuery(rep, 50, 500)
    else:
        print "No repositories found."

if __name__ == '__main__':
    test()
