package.path = package.path .. ";./modules/?.lua"

local wiredroute = require("wiredroute")
wiredroute.start()
