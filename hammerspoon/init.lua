require("hs.ipc")

-- Hammerspoon entrypoint shared by both Macs.
-- The host role is selected by ~/.hammerspoon-host.

local configDir = hs.configdir
package.path = table.concat({
    configDir .. "/common/?.lua",
    configDir .. "/modules/?.lua",
    configDir .. "/?.lua",
    package.path
}, ";")

local function readHostName()
    local overridePath = os.getenv("HOME") .. "/.hammerspoon-host"
    local file = io.open(overridePath, "r")
    if file then
        local value = file:read("*l")
        file:close()
        if value and value ~= "" then
            return value:gsub("%s+$", "")
        end
    end

    local localizedName = hs.host.localizedName() or ""
    if localizedName:lower():match("mini") then
        return "m4mini"
    end
    return "mbp"
end

local hosts = require("hosts")
local hostName = readHostName()
local host = hosts[hostName]
if not host then
    error("unknown Hammerspoon host: " .. tostring(hostName))
end

local wiredroute = require("wiredroute")
wiredroute.start()

local handoff = require("handoff")
handoff.start(host.handoff)

if host.presence then
    local presence = require("presence")
    presence.start(host.presence)
end

print("Hammerspoon loaded host profile: " .. hostName)
