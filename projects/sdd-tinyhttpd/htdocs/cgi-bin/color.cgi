#!/bin/sh
echo "Content-Type: text/html"
echo ""
echo "<html><body>"
echo "<h1>Color: $QUERY_STRING</h1>"
echo "<p>CGI works! Method: $REQUEST_METHOD</p>"
echo "</body></html>"
