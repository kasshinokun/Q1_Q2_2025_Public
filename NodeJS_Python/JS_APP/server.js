// Created on 2025-01-23
// release 1_23_01_2025

var http = require('http');
const PORT_HOST=8080;
http.createServer(function (req, res) {
  res.writeHead(200, {'Content-Type': 'text/html'});
  //Return the url part of the request object:
  res.write(req.url);
  res.end();
}).listen(PORT_HOST);
