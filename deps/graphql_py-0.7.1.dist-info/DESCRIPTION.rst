Copyright (c) 2015 ivelum

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Description-Content-Type: UNKNOWN
Description: graphql-py
        ==========
        
        .. image:: https://travis-ci.org/ivelum/graphql-py.svg?branch=master
                :target: https://travis-ci.org/ivelum/graphql-py
        
        GraphQL lexer and parser written in pure Python, produces AST. Features:
        
        * Complies with latest `working draft of GraphQL specification`_;
        * Fast enough, built on `PLY`_;
        * Tested vs. Python 2.7, 3.4, 3.5, 3.6 and PyPy
        
        .. _working draft of GraphQL specification: https://facebook.github.io/graphql/
        .. _PLY: http://www.dabeaz.com/ply/
        
        Installation
        ------------
        
        .. code:: shell
        
            $ pip install graphql-py
        
        Usage
        -----
        
        .. code:: shell
        
            from graphql.parser import GraphQLParser
        
            parser = GraphQLParser()
            ast = parser.parse("""
            {
              user(id: 4) {
                id
                name
                profilePic
                avatar: profilePic(width: 30, height: 30)
              }
            }
            """)
            print(ast)
        
        License
        -------
        
        MIT
        
Platform: UNKNOWN
Classifier: Development Status :: 3 - Alpha
Classifier: Intended Audience :: Developers
Classifier: Natural Language :: English
Classifier: License :: OSI Approved :: MIT License
Classifier: Programming Language :: Python
Classifier: Programming Language :: Python :: 2.7
Classifier: Programming Language :: Python :: 3.4
Classifier: Programming Language :: Python :: 3.5
Classifier: Programming Language :: Python :: 3.6
